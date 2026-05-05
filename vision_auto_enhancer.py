# Vision Auto-Enhancement Integration
# Connects the Writer-Reviewer workflow to Vision for automated repo improvement

import asyncio
import json

# Import the workflow
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "agent_workflow"))

from content_collaboration import CollaborationResult, ContentCollaborationWorkflow, ContentRequest, WorkflowConfig


class VisionAutoEnhancer:
    """Automated enhancement system for the Vision project."""

    def __init__(self):
        self.config = WorkflowConfig(
            max_iterations=3, output_dir=Path("c:/project/vision/agent_workflow/outputs/enhancements")
        )
        self.workflow = ContentCollaborationWorkflow(self.config)
        self.enhancement_log = []

    async def enhance_documentation(self, topic: str, source_file: Path | None = None) -> CollaborationResult:
        """Enhance existing documentation or create new docs."""

        # Read source content if provided
        context = ""
        if source_file and source_file.exists():
            context = source_file.read_text(encoding="utf-8")[:2000]  # First 2000 chars

        request = ContentRequest(
            topic=topic,
            content_type="documentation",
            tone="professional",
            requirements=[
                "Clear and concise explanations",
                "Code examples where relevant",
                "Step-by-step instructions",
                "Troubleshooting section",
                "Follow Vision project conventions",
            ],
            context=f"Vision project documentation. Source: {source_file}\n\n{context}",
        )

        result = await self.workflow.execute(request)
        self._log_enhancement("documentation", topic, result)
        return result

    async def generate_code_review(self, code_file: Path, review_focus: list[str] = None) -> CollaborationResult:
        """Generate a comprehensive code review document."""

        code_content = code_file.read_text(encoding="utf-8") if code_file.exists() else ""

        request = ContentRequest(
            topic=f"Code Review: {code_file.name}",
            content_type="review",
            tone="professional",
            requirements=review_focus
            or [
                "Analyze code structure and patterns",
                "Identify potential issues",
                "Suggest improvements",
                "Check against best practices",
                "Provide actionable feedback",
            ],
            context=f"Reviewing code file: {code_file}\n\n```\n{code_content[:3000]}\n```",
        )

        result = await self.workflow.execute(request)
        self._log_enhancement("code_review", code_file.name, result)
        return result

    async def create_blog_post(self, feature: str, highlights: list[str]) -> CollaborationResult:
        """Create a blog post about a new feature."""

        request = ContentRequest(
            topic=f"Vision Update: {feature}",
            content_type="blog",
            tone="enthusiastic",
            requirements=[
                "Engaging introduction",
                "Feature highlights with examples",
                "Usage scenarios",
                "Call to action",
                "Links to documentation",
            ],
            context=f"New Vision feature: {feature}\nHighlights: {', '.join(highlights)}",
        )

        result = await self.workflow.execute(request)
        self._log_enhancement("blog_post", feature, result)
        return result

    async def enhance_readme(self) -> CollaborationResult:
        """Enhance the main README.md with latest features."""

        readme_path = Path("c:/project/vision/README.md")
        current_readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

        request = ContentRequest(
            topic="Vision Project README Enhancement",
            content_type="documentation",
            tone="professional",
            requirements=[
                "Clear project overview",
                "Feature highlights with OpenClaw Elite",
                "Quick start guide",
                "Installation instructions",
                "Links to detailed docs",
            ],
            context=f"Current README:\n{current_readme[:2000]}\n\nNew features to highlight: OpenClaw Elite, Phone Control, Memory System",
        )

        result = await self.workflow.execute(request)
        self._log_enhancement("readme", "README.md", result)
        return result

    async def generate_skill_documentation(self, skill_name: str, skill_path: Path) -> CollaborationResult:
        """Generate documentation for a Vision skill."""

        skill_content = ""
        if skill_path.exists():
            skill_content = skill_path.read_text(encoding="utf-8")[:2000]

        request = ContentRequest(
            topic=f"Vision Skill: {skill_name}",
            content_type="documentation",
            tone="technical",
            requirements=[
                "Skill purpose and use cases",
                "How to invoke",
                "Parameters and options",
                "Examples",
                "Troubleshooting",
            ],
            context=f"Skill file: {skill_path}\n\nContent:\n{skill_content}",
        )

        result = await self.workflow.execute(request)
        self._log_enhancement("skill_doc", skill_name, result)
        return result

    def _log_enhancement(self, enhancement_type: str, target: str, result: CollaborationResult):
        """Log the enhancement for tracking."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": enhancement_type,
            "target": target,
            "iterations": result.iterations,
            "approved": result.metadata.get("approved", False),
            "output_path": str(self.config.output_dir),
        }
        self.enhancement_log.append(log_entry)

        # Save log
        log_file = self.config.output_dir / "enhancement_log.json"
        log_file.write_text(json.dumps(self.enhancement_log, indent=2))

    async def run_full_enhancement_cycle(self):
        """Run a complete enhancement cycle for the Vision project."""

        print("🚀 Starting Vision Auto-Enhancement Cycle")
        print("=" * 60)

        enhancements = []

        # 1. Enhance main README
        print("\n📄 Enhancing README.md...")
        readme_result = await self.enhance_readme()
        enhancements.append(("README", readme_result))

        # 2. Generate docs for OpenClaw Elite
        print("\n🦞 Documenting OpenClaw Elite...")
        elite_result = await self.enhance_documentation(
            topic="OpenClaw Elite Complete Guide", source_file=Path("c:/project/vision/openclaw-elite.ps1")
        )
        enhancements.append(("OpenClaw Elite", elite_result))

        # 3. Generate docs for Phone Control
        print("\n📱 Documenting Phone Control...")
        phone_result = await self.enhance_documentation(
            topic="Phone Control Integration", source_file=Path("c:/project/vision/openclaw-elite-phone.ps1")
        )
        enhancements.append(("Phone Control", phone_result))

        # 4. Generate docs for Memory System
        print("\n🧠 Documenting Memory System...")
        memory_result = await self.enhance_documentation(
            topic="Memory and Self-Awareness System", source_file=Path("c:/project/vision/openclaw-elite-memory.ps1")
        )
        enhancements.append(("Memory System", memory_result))

        # 5. Create blog post about latest features
        print("\n📝 Creating feature announcement blog post...")
        blog_result = await self.create_blog_post(
            feature="OpenClaw Elite with Memory and Phone Control",
            highlights=[
                "Multi-agent workflow support",
                "Full phone control via ADB",
                "Persistent memory and self-awareness",
                "12 MCP servers integration",
                "25+ skills available",
            ],
        )
        enhancements.append(("Blog Post", blog_result))

        # Summary
        print("\n" + "=" * 60)
        print("✅ Enhancement Cycle Complete!")
        print("=" * 60)

        for name, result in enhancements:
            status = "✅ Approved" if result.metadata.get("approved") else "⚠️ Max iterations"
            print(f"  {name}: {result.iterations} iterations - {status}")

        print(f"\n📁 All outputs saved to: {self.config.output_dir}")
        print(f"📊 Enhancement log: {self.config.output_dir / 'enhancement_log.json'}")

        return enhancements


# ── CLI Interface ───────────────────────────────────────────────────────────


async def main():
    """Main entry point for the auto-enhancer."""
    import argparse

    parser = argparse.ArgumentParser(description="Vision Auto-Enhancement System")
    parser.add_argument("--full-cycle", action="store_true", help="Run full enhancement cycle")
    parser.add_argument("--readme", action="store_true", help="Enhance README only")
    parser.add_argument("--docs", metavar="TOPIC", help="Generate documentation for topic")
    parser.add_argument("--blog", metavar="FEATURE", help="Create blog post about feature")
    parser.add_argument("--review", metavar="FILE", help="Review code file")

    args = parser.parse_args()

    enhancer = VisionAutoEnhancer()

    if args.full_cycle:
        await enhancer.run_full_enhancement_cycle()
    elif args.readme:
        result = await enhancer.enhance_readme()
        print(f"\n✅ README enhanced: {result.iterations} iterations")
    elif args.docs:
        result = await enhancer.enhance_documentation(args.docs)
        print(f"\n✅ Documentation created: {result.iterations} iterations")
    elif args.blog:
        result = await enhancer.create_blog_post(args.blog, ["New feature", "Enhanced capabilities"])
        print(f"\n✅ Blog post created: {result.iterations} iterations")
    elif args.review:
        result = await enhancer.generate_code_review(Path(args.review))
        print(f"\n✅ Code review generated: {result.iterations} iterations")
    else:
        # Default: run full cycle
        await enhancer.run_full_enhancement_cycle()


if __name__ == "__main__":
    asyncio.run(main())
