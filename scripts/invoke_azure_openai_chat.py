r"""Send a chat prompt to an Azure-hosted OpenAI-compatible endpoint.

Defaults target the dqikst Azure AI resource and a `gpt-4o` deployment.

Usage:
    python scripts\invoke_azure_openai_chat.py
    python scripts\invoke_azure_openai_chat.py --prompt "What is the capital of France?"
    python scripts\invoke_azure_openai_chat.py --model gpt-4o-mini
"""

from __future__ import annotations

import argparse
import os
import sys

from openai import APIError, OpenAI

DEFAULT_BASE_URL = "https://dqikst-agent-resource.services.ai.azure.com/openai/v1"
DEFAULT_MODEL = "gpt-4o"
DEFAULT_PROMPT = "What is the capital of France?"
DEFAULT_SYSTEM_PROMPT = "You are a concise helpful assistant."


def _env(name: str, default: str) -> str:
    value = os.getenv(name, "").strip()
    return value or default


def _resolve_api_key() -> str | None:
    for variable_name in ("AZURE_OPENAI_API_KEY", "OPENAI_API_KEY"):
        value = os.getenv(variable_name, "").strip()
        if value:
            return value
    return None


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the Azure OpenAI smoke-test script."""
    parser = argparse.ArgumentParser(
        description="Send a chat prompt to an Azure-hosted OpenAI-compatible endpoint.",
        epilog=(
            "Examples:\n"
            "  python scripts\\invoke_azure_openai_chat.py\n"
            '  python scripts\\invoke_azure_openai_chat.py --prompt "Summarize your capabilities."\n'
            "  python scripts\\invoke_azure_openai_chat.py --model gpt-4o-mini"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--base-url",
        default=_env("AZURE_OPENAI_BASE_URL", DEFAULT_BASE_URL),
        help="Azure-hosted OpenAI-compatible base URL.",
    )
    parser.add_argument(
        "--model",
        default=_env("AZURE_OPENAI_MODEL", DEFAULT_MODEL),
        help="Deployment or model name exposed by the endpoint.",
    )
    parser.add_argument(
        "--prompt",
        default=DEFAULT_PROMPT,
        help="User prompt to send.",
    )
    parser.add_argument(
        "--system-prompt",
        default=DEFAULT_SYSTEM_PROMPT,
        help="Optional system prompt prepended to the request.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print resolved endpoint and model before sending the request.",
    )
    return parser


def run_chat(base_url: str, model: str, prompt: str, system_prompt: str, verbose: bool) -> int:
    """Send a prompt to the configured Azure OpenAI-compatible endpoint.

    Args:
        base_url: The OpenAI-compatible endpoint base URL.
        model: The model or deployment name exposed by the endpoint.
        prompt: The user prompt.
        system_prompt: The system prompt to prepend.
        verbose: Whether to print resolved config before sending.

    Returns:
        Process-style exit code. Zero indicates success.
    """
    api_key = _resolve_api_key()
    if not api_key:
        print(
            "Missing API key. Set AZURE_OPENAI_API_KEY or OPENAI_API_KEY before running this script.",
            file=sys.stderr,
        )
        return 2

    if verbose:
        print(f"Base URL: {base_url}")
        print(f"Model: {model}")

    client = OpenAI(base_url=base_url, api_key=api_key)

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
    except APIError as exc:
        print("Azure OpenAI request failed.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    if not completion.choices:
        print("Request completed without any choices in the response.", file=sys.stderr)
        return 1

    message_content = completion.choices[0].message.content
    if not message_content:
        print("Request completed but returned an empty message.", file=sys.stderr)
        return 1

    print(message_content.strip())
    return 0


def main() -> int:
    """Parse CLI args and run the Azure OpenAI-compatible chat request."""
    args = build_parser().parse_args()
    return run_chat(
        base_url=args.base_url,
        model=args.model,
        prompt=args.prompt,
        system_prompt=args.system_prompt,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    raise SystemExit(main())
