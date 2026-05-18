r"""
Invoke an Azure AI Foundry agent through AIProjectClient.

Defaults are preconfigured for the dqikst Foundry project and ultron agent.

Usage:
    python scripts\invoke_foundry_agent.py
    python scripts\invoke_foundry_agent.py --prompt "Summarize your capabilities."
    python scripts\invoke_foundry_agent.py --agent-version 3 --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from azure.ai.projects import AIProjectClient
from azure.core.exceptions import ClientAuthenticationError, HttpResponseError
from azure.identity import CredentialUnavailableError, DefaultAzureCredential

DEFAULT_ENDPOINT = "https://dqikst-agent-resource.services.ai.azure.com/api/projects/dqikst-agent"
DEFAULT_AGENT_NAME = "ultron"
DEFAULT_AGENT_VERSION = "2"
DEFAULT_PROMPT = "Tell me what you can help with."


def _env(name: str, default: str) -> str:
    value = os.getenv(name, "").strip()
    return value or default


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Invoke an Azure AI Foundry agent through AIProjectClient.",
        epilog=(
            "Examples:\n"
            "  python scripts\\invoke_foundry_agent.py\n"
            "  python scripts\\invoke_foundry_agent.py --prompt \"Summarize your capabilities.\"\n"
            "  python scripts\\invoke_foundry_agent.py --agent-version 3 --json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--endpoint",
        default=_env("FOUNDRY_PROJECT_ENDPOINT", DEFAULT_ENDPOINT),
        help="Foundry project endpoint. Defaults to the dqikst project endpoint.",
    )
    parser.add_argument(
        "--agent-name",
        default=_env("FOUNDRY_AGENT_NAME", DEFAULT_AGENT_NAME),
        help="Agent name to reference.",
    )
    parser.add_argument(
        "--agent-version",
        default=_env("FOUNDRY_AGENT_VERSION", DEFAULT_AGENT_VERSION),
        help="Agent version to reference.",
    )
    parser.add_argument(
        "--prompt",
        default=_env("FOUNDRY_AGENT_PROMPT", DEFAULT_PROMPT),
        help="User message to send to the agent.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full response payload as JSON when possible.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print resolved endpoint and agent reference before invoking.",
    )
    return parser


def _response_to_json(response: Any) -> str:
    if hasattr(response, "model_dump_json"):
        return response.model_dump_json(indent=2)
    if hasattr(response, "model_dump"):
        return json.dumps(response.model_dump(), indent=2, default=str)
    if hasattr(response, "as_dict"):
        return json.dumps(response.as_dict(), indent=2, default=str)
    return json.dumps({"output_text": getattr(response, "output_text", "")}, indent=2)


def invoke_agent(endpoint: str, agent_name: str, agent_version: str, prompt: str, emit_json: bool) -> int:
    credential = DefaultAzureCredential()
    project_client = AIProjectClient(endpoint=endpoint, credential=credential)

    try:
        openai_client = project_client.get_openai_client()
        response = openai_client.responses.create(
            input=[{"role": "user", "content": prompt}],
            extra_body={
                "agent_reference": {
                    "name": agent_name,
                    "version": str(agent_version),
                    "type": "agent_reference",
                }
            },
        )
    except CredentialUnavailableError:
        print(
            "Azure credentials are not available. Sign in with 'az login' or provide a supported "
            "DefaultAzureCredential source before retrying.",
            file=sys.stderr,
        )
        return 2
    except ClientAuthenticationError:
        print(
            "Azure authentication failed. Run 'az login' for this account or refresh the configured "
            "credential source, then retry.",
            file=sys.stderr,
        )
        return 2
    except HttpResponseError as exc:
        print("Foundry invocation failed.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        project_client.close()
        credential.close()

    if emit_json:
        print(_response_to_json(response))
        return 0

    print(getattr(response, "output_text", "").strip())
    return 0


def main() -> int:
    args = build_parser().parse_args()
    if args.verbose:
        print(f"Endpoint: {args.endpoint}")
        print(f"Agent: {args.agent_name}")
        print(f"Version: {args.agent_version}")
    return invoke_agent(
        endpoint=args.endpoint,
        agent_name=args.agent_name,
        agent_version=args.agent_version,
        prompt=args.prompt,
        emit_json=args.json,
    )


if __name__ == "__main__":
    raise SystemExit(main())
