#!/usr/bin/env python3
"""
Email Drafting Orchestrator

Coordinates Gemini-powered email drafting with Claude Code task system.
Can be run standalone or integrated with Claude agent teams.
"""

import sys
import os
from pathlib import Path
from gemini_email_drafter import GeminiEmailDrafter, get_startup_programs


def create_drafting_tasks():
    """
    Create tasks for email drafting workflow.

    Returns:
        List of task definitions
    """
    services = get_startup_programs()

    tasks = []
    for idx, service_info in enumerate(services, 1):
        service = service_info['service']
        program = service_info['program']
        details = service_info.get('details', {})

        # Determine priority based on urgency and credit amount
        urgency = details.get('urgency', '')
        benefit = details.get('benefit', '')

        if 'HIGH' in urgency or 'Feb 16' in str(details.get('eligibility', '')):
            priority = 'P0-critical'
        elif '$100K' in benefit or '$100,000' in benefit:
            priority = 'P1-high'
        else:
            priority = 'P2-medium'

        task = {
            'id': f"EMAIL-DRAFT-{idx:03d}",
            'subject': f"Draft application email: {service} - {program}",
            'description': f"""Draft professional application email for {service} {program}.

**Program Details:**
- Benefit: {details.get('benefit', 'N/A')}
- Eligibility: {details.get('eligibility', 'N/A')}
- Application: {details.get('application_url', 'N/A')}

**Use Case:**
{details.get('use_case', 'Agent orchestration tooling')}

**Deliverable:**
- Drafted email in `drafts/{service.lower().replace(' ', '-')}-{program.lower().replace(' ', '-')}.md`
- Email under 250 words
- Professional but authentic tone
- Specific technical use case
- Clear call-to-action

**Review Criteria:**
- [ ] Company name correct (jadecli-ai)
- [ ] Technical details accurate
- [ ] Meets eligibility requirements
- [ ] Under 250 words
- [ ] Links included
""",
            'activeForm': f"Drafting {service} application",
            'priority': priority,
            'metadata': {
                'service': service,
                'program': program,
                'benefit': details.get('benefit', ''),
                'application_url': details.get('application_url', ''),
                'urgency': urgency
            }
        }
        tasks.append(task)

    return tasks


def print_task_summary(tasks):
    """Print summary of tasks to be created."""
    print(f"\n{'='*70}")
    print(f"Email Drafting Workflow - {len(tasks)} Tasks")
    print(f"{'='*70}\n")

    # Group by priority
    by_priority = {}
    for task in tasks:
        priority = task['priority']
        by_priority.setdefault(priority, []).append(task)

    for priority in ['P0-critical', 'P1-high', 'P2-medium']:
        task_list = by_priority.get(priority, [])
        if task_list:
            print(f"{priority}: {len(task_list)} tasks")
            for task in task_list:
                service = task['metadata']['service']
                benefit = task['metadata'].get('benefit', '')
                print(f"  • {service}: {benefit}")
            print()


def draft_all_emails(output_dir: str = "drafts"):
    """
    Draft all emails using Gemini API.

    Args:
        output_dir: Directory for draft outputs
    """
    print("\n🚀 Starting email drafting workflow...\n")

    # Initialize drafter
    drafter = GeminiEmailDrafter()

    # Get services
    services = get_startup_programs()

    # Create tasks (for tracking)
    tasks = create_drafting_tasks()
    print_task_summary(tasks)

    # Draft all emails
    print(f"{'='*70}")
    print("Generating drafts via Gemini API...")
    print(f"{'='*70}\n")

    results = drafter.draft_all_services(services, output_dir=output_dir)

    # Generate submission instructions
    generate_submission_guide(results, output_dir)

    return results


def generate_submission_guide(results: dict, output_dir: str):
    """Generate a submission guide for the drafted emails."""
    guide_path = f"{output_dir}/SUBMISSION_GUIDE.md"

    content = f"""# Email Submission Guide

Generated: {Path(__file__).name}

## 📋 Quick Checklist

Before submitting each email:
1. [ ] Review draft for accuracy
2. [ ] Customize with specific company details
3. [ ] Verify eligibility requirements
4. [ ] Check word count (<250 words)
5. [ ] Copy to clipboard
6. [ ] Submit via application URL
7. [ ] Mark as submitted in tracker

---

## 🚨 Priority Order (By Deadline & Value)

### 1. URGENT - Submit This Week

"""

    # Add each service
    idx = 1
    for service, filepath in results.items():
        if filepath:
            content += f"""
### {idx}. {service}
- **Draft**: `{filepath}`
- **Status**: 🟡 Ready for review

**Next Steps:**
1. Review draft: `cat {filepath}`
2. Edit if needed
3. Submit application
4. Update tracker: `docs/STARTUP_CREDITS_TRACKER.md`

---
"""
            idx += 1

    content += """
## 📝 Submission Process

### For Web Forms
1. Open draft file
2. Copy email content (without frontmatter)
3. Open application URL
4. Paste into form
5. Review and submit
6. Mark as submitted in tracker

### For Email Applications
1. Open draft file
2. Copy subject line and body
3. Create new email
4. To: [application email]
5. Paste subject and body
6. Send
7. Mark as submitted in tracker

---

## 🎯 Success Metrics

Track in `docs/STARTUP_CREDITS_TRACKER.md`:
- [ ] Emails reviewed: 0/7
- [ ] Applications submitted: 0/7
- [ ] Responses received: 0/7
- [ ] Credits approved: $0/$417K

---

## 🔄 Follow-Up

- **Week 1**: Follow up on urgent applications (Vercel, Neon, Anthropic)
- **Week 2**: Follow up on all pending applications
- **Week 3**: Escalate non-responsive applications

---

## 📞 Contact Points

If applications don't respond within expected timeframe:
- Check spam folder
- Reply to confirmation email
- Contact via alternative channels (Twitter, support)

---

**Generated by:** Gemini Email Drafter
**Date:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

    with open(guide_path, 'w') as f:
        f.write(content)

    print(f"\n📋 Submission guide created: {guide_path}")


def integrate_with_claude_tasks():
    """
    Integration point for Claude Code task system.

    When called by Claude agent, creates tasks in shared TaskList.
    """
    # This would integrate with Claude Code's TaskCreate tool
    # For now, just print task definitions
    tasks = create_drafting_tasks()

    print("\n🤖 Claude Code Task Integration\n")
    print("To integrate with Claude Code tasks, use:")
    print()
    print("```python")
    print("from claude_code_tasks import TaskCreate")
    print()
    for task in tasks:
        print(f"TaskCreate(")
        print(f"    subject='{task['subject']}',")
        print(f"    description='''{task['description']}''',")
        print(f"    activeForm='{task['activeForm']}'")
        print(f")")
        print()
    print("```")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Orchestrate email drafting workflow')
    parser.add_argument(
        '--mode',
        choices=['draft', 'tasks', 'both'],
        default='draft',
        help='Workflow mode: draft emails, create tasks, or both'
    )
    parser.add_argument(
        '--output-dir',
        default='drafts',
        help='Output directory for drafts'
    )

    args = parser.parse_args()

    # Ensure output directory exists
    Path(args.output_dir).mkdir(exist_ok=True)

    if args.mode in ['draft', 'both']:
        results = draft_all_emails(output_dir=args.output_dir)

        # Print summary
        success_count = sum(1 for v in results.values() if v)
        print(f"\n{'='*70}")
        print(f"✅ Email drafting complete!")
        print(f"{'='*70}")
        print(f"  • Drafted: {success_count}/{len(results)} emails")
        print(f"  • Location: {args.output_dir}/")
        print(f"  • Tracker: docs/STARTUP_CREDITS_TRACKER.md")
        print(f"  • Guide: {args.output_dir}/SUBMISSION_GUIDE.md")
        print(f"{'='*70}\n")

    if args.mode in ['tasks', 'both']:
        integrate_with_claude_tasks()

    sys.exit(0)
