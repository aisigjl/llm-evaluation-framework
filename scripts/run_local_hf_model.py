from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import torch
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

from run_model import CANDIDATE_SYSTEM_PROMPT, build_user_prompt
from utils import append_jsonl, existing_ids, load_config, project_path, read_jsonl, utc_now


def load_local_model(args: argparse.Namespace):
    dtype_map = {
        "auto": "auto",
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }
    torch_dtype = dtype_map[args.torch_dtype]
    tokenizer = AutoTokenizer.from_pretrained(
        args.model_path,
        trust_remote_code=args.trust_remote_code,
        use_fast=not args.no_fast_tokenizer,
    )
    tokenizer.padding_side = "left"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    model_kwargs = {
        "device_map": args.device_map,
        "trust_remote_code": args.trust_remote_code,
        "low_cpu_mem_usage": True,
    }
    if torch_dtype != "auto":
        model_kwargs["dtype"] = torch_dtype
    else:
        model_kwargs["dtype"] = "auto"

    try:
        model = AutoModelForCausalLM.from_pretrained(args.model_path, **model_kwargs)
    except TypeError:
        model_kwargs["torch_dtype"] = model_kwargs.pop("dtype")
        model = AutoModelForCausalLM.from_pretrained(args.model_path, **model_kwargs)

    model.eval()
    return tokenizer, model


def render_prompt(tokenizer: Any, messages: list[dict[str, str]], args: argparse.Namespace) -> str:
    kwargs = {
        "tokenize": False,
        "add_generation_prompt": True,
        "enable_thinking": bool(args.enable_thinking),
    }
    try:
        return tokenizer.apply_chat_template(messages, **kwargs)
    except TypeError:
        kwargs.pop("enable_thinking", None)
        return tokenizer.apply_chat_template(messages, **kwargs)
    except Exception:
        return "\n".join(f"{m['role']}: {m['content']}" for m in messages) + "\nassistant:"


def build_prompts(tokenizer: Any, samples: list[dict[str, Any]], args: argparse.Namespace) -> list[str]:
    prompts: list[str] = []
    for sample in samples:
        messages = [
            {"role": "system", "content": args.system_prompt},
            {"role": "user", "content": build_user_prompt(sample)},
        ]
        prompts.append(render_prompt(tokenizer, messages, args))
    return prompts


def generation_kwargs(tokenizer: Any, args: argparse.Namespace) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "max_new_tokens": args.max_new_tokens,
        "pad_token_id": tokenizer.pad_token_id,
        "eos_token_id": tokenizer.eos_token_id,
    }
    if args.temperature > 0:
        kwargs.update({
            "do_sample": True,
            "temperature": args.temperature,
            "top_p": args.top_p,
        })
    else:
        kwargs["do_sample"] = False
    return kwargs


def generate_batch(tokenizer: Any, model: Any, samples: list[dict[str, Any]], args: argparse.Namespace) -> list[str]:
    prompts = build_prompts(tokenizer, samples, args)
    tokenize_kwargs: dict[str, Any] = {
        "return_tensors": "pt",
        "padding": True,
    }
    if args.max_input_tokens and args.max_input_tokens > 0:
        tokenize_kwargs.update({"truncation": True, "max_length": args.max_input_tokens})

    inputs = tokenizer(prompts, **tokenize_kwargs)
    inputs = {key: value.to(model.device) for key, value in inputs.items()}
    prompt_width = inputs["input_ids"].shape[-1]

    with torch.inference_mode():
        output_ids = model.generate(**inputs, **generation_kwargs(tokenizer, args))

    responses: list[str] = []
    for index in range(len(samples)):
        new_tokens = output_ids[index, prompt_width:]
        responses.append(tokenizer.decode(new_tokens, skip_special_tokens=True).strip())
    return responses


def append_result(output: Path, sample: dict[str, Any], args: argparse.Namespace, model_name: str, response: str, error: str | None) -> None:
    append_jsonl(
        output,
        {
            **sample,
            "model_name": model_name,
            "model_path": str(args.model_path),
            "model_response": response,
            "generation_error": error,
            "generated_at": utc_now(),
        },
    )


def batched(items: list[dict[str, Any]], size: int):
    for start in range(0, len(items), size):
        yield items[start : start + size]


def run(args: argparse.Namespace) -> Path:
    cfg = load_config(args.config)
    golden_path = args.golden_set or cfg["golden_set_path"]
    responses_path = args.responses_path or cfg["default_outputs"]["responses_path"]
    model_name = args.model_name or Path(args.model_path).name

    samples = read_jsonl(golden_path)
    if args.limit and args.limit > 0:
        samples = samples[: args.limit]

    output = project_path(responses_path)
    if args.overwrite and output.exists():
        output.unlink()
    done = set() if args.overwrite else existing_ids(output)
    pending = [sample for sample in samples if sample["id"] not in done]

    tokenizer, model = load_local_model(args)
    progress = tqdm(total=len(pending), desc=f"generate:{model_name}")
    for batch in batched(pending, max(1, args.batch_size)):
        try:
            responses = generate_batch(tokenizer, model, batch, args)
            for sample, response in zip(batch, responses):
                append_result(output, sample, args, model_name, response, None)
                progress.update(1)
        except RuntimeError as exc:
            if "out of memory" in str(exc).lower() and torch.cuda.is_available():
                torch.cuda.empty_cache()
            if len(batch) == 1:
                append_result(output, batch[0], args, model_name, "", str(exc))
                progress.update(1)
                continue
            for sample in batch:
                try:
                    response = generate_batch(tokenizer, model, [sample], args)[0]
                    append_result(output, sample, args, model_name, response, None)
                except RuntimeError as inner_exc:
                    if "out of memory" in str(inner_exc).lower() and torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    append_result(output, sample, args, model_name, "", str(inner_exc))
                progress.update(1)
    progress.close()
    print(f"responses={output} total={len(samples)} pending_written={len(pending)} batch_size={args.batch_size}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a local HuggingFace causal LM on the finance golden set.")
    parser.add_argument("--config", default="configs/finance_eval_public_v2.json")
    parser.add_argument("--golden-set")
    parser.add_argument("--responses-path")
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--model-name")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--max-input-tokens", type=int, default=4096)
    parser.add_argument("--max-new-tokens", type=int, default=1024)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--torch-dtype", choices=["auto", "float16", "bfloat16", "float32"], default="bfloat16")
    parser.add_argument("--device-map", default="auto")
    parser.add_argument("--trust-remote-code", action="store_true")
    parser.add_argument("--no-fast-tokenizer", action="store_true")
    parser.add_argument("--enable-thinking", action="store_true", help="Pass enable_thinking=true to chat templates that support it.")
    parser.add_argument("--system-prompt", default=CANDIDATE_SYSTEM_PROMPT)
    parser.add_argument("--overwrite", action="store_true")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
