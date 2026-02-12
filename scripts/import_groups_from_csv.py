#!/usr/bin/env python3
"""
Import Google Workspace groups from CSV file.

CSV Format:
    group_email,group_name,description,security_preset,member_email,member_role
    team@domain.com,Team Alpha,Project team,internal_moderate,user1@domain.com,MEMBER
    team@domain.com,Team Alpha,Project team,internal_moderate,owner@domain.com,OWNER
    dept@domain.com,Department,Department group,internal_strict,manager@domain.com,OWNER

Multiple rows with same group_email will add members to the same group.
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path
from google_workspace_groups import GoogleWorkspaceGroupManager
from google_workspace_config import (
    SERVICE_ACCOUNT_FILE,
    ADMIN_USER_EMAIL,
    SECURITY_PRESETS
)


def parse_csv(csv_file: str) -> dict:
    """
    Parse CSV file into group definitions.

    Returns:
        Dict mapping group_email -> {name, description, preset, members}
    """
    groups = defaultdict(lambda: {
        'name': '',
        'description': '',
        'security_preset': 'internal_moderate',
        'members': []
    })

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row['group_email'].strip()

            # Set group metadata (first row wins)
            if not groups[email]['name']:
                groups[email]['name'] = row['group_name'].strip()
                groups[email]['description'] = row.get('description', '').strip()
                groups[email]['security_preset'] = row.get('security_preset', 'internal_moderate').strip()

            # Add member
            member_email = row.get('member_email', '').strip()
            member_role = row.get('member_role', 'MEMBER').strip()

            if member_email:
                groups[email]['members'].append({
                    'email': member_email,
                    'role': member_role
                })

    return dict(groups)


def import_groups(csv_file: str, dry_run: bool = False):
    """
    Import groups from CSV file.

    Args:
        csv_file: Path to CSV file
        dry_run: If True, only print what would be done
    """
    # Parse CSV
    print(f"Parsing CSV: {csv_file}")
    groups = parse_csv(csv_file)

    print(f"\nFound {len(groups)} groups to create:")
    for email, data in groups.items():
        print(f"  - {email}: {data['name']} ({len(data['members'])} members)")

    if dry_run:
        print("\n[DRY RUN] Skipping actual creation. Use --execute to create.")
        return True

    # Initialize manager
    manager = GoogleWorkspaceGroupManager(SERVICE_ACCOUNT_FILE, ADMIN_USER_EMAIL)

    # Create groups
    total = len(groups)
    succeeded = 0
    failed = 0

    print(f"\n{'='*60}")
    print(f"Creating {total} groups...")
    print(f"{'='*60}\n")

    for idx, (email, data) in enumerate(groups.items(), 1):
        print(f"\n[{idx}/{total}] {email}")

        # Get security settings
        custom_settings = SECURITY_PRESETS.get(data['security_preset'])
        if not custom_settings:
            print(f"  ⚠️  Unknown preset: {data['security_preset']}")
            custom_settings = None

        # Create and configure
        success = manager.create_and_configure_group(
            email=email,
            name=data['name'],
            description=data['description'],
            members=data['members'],
            custom_settings=custom_settings
        )

        if success:
            succeeded += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"Import complete:")
    print(f"  ✓ Succeeded: {succeeded}")
    print(f"  ✗ Failed: {failed}")
    print(f"{'='*60}\n")

    return failed == 0


def create_example_csv(output_file: str = 'groups_example.csv'):
    """Create an example CSV file."""
    example_data = [
        ['group_email', 'group_name', 'description', 'security_preset', 'member_email', 'member_role'],
        ['engineering@company.com', 'Engineering', 'All engineers', 'internal_moderate', 'cto@company.com', 'OWNER'],
        ['engineering@company.com', 'Engineering', 'All engineers', 'internal_moderate', 'eng1@company.com', 'MEMBER'],
        ['engineering@company.com', 'Engineering', 'All engineers', 'internal_moderate', 'eng2@company.com', 'MEMBER'],
        ['product@company.com', 'Product', 'Product team', 'internal_moderate', 'vp-product@company.com', 'OWNER'],
        ['product@company.com', 'Product', 'Product team', 'internal_moderate', 'pm1@company.com', 'MANAGER'],
        ['leadership@company.com', 'Leadership', 'Exec team', 'internal_strict', 'ceo@company.com', 'OWNER'],
        ['leadership@company.com', 'Leadership', 'Exec team', 'internal_strict', 'cto@company.com', 'MEMBER'],
    ]

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(example_data)

    print(f"✓ Created example CSV: {output_file}")
    print("\nEdit this file with your groups, then run:")
    print(f"  python import_groups_from_csv.py {output_file} --execute")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Import Google Workspace groups from CSV')
    parser.add_argument('csv_file', nargs='?', help='CSV file to import')
    parser.add_argument('--execute', action='store_true', help='Execute import (default is dry-run)')
    parser.add_argument('--create-example', action='store_true', help='Create example CSV file')

    args = parser.parse_args()

    if args.create_example:
        create_example_csv()
        sys.exit(0)

    if not args.csv_file:
        print("Usage: python import_groups_from_csv.py <csv_file> [--execute]")
        print("   Or: python import_groups_from_csv.py --create-example")
        sys.exit(1)

    if not Path(args.csv_file).exists():
        print(f"Error: File not found: {args.csv_file}")
        sys.exit(1)

    try:
        success = import_groups(args.csv_file, dry_run=not args.execute)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
