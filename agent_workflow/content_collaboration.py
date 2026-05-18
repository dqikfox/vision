# Vision Content Collaboration Workflow
# Multi-agent Writer-Reviewer system for automated content creation and refinement

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from functools import partial
from pathlib import Path

from agent_framework import Agent, Message
from agent_framework.foundry import FoundryChatClient
from agent_framework.workflows import WorkflowContext, handler
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=False)

# ── Configuration ───────────────────────────────────────────────────────────


logger = logging.getLogger(__name__)


def _default_max_iterations() -> int:
    raw_value = os.getenv("WORKFLOW_MAX_ITERATIONS", "3")
    try:
        parsed = int(raw_value)
    except ValueError:
        logger.warning("Invalid WORKFLOW_MAX_ITERATIONS=%r; falling back to 3", raw_value)
        return 3

    if 1 <= parsed <= 1000:
        return parsed

    logger.warning("Out-of-range WORKFLOW_MAX_ITERATIONS=%r; falling back to 3", raw_value)
    return 3


def _default_output_dir() -> Path:
    configured = os.getenv("WORKFLOW_OUTPUT_DIR")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parent / "outputs"


@dataclass
class WorkflowConfig:
    """Configuration for the Writer-Reviewer workflow."""

    project_endpoint: str = field(default_factory=lambda: os.getenv("FOUNDRY_PROJECT_ENDPOINT", ""))
    model_deployment: str = field(default_factory=lambda: os.getenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "gpt-4o"))
    max_iterations: int = field(default_factory=_default_max_iterations)
    output_dir: Path = field(default_factory=_default_output_dir)

    def __post_init__(self) -> None:
        if not 1 <= self.max_iterations <= 1000:
            logger.warning("Out-of-range max_iterations=%r; falling back to 3", self.max_iterations)
            self.max_iterations = 3

        self.output_dir = Path(self.output_dir)
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.error("Failed to create workflow output directory %s: %s", self.output_dir, exc)
            raise


# ── Content Types ────────────────────────────────────────────────────────────


@dataclass
class ContentRequest:
    """User request for content creation."""

    topic: str
    content_type: str = "documentation"  # documentation, code, blog, review
    tone: str = "professional"
    length: str = "medium"  # short, medium, long
    requirements: list[str] = field(default_factory=list)
    context: str = ""


@dataclass
class ContentDraft:
    """Content produced by the Writer agent."""

    content: str
    iteration: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ReviewFeedback:
    """Feedback produced by the Reviewer agent."""

    feedback: str
    suggestions: list[str] = field(default_factory=list)
    approved: bool = False
    iteration: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CollaborationResult:
    """Final result of the Writer-Reviewer collaboration."""

    final_content: str
    iterations: int
    feedback_history: list[ReviewFeedback] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)


# ── Writer Agent ───────────────────────────────────────────────────────────


class WriterAgent:
    """Agent responsible for creating initial content and refining based on feedback."""

    def __init__(self, client: FoundryChatClient):
        self.client = client
        self.system_prompt = """You are an expert Content Writer specializing in technical documentation and software development content.

Your responsibilities:
1. Create clear, engaging, and accurate content based on user requirements
2. Adapt your writing style to match the requested tone and audience
3. Incorporate reviewer feedback to improve content quality
4. Maintain consistency with project standards and conventions

When writing:
- Start with a clear structure (outline, introduction, body, conclusion)
- Use appropriate formatting (headers, lists, code blocks)
- Include examples where relevant
- Ensure technical accuracy
- Write concisely but comprehensively

When revising:
- Address all reviewer feedback points
- Maintain the original intent while improving clarity
- Preserve important technical details
- Explain changes if significant revisions are made"""

    async def create_initial(self, request: ContentRequest) -> ContentDraft:
        """Create initial content based on user request."""

        prompt = f"""Create {request.content_type} content about: {request.topic}

Tone: {request.tone}
Length: {request.length}
Context: {request.context}

Requirements:
{chr(10).join(f"- {req}" for req in request.requirements)}

Please provide well-structured, engaging content that meets these requirements."""

        async with Agent(client=self.client, name="ContentWriter", instructions=self.system_prompt) as agent:
            response = await agent.run(prompt)
            return ContentDraft(content=response.text, iteration=1)

    async def revise(self, draft: ContentDraft, feedback: ReviewFeedback, request: ContentRequest) -> ContentDraft:
        """Revise content based on reviewer feedback."""

        prompt = f"""Revise the following content based on reviewer feedback.

Original Content:
{draft.content}

Reviewer Feedback:
{feedback.feedback}

Specific Suggestions:
{chr(10).join(f"- {s}" for s in feedback.suggestions)}

Please provide a revised version that addresses all feedback while maintaining the original intent and technical accuracy.
Explain briefly what changes you made and why."""

        async with Agent(client=self.client, name="ContentWriter", instructions=self.system_prompt) as agent:
            response = await agent.run(prompt)
            return ContentDraft(content=response.text, iteration=draft.iteration + 1)


# ── Reviewer Agent ───────────────────────────────────────────────────────────


class ReviewerAgent:
    """Agent responsible for reviewing content and providing actionable feedback."""

    def __init__(self, client: FoundryChatClient):
        self.client = client
        self.system_prompt = """You are an expert Content Reviewer specializing in technical documentation quality assurance.

Your responsibilities:
1. Evaluate content for clarity, accuracy, completeness, and engagement
2. Provide specific, actionable feedback
3. Suggest concrete improvements
4. Determine when content meets quality standards

Review criteria:
- CLARITY: Is the content easy to understand? Is the structure logical?
- ACCURACY: Is the technical information correct? Are code examples valid?
- COMPLETENESS: Does it cover all necessary aspects? Are there gaps?
- ENGAGEMENT: Is it interesting? Does it maintain reader attention?
- STYLE: Is the tone appropriate? Is formatting consistent?
- CONVENTIONS: Does it follow project standards and best practices?

Provide feedback in this format:
1. Overall assessment (2-3 sentences)
2. Specific issues found (bullet points)
3. Actionable suggestions for improvement (numbered list)
4. APPROVE or REVISE recommendation"""

    async def review(self, draft: ContentDraft, request: ContentRequest) -> ReviewFeedback:
        """Review content and provide feedback."""

        prompt = f"""Review the following {request.content_type} content about "{request.topic}".

Content to Review:
{draft.content}

Original Requirements:
{chr(10).join(f"- {req}" for req in request.requirements)}

Please provide:
1. Brief overall assessment
2. Specific issues (clarity, accuracy, completeness, style)
3. Actionable suggestions for improvement
4. Final verdict: APPROVE or REVISE

Be concise but thorough. Focus on the most important improvements."""

        async with Agent(client=self.client, name="ContentReviewer", instructions=self.system_prompt) as agent:
            response = await agent.run(prompt)

            # Parse response for approval status
            approved = "APPROVE" in response.text.upper() or "APPROVED" in response.text.upper()

            # Extract suggestions (lines starting with numbers or dashes)
            lines = response.text.split("\n")
            suggestions = [
                line.strip("- ").strip()
                for line in lines
                if line.strip().startswith(("- ", "1.", "2.", "3.", "4.", "5."))
            ]

            return ReviewFeedback(
                feedback=response.text,
                suggestions=suggestions[:5],  # Top 5 suggestions
                approved=approved,
                iteration=draft.iteration,
            )


# ── Workflow Definition ────────────────────────────────────────────────────


class ContentCollaborationWorkflow:
    """Multi-agent workflow for Writer-Reviewer content collaboration."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.credential = DefaultAzureCredential()
        self.client = FoundryChatClient(
            project_endpoint=config.project_endpoint, model=config.model_deployment, credential=self.credential
        )
        self.writer = WriterAgent(self.client)
        self.reviewer = ReviewerAgent(self.client)

    async def execute(self, request: ContentRequest) -> CollaborationResult:
        """Execute the Writer-Reviewer collaboration workflow."""

        print(f"📝 Starting content collaboration for: {request.topic}")
        print(f"   Type: {request.content_type} | Tone: {request.tone} | Max iterations: {self.config.max_iterations}")

        # Step 1: Writer creates initial content
        print("\n🖊️  Writer: Creating initial content...")
        draft = await self.writer.create_initial(request)
        print(f"   ✓ Initial draft created (iteration {draft.iteration})")

        feedback_history = []
        feedback: ReviewFeedback | None = None

        # Step 2-4: Review and Revise loop
        for iteration in range(self.config.max_iterations):
            print(f"\n🔍 Reviewer: Reviewing content (iteration {iteration + 1})...")
            feedback = await self.reviewer.review(draft, request)
            feedback_history.append(feedback)

            print(f"   {'✓' if feedback.approved else '⚠'}  Review: {feedback.feedback[:100]}...")

            if feedback.approved:
                print(f"   ✓ Content approved after {iteration + 1} review(s)")
                break

            if iteration < self.config.max_iterations - 1:
                print("\n🖊️  Writer: Revising based on feedback...")
                draft = await self.writer.revise(draft, feedback, request)
                print(f"   ✓ Revision completed (iteration {draft.iteration})")
            else:
                print(f"   ⚠ Maximum iterations ({self.config.max_iterations}) reached")

        # Compile final result
        result = CollaborationResult(
            final_content=draft.content,
            iterations=draft.iteration,
            feedback_history=feedback_history,
            metadata={
                "topic": request.topic,
                "content_type": request.content_type,
                "timestamp": datetime.now().isoformat(),
                "approved": feedback.approved if feedback_history and feedback is not None else False,
            },
        )

        # Save output
        await self._save_result(result, request)

        print("\n✅ Collaboration complete!")
        print(f"   Final content length: {len(result.final_content)} characters")
        print(f"   Total iterations: {result.iterations}")
        print(f"   Reviews completed: {len(feedback_history)}")

        return result

    async def _save_result(self, result: CollaborationResult, request: ContentRequest) -> None:
        """Save the collaboration result to file."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{request.content_type}-{request.topic.replace(' ', '-')[:30]}-{timestamp}.md"
        filepath = self.config.output_dir / filename

        content = f"""# {request.topic}

**Content Type:** {request.content_type}
**Tone:** {request.tone}
**Generated:** {result.metadata["timestamp"]}
**Iterations:** {result.iterations}
**Status:** {"✅ Approved" if result.metadata["approved"] else "⚠️ Max iterations reached"}

---

{result.final_content}

---

## Review History

"""

        for i, feedback in enumerate(result.feedback_history, 1):
            content += f"""### Review {i} (Iteration {feedback.iteration})

**Status:** {"✅ Approved" if feedback.approved else "📝 Revision Requested"}

**Feedback:**
{feedback.feedback}

**Key Suggestions:**
{chr(10).join(f"- {s}" for s in feedback.suggestions)}

---

"""

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, partial(filepath.write_text, content, encoding="utf-8"))
        print(f"   💾 Output saved to: {filepath}")


# ── HTTP Server Handler ──────────────────────────────────────────────────────


class WorkflowHandler:
    """HTTP request handler for the workflow."""

    def __init__(self) -> None:
        self.config = WorkflowConfig()
        self.workflow = ContentCollaborationWorkflow(self.config)

    @handler
    async def create_content(self, messages: list[Message], ctx: WorkflowContext) -> str:
        """Handle content creation requests."""

        # Extract request from messages
        user_message = messages[-1].text if messages else ""

        # Parse request (simple parsing for demo)
        lines = user_message.split("\n")
        topic = lines[0] if lines else "Untitled Content"
        content_type = "documentation"

        # Detect content type from message
        if any(kw in user_message.lower() for kw in ["code", "function", "class", "api"]):
            content_type = "code"
        elif any(kw in user_message.lower() for kw in ["blog", "article", "post"]):
            content_type = "blog"
        elif any(kw in user_message.lower() for kw in ["review", "analysis"]):
            content_type = "review"

        request = ContentRequest(
            topic=topic,
            content_type=content_type,
            requirements=[line.strip("- ") for line in lines[1:] if line.strip().startswith("-")],
            context=user_message,
        )

        # Execute workflow
        result = await self.workflow.execute(request)

        return result.final_content


# ── Main Entry Point ─────────────────────────────────────────────────────────


async def main() -> None:
    """Run the content collaboration workflow."""

    # Example usage
    config = WorkflowConfig()
    workflow = ContentCollaborationWorkflow(config)

    # Sample request
    request = ContentRequest(
        topic="OpenClaw Elite Memory System",
        content_type="documentation",
        tone="professional",
        length="medium",
        requirements=[
            "Explain the memory architecture",
            "Include code examples",
            "Describe self-awareness features",
            "Show usage patterns",
        ],
        context="Technical documentation for the Vision project",
    )

    result = await workflow.execute(request)

    print("\n" + "=" * 60)
    print("FINAL CONTENT:")
    print("=" * 60)
    print(result.final_content[:500] + "..." if len(result.final_content) > 500 else result.final_content)


if __name__ == "__main__":
    asyncio.run(main())
