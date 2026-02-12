#!/usr/bin/env python3
"""
Batch Group Provisioning Script

Provisions multiple Google Workspace groups from configuration file.
"""

import sys
from google_workspace_groups import GoogleWorkspaceGroupManager
from google_workspace_config import (
    SERVICE_ACCOUNT_FILE,
    ADMIN_USER_EMAIL,
    SECURITY_PRESETS,
    GROUPS_TO_CREATE
)


def provision_groups():
    """Provision all groups defined in configuration."""
    manager = GoogleWorkspaceGroupManager(SERVICE_ACCOUNT_FILE, ADMIN_USER_EMAIL)

    total = len(GROUPS_TO_CREATE)
    succeeded = 0
    failed = 0

    print(f"\n{'='*60}")
    print(f"Provisioning {total} Google Workspace groups")
    print(f"{'='*60}\n")

    for idx, group_def in enumerate(GROUPS_TO_CREATE, 1):
        email = group_def['email']
        name = group_def['name']
        description = group_def.get('description', '')
        members = group_def.get('members', [])
        preset = group_def.get('security_preset', 'internal_moderate')

        print(f"\n[{idx}/{total}] Provisioning: {email}")
        print(f"  Name: {name}")
        print(f"  Security: {preset}")
        print(f"  Members: {len(members)}")

        # Get security settings from preset
        custom_settings = SECURITY_PRESETS.get(preset)
        if not custom_settings:
            print(f"  ⚠️  Warning: Unknown preset '{preset}', using defaults")
            custom_settings = None

        # Create and configure
        success = manager.create_and_configure_group(
            email=email,
            name=name,
            description=description,
            members=members,
            custom_settings=custom_settings
        )

        if success:
            succeeded += 1
            print(f"  ✓ Success")
        else:
            failed += 1
            print(f"  ✗ Failed")

    print(f"\n{'='*60}")
    print(f"Provisioning complete:")
    print(f"  ✓ Succeeded: {succeeded}")
    print(f"  ✗ Failed: {failed}")
    print(f"{'='*60}\n")

    return failed == 0


if __name__ == '__main__':
    try:
        success = provision_groups()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
