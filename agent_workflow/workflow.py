# Vision Content Collaboration Workflow
# Writer-Reviewer multi-agent system for automated content creation

import asyncio

from agent_framework.workflows import WorkflowBuilder
from content_collaboration import ContentCollaborationWorkflow, ContentRequest, WorkflowConfig, WorkflowHandler

# ── Workflow Builder ─────────────────────────────────────────────────────────


def create_content_workflow():
    """Create the Writer-Reviewer workflow using WorkflowBuilder."""

    handler = WorkflowHandler()

    workflow = WorkflowBuilder(start_executor=handler.create_content).build()

    return workflow


# ── Direct Execution ─────────────────────────────────────────────────────────


async def run_collaboration(
    topic: str, content_type: str = "documentation", requirements: list[str] = None, max_iterations: int = 3
) -> str:
    """Run a content collaboration directly."""

    config = WorkflowConfig(max_iterations=max_iterations)
    workflow = ContentCollaborationWorkflow(config)

    request = ContentRequest(
        topic=topic,
        content_type=content_type,
        requirements=requirements or [],
        context=f"Content collaboration for: {topic}",
    )

    result = await workflow.execute(request)
    return result.final_content


# ── HTTP Server Entry Point ───────────────────────────────────────────────────


async def run_server():
    """Run the workflow as an HTTP server."""
    from azure.ai.agentserver.agentframework import from_agent_framework

    workflow = create_content_workflow()
    await from_agent_framework(workflow).run_async()


# ── Example Usage ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "server":
        # Run as HTTP server
        asyncio.run(run_server())
    else:
        # Run example collaboration
        asyncio.run(
            run_collaboration(
                topic="Getting Started with Vision",
                content_type="documentation",
                requirements=["Clear installation steps", "Basic usage examples", "Troubleshooting section"],
            )
        )
