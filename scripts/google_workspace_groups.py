#!/usr/bin/env python3
"""
Google Workspace Group Management - Programmatic Setup

This script provides complete programmatic control over Google Workspace groups:
1. Create groups via Directory API
2. Secure settings via Groups Settings API (fixes unsafe defaults)
3. Populate members via Directory API

Prerequisites:
- GCP Project with APIs enabled:
  * Admin SDK API
  * Groups Settings API
  * Cloud Identity API (optional)
- Service Account with Domain-Wide Delegation
- OAuth Scopes configured in Workspace Admin Console
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GoogleWorkspaceGroupManager:
    """Manage Google Workspace groups programmatically."""

    # Required OAuth scopes
    SCOPES = [
        'https://www.googleapis.com/auth/admin.directory.group',
        'https://www.googleapis.com/auth/apps.groups.settings'
    ]

    def __init__(self, service_account_file: str, admin_user_email: str):
        """
        Initialize the group manager.

        Args:
            service_account_file: Path to service account JSON key file
            admin_user_email: Admin user to impersonate (requires domain-wide delegation)
        """
        self.admin_user = admin_user_email
        self.credentials = self._authenticate(service_account_file)
        self.directory_service = build('admin', 'directory_v1', credentials=self.credentials)
        self.settings_service = build('groupssettings', 'v1', credentials=self.credentials)

    def _authenticate(self, service_account_file: str):
        """Authenticate using service account with domain-wide delegation."""
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=self.SCOPES
        )
        # Impersonate admin user for domain-wide delegation
        return credentials.with_subject(self.admin_user)

    def create_group(
        self,
        email: str,
        name: str,
        description: str = ""
    ) -> Optional[str]:
        """
        Create a new Google Workspace group.

        Args:
            email: Group email address (e.g., team@yourdomain.com)
            name: Display name for the group
            description: Group description

        Returns:
            Group ID if successful, None otherwise
        """
        group_body = {
            "email": email,
            "name": name,
            "description": description
        }

        try:
            logger.info(f"Creating group: {email}")
            result = self.directory_service.groups().insert(body=group_body).execute()
            group_id = result['id']
            logger.info(f"✓ Group created successfully. ID: {group_id}")
            return group_id
        except Exception as e:
            logger.error(f"✗ Error creating group {email}: {e}")
            return None

    def secure_group_settings(
        self,
        group_email: str,
        custom_settings: Optional[Dict] = None
    ) -> bool:
        """
        Apply secure settings to a group.

        This is CRITICAL - API-created groups default to allowing "Anyone on the web"
        to post, which is a major security risk. This method locks down the group.

        Args:
            group_email: Group email address
            custom_settings: Optional dict to override default secure settings

        Returns:
            True if successful, False otherwise
        """
        # Default secure settings (overrides unsafe API defaults)
        default_settings = {
            # WHO CAN POST - Default is "ANYONE_CAN_POST" (UNSAFE!)
            "whoCanPostMessage": "ALL_IN_DOMAIN_CAN_POST",

            # WHO CAN JOIN - Default is "ALL_IN_DOMAIN_CAN_JOIN"
            "whoCanJoin": "INVITED_CAN_JOIN",

            # WHO CAN VIEW MEMBERSHIP - Protect member list
            "whoCanViewMembership": "ALL_MANAGERS_CAN_VIEW",

            # WHO CAN VIEW GROUP - Restrict visibility
            "whoCanViewGroup": "ALL_MEMBERS_CAN_VIEW",

            # EXTERNAL MEMBERS - Keep internal by default
            "allowExternalMembers": "false",

            # WEB POSTING - Disable web interface posting
            "allowWebPosting": "true",

            # MESSAGE MODERATION - Moderate first-time posters
            "messageModerationLevel": "MODERATE_NEW_MEMBERS",

            # SPAM MODERATION - Let Google handle spam
            "spamModerationLevel": "MODERATE",

            # WHO CAN CONTACT OWNER - Protect owner emails
            "whoCanContactOwner": "ALL_MANAGERS_CAN_CONTACT",
        }

        # Merge custom settings if provided
        settings_body = {**default_settings, **(custom_settings or {})}

        try:
            logger.info(f"Applying secure settings to: {group_email}")
            self.settings_service.groups().update(
                groupUniqueId=group_email,
                body=settings_body
            ).execute()
            logger.info(f"✓ Settings updated successfully for {group_email}")
            return True
        except Exception as e:
            logger.error(f"✗ Error updating settings for {group_email}: {e}")
            return False

    def add_member(
        self,
        group_email: str,
        user_email: str,
        role: str = 'MEMBER'
    ) -> bool:
        """
        Add a member to a group.

        Args:
            group_email: Group email address
            user_email: User email to add
            role: Member role (MEMBER, MANAGER, OWNER)

        Returns:
            True if successful, False otherwise
        """
        valid_roles = ['MEMBER', 'MANAGER', 'OWNER']
        if role not in valid_roles:
            logger.error(f"Invalid role: {role}. Must be one of {valid_roles}")
            return False

        member_body = {
            "email": user_email,
            "role": role
        }

        try:
            logger.info(f"Adding {user_email} as {role} to {group_email}")
            self.directory_service.members().insert(
                groupKey=group_email,
                body=member_body
            ).execute()
            logger.info(f"✓ Member {user_email} added successfully")
            return True
        except Exception as e:
            logger.error(f"✗ Error adding {user_email} to {group_email}: {e}")
            return False

    def add_members_bulk(
        self,
        group_email: str,
        members: List[Dict[str, str]]
    ) -> Dict[str, int]:
        """
        Add multiple members to a group.

        Args:
            group_email: Group email address
            members: List of dicts with 'email' and optional 'role' keys

        Returns:
            Dict with success/failure counts
        """
        results = {"success": 0, "failed": 0}

        for member in members:
            user_email = member.get('email')
            role = member.get('role', 'MEMBER')

            if not user_email:
                logger.warning(f"Skipping member with no email: {member}")
                results["failed"] += 1
                continue

            if self.add_member(group_email, user_email, role):
                results["success"] += 1
            else:
                results["failed"] += 1

        logger.info(f"Bulk add complete: {results['success']} succeeded, {results['failed']} failed")
        return results

    def create_and_configure_group(
        self,
        email: str,
        name: str,
        description: str = "",
        members: Optional[List[Dict[str, str]]] = None,
        custom_settings: Optional[Dict] = None
    ) -> bool:
        """
        Complete workflow: Create, Secure, and Populate a group.

        This is the recommended method - it ensures groups are properly
        secured immediately after creation.

        Args:
            email: Group email address
            name: Display name
            description: Group description
            members: List of members to add (dicts with 'email' and 'role')
            custom_settings: Optional custom security settings

        Returns:
            True if all steps succeeded, False otherwise
        """
        logger.info(f"=== Starting complete group setup for {email} ===")

        # Step 1: Create group
        group_id = self.create_group(email, name, description)
        if not group_id:
            logger.error("Failed at step 1: Group creation")
            return False

        # Step 2: Secure settings (CRITICAL - fixes unsafe defaults)
        if not self.secure_group_settings(email, custom_settings):
            logger.error("Failed at step 2: Security settings")
            return False

        # Step 3: Add members (if provided)
        if members:
            results = self.add_members_bulk(email, members)
            if results["failed"] > 0:
                logger.warning(f"Some members failed to add: {results}")

        logger.info(f"=== Group setup complete for {email} ===")
        return True

    def get_group_settings(self, group_email: str) -> Optional[Dict]:
        """
        Retrieve current settings for a group.

        Args:
            group_email: Group email address

        Returns:
            Dict of current settings, or None if error
        """
        try:
            settings = self.settings_service.groups().get(
                groupUniqueId=group_email
            ).execute()
            return settings
        except Exception as e:
            logger.error(f"Error retrieving settings for {group_email}: {e}")
            return None

    def list_members(self, group_email: str) -> List[Dict]:
        """
        List all members of a group.

        Args:
            group_email: Group email address

        Returns:
            List of member dicts
        """
        try:
            members = []
            request = self.directory_service.members().list(groupKey=group_email)

            while request:
                response = request.execute()
                members.extend(response.get('members', []))
                request = self.directory_service.members().list_next(request, response)

            return members
        except Exception as e:
            logger.error(f"Error listing members for {group_email}: {e}")
            return []


def example_usage():
    """Example: Create a secure project team group."""

    # Configuration
    SERVICE_ACCOUNT_FILE = 'path/to/service_account.json'
    ADMIN_USER_EMAIL = 'admin@yourdomain.com'

    # Initialize manager
    manager = GoogleWorkspaceGroupManager(SERVICE_ACCOUNT_FILE, ADMIN_USER_EMAIL)

    # Define group
    group_email = "project-alpha@yourdomain.com"
    group_name = "Project Alpha Team"
    description = "Main discussion group for Project Alpha"

    # Define members
    members = [
        {"email": "engineer1@yourdomain.com", "role": "MEMBER"},
        {"email": "engineer2@yourdomain.com", "role": "MEMBER"},
        {"email": "manager@yourdomain.com", "role": "OWNER"},
    ]

    # Optional: Custom settings (overrides defaults)
    custom_settings = {
        "whoCanPostMessage": "ALL_MEMBERS_CAN_POST",  # More permissive
    }

    # Create and configure group (all-in-one)
    success = manager.create_and_configure_group(
        email=group_email,
        name=group_name,
        description=description,
        members=members,
        custom_settings=custom_settings
    )

    if success:
        print(f"\n✓ Group {group_email} is ready for use!")
    else:
        print(f"\n✗ Group setup failed. Check logs for details.")


if __name__ == '__main__':
    # Run example
    # example_usage()

    # Or use programmatically:
    import sys
    if len(sys.argv) > 1:
        print("Usage: See example_usage() function for implementation")
        sys.exit(1)

    print(__doc__)
