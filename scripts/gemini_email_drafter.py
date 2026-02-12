#!/usr/bin/env python3
"""
Gemini Email Drafter - Automated startup credit application emails

Uses Google Gemini API to draft professional emails for startup programs.
Integrates with Claude Code task system for team coordination.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
import time

try:
    from google import genai
except ImportError:
    print("Error: google-genai not installed")
    print("Run: pip install google-genai")
    sys.exit(1)


class GeminiEmailDrafter:
    """Draft startup program application emails using Gemini API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini email drafter.

        Args:
            api_key: Gemini API key (defaults to CLAUDE_GEMINI_244_KEY env var)
        """
        self.api_key = api_key or os.environ.get(
            "CLAUDE_GEMINI_244_KEY",
            "AIzaSyDdPIAHciJa1zVcnu6rF_J4s1U7Bka5UMI"
        )

        # Configure Gemini client
        self.client = genai.Client(api_key=self.api_key)

        # Use latest stable model (as of Feb 2026)
        self.model_name = 'gemini-2.0-flash-001'

        # Company details
        self.company_info = {
            "name": "jadecli-ai",
            "product": "Team Agents SDK",
            "description": "Multi-agent orchestration framework for Claude Code",
            "stage": "Early development, building core SDK",
            "tech_stack": ["Claude API (Opus/Sonnet)", "Python", "TypeScript", "FastMCP", "Redis"],
            "focus": "Agent team coordination, task management, and workflow automation"
        }

    def draft_email(
        self,
        service: str,
        program: str,
        details: Dict[str, str],
        max_retries: int = 3
    ) -> Optional[str]:
        """
        Draft email using Gemini API.

        Args:
            service: Service name (e.g., "Neon Database")
            program: Program name (e.g., "Startup Program")
            details: Dict with use_case, eligibility, benefit, application_url
            max_retries: Maximum retry attempts

        Returns:
            Drafted email text or None if failed
        """
        prompt = self._build_prompt(service, program, details)

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                print(f"Gemini API error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return None

    def _build_prompt(self, service: str, program: str, details: Dict[str, str]) -> str:
        """Build Gemini prompt for email drafting."""
        return f"""Draft a professional startup program application email.

**Service:** {service}
**Program:** {program}

**Company Information:**
- Name: {self.company_info['name']}
- Product: {self.company_info['product']}
- Description: {self.company_info['description']}
- Stage: {self.company_info['stage']}
- Tech Stack: {', '.join(self.company_info['tech_stack'])}
- Focus: {self.company_info['focus']}

**Program Details:**
- Use Case: {details.get('use_case', 'Agent orchestration and development tooling')}
- Eligibility: {details.get('eligibility', 'Early-stage startup')}
- Benefit: {details.get('benefit', 'Startup credits')}
- Application: {details.get('application_url', 'N/A')}

**Email Requirements:**
1. Professional but authentic tone (not overly formal)
2. Clearly explain our genuine need for {service}
3. Show we meet eligibility requirements
4. Demonstrate technical competence in AI/agents space
5. Highlight specific use case for {service}
6. Include measurable traction if applicable
7. Clear call-to-action at the end
8. Keep under 250 words
9. No buzzwords or fluff

**Output Format:**
Subject: [compelling subject line]

[email body with proper paragraphs]

Best regards,
[signature placeholder]

**Important:** Write as if you're a technical founder genuinely excited about the product and service. Be specific, not generic."""

    def save_draft(
        self,
        service: str,
        program: str,
        content: str,
        details: Dict[str, str],
        output_dir: str = "drafts"
    ) -> str:
        """
        Save email draft to markdown file.

        Args:
            service: Service name
            program: Program name
            content: Drafted email content
            details: Program details dict
            output_dir: Output directory for drafts

        Returns:
            Path to saved file
        """
        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)

        # Generate filename
        date = datetime.now().strftime("%Y-%m-%d")
        safe_service = service.lower().replace(' ', '-').replace('/', '-')
        safe_program = program.lower().replace(' ', '-').replace('/', '-')
        filename = f"{output_dir}/{date}-{safe_service}-{safe_program}.md"

        # Build markdown content
        md_content = f"""---
service: {service}
program: {program}
credit_amount: {details.get('benefit', 'N/A')}
application_url: {details.get('application_url', 'N/A')}
eligibility: {details.get('eligibility', 'N/A')}
drafted: {date}
status: draft
---

# Email Draft: {service} - {program}

**To:** {details.get('application_url', 'Application form/email')}

---

{content}

---

## Review Checklist
- [ ] Company name correct (jadecli-ai)
- [ ] Technical details accurate
- [ ] Use case specific and genuine
- [ ] Tone professional but authentic
- [ ] Eligibility demonstrated
- [ ] Call-to-action clear
- [ ] Under 250 words
- [ ] Links/URLs included

## Next Steps
1. Review and edit email above
2. Customize with any additional details
3. Submit via {details.get('application_url', 'application URL')}
4. Track submission in `../docs/STARTUP_CREDITS_TRACKER.md`

## Generated via
- Tool: Gemini API (gemini-2.0-flash-001)
- Agent: gemini-email-drafter
- Date: {datetime.now().isoformat()}
"""

        # Save file
        with open(filename, 'w') as f:
            f.write(md_content)

        return filename

    def draft_all_services(self, services: List[Dict], output_dir: str = "drafts") -> Dict[str, str]:
        """
        Draft emails for all services.

        Args:
            services: List of service dicts with service, program, and details
            output_dir: Output directory for drafts

        Returns:
            Dict mapping service name to draft file path
        """
        results = {}

        print(f"\n{'='*60}")
        print(f"Drafting emails for {len(services)} startup programs")
        print(f"{'='*60}\n")

        for idx, service_info in enumerate(services, 1):
            service = service_info['service']
            program = service_info['program']

            print(f"[{idx}/{len(services)}] Drafting: {service} - {program}")

            # Draft email via Gemini
            content = self.draft_email(
                service=service,
                program=program,
                details=service_info.get('details', {})
            )

            if content:
                # Save draft
                filepath = self.save_draft(
                    service=service,
                    program=program,
                    content=content,
                    details=service_info.get('details', {}),
                    output_dir=output_dir
                )
                results[service] = filepath
                print(f"  ✓ Saved to: {filepath}")
            else:
                results[service] = None
                print(f"  ✗ Failed to generate")

            # Rate limiting
            time.sleep(1)

        print(f"\n{'='*60}")
        print(f"Drafting complete:")
        print(f"  ✓ Succeeded: {sum(1 for v in results.values() if v)}")
        print(f"  ✗ Failed: {sum(1 for v in results.values() if not v)}")
        print(f"{'='*60}\n")

        return results


def get_startup_programs() -> List[Dict]:
    """
    Get list of startup programs to apply to.

    Returns:
        List of dicts with service, program, and details
    """
    return [
        {
            "service": "Vercel",
            "program": "AI Accelerator",
            "details": {
                "benefit": "$100K+ in credits",
                "eligibility": "AI-focused startups, deadline Feb 16, 2026",
                "use_case": "Deploy agent management dashboard, serverless API endpoints for Claude agent orchestration",
                "application_url": "https://vercel.com/ai-accelerator",
                "urgency": "HIGH - Deadline Feb 16"
            }
        },
        {
            "service": "Neon Database",
            "program": "Startup Program",
            "details": {
                "benefit": "Up to $100K in credits",
                "eligibility": "VC-backed startups, <$5M raised, <12 months old",
                "use_case": "Store agent state, task queues, and orchestration metadata for multi-agent systems. Requires serverless Postgres for scaling agent teams.",
                "application_url": "https://neon.com/startups"
            }
        },
        {
            "service": "Anthropic Claude",
            "program": "Startup Program",
            "details": {
                "benefit": "Up to $100K in API credits",
                "eligibility": "VC-backed AI startups with traction",
                "use_case": "Core agent orchestration using Claude Opus/Sonnet models. Building Team Agents SDK that coordinates multiple Claude agents for software development workflows.",
                "application_url": "https://claude.com/programs/startups"
            }
        },
        {
            "service": "Aiven",
            "program": "Cluster Startup Program",
            "details": {
                "benefit": "$12K to $100K over 12 months",
                "eligibility": "≤7 years old, Pre-seed to Series B, VC/accelerator affiliated",
                "use_case": "Dragonfly/Redis for agent state caching, task queue management, and real-time coordination between distributed agents.",
                "application_url": "https://aiven.io/startups"
            }
        },
        {
            "service": "Langfuse",
            "program": "Startup Program",
            "details": {
                "benefit": "50% off for 12 months",
                "eligibility": "Bootstrapped or ≤$5M raised, <5 years old",
                "use_case": "LLM observability for tracking agent performance, token usage, and conversation flows. Critical for debugging multi-agent orchestration.",
                "application_url": "startups@langfuse.com"
            }
        },
        {
            "service": "Sentry",
            "program": "Startup Program",
            "details": {
                "benefit": "$5K in credits",
                "eligibility": "<2 years old, <$5M raised, new to Sentry",
                "use_case": "Error tracking for production agent deployments. Monitor agent failures, API errors, and system health across distributed teams.",
                "application_url": "https://sentry.io/for/startups/apply/"
            }
        },
        {
            "service": "Vercel",
            "program": "For Startups",
            "details": {
                "benefit": "$600 credits ($200/mo × 3)",
                "eligibility": "Early-stage startups",
                "use_case": "Deploy agent dashboard UI and documentation site. Serverless functions for webhook handling and API proxying.",
                "application_url": "https://vercel.com/startups"
            }
        },
    ]


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Draft startup program application emails using Gemini API')
    parser.add_argument('--output-dir', default='drafts', help='Output directory for drafts')
    parser.add_argument('--test', action='store_true', help='Test with single service only')

    args = parser.parse_args()

    # Initialize drafter
    drafter = GeminiEmailDrafter()

    # Get services
    services = get_startup_programs()

    # Test mode: only draft first service
    if args.test:
        print("\n⚠️  TEST MODE: Drafting one email only\n")
        services = services[:1]

    # Draft all emails
    results = drafter.draft_all_services(services, output_dir=args.output_dir)

    # Print summary
    print("\n📧 Drafts ready for review:")
    for service, filepath in results.items():
        if filepath:
            print(f"  • {service}: {filepath}")
        else:
            print(f"  ✗ {service}: FAILED")

    # Exit code
    sys.exit(0 if all(results.values()) else 1)
