"""
Google Workspace Configuration Template

1. Copy this file to google_workspace_config.py
2. Fill in your actual values
3. Add google_workspace_config.py to .gitignore
"""

# Service Account Configuration
SERVICE_ACCOUNT_FILE = '/path/to/service-account-key.json'

# Admin user for domain-wide delegation
ADMIN_USER_EMAIL = 'admin@yourdomain.com'

# Domain
WORKSPACE_DOMAIN = 'yourdomain.com'

# Group Security Presets
SECURITY_PRESETS = {
    # Maximum security - internal only, invitation required
    'internal_strict': {
        "whoCanPostMessage": "ALL_MEMBERS_CAN_POST",
        "whoCanJoin": "INVITED_CAN_JOIN",
        "whoCanViewMembership": "ALL_MANAGERS_CAN_VIEW",
        "whoCanViewGroup": "ALL_MEMBERS_CAN_VIEW",
        "allowExternalMembers": "false",
        "messageModerationLevel": "MODERATE_ALL_MESSAGES",
    },

    # Moderate security - domain can post, invitation required
    'internal_moderate': {
        "whoCanPostMessage": "ALL_IN_DOMAIN_CAN_POST",
        "whoCanJoin": "INVITED_CAN_JOIN",
        "whoCanViewMembership": "ALL_MEMBERS_CAN_VIEW",
        "whoCanViewGroup": "ALL_MEMBERS_CAN_VIEW",
        "allowExternalMembers": "false",
        "messageModerationLevel": "MODERATE_NEW_MEMBERS",
    },

    # Public within domain
    'internal_open': {
        "whoCanPostMessage": "ALL_IN_DOMAIN_CAN_POST",
        "whoCanJoin": "ALL_IN_DOMAIN_CAN_JOIN",
        "whoCanViewMembership": "ALL_IN_DOMAIN_CAN_VIEW",
        "whoCanViewGroup": "ALL_IN_DOMAIN_CAN_VIEW",
        "allowExternalMembers": "false",
        "messageModerationLevel": "MODERATE_NONE",
    },

    # External collaboration allowed
    'external_collaboration': {
        "whoCanPostMessage": "ALL_MEMBERS_CAN_POST",
        "whoCanJoin": "INVITED_CAN_JOIN",
        "whoCanViewMembership": "ALL_MEMBERS_CAN_VIEW",
        "whoCanViewGroup": "ALL_MEMBERS_CAN_VIEW",
        "allowExternalMembers": "true",
        "messageModerationLevel": "MODERATE_NEW_MEMBERS",
    },
}

# Example group definitions
GROUPS_TO_CREATE = [
    {
        'email': 'engineering@yourdomain.com',
        'name': 'Engineering Team',
        'description': 'All engineering staff',
        'security_preset': 'internal_moderate',
        'members': [
            {'email': 'engineer1@yourdomain.com', 'role': 'MEMBER'},
            {'email': 'cto@yourdomain.com', 'role': 'OWNER'},
        ]
    },
    {
        'email': 'leadership@yourdomain.com',
        'name': 'Leadership',
        'description': 'Executive leadership team',
        'security_preset': 'internal_strict',
        'members': [
            {'email': 'ceo@yourdomain.com', 'role': 'OWNER'},
            {'email': 'cto@yourdomain.com', 'role': 'MEMBER'},
        ]
    },
]
