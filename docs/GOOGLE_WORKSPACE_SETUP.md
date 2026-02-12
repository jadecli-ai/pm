# Google Workspace Group Management - Setup Guide

Complete guide for programmatic Google Workspace group management with proper security defaults.

## 🎯 Problem Statement

**API-created groups are INSECURE by default:**
- Default: "Anyone on the web" can post messages
- Default: All domain users can join without invitation
- Default: Member list is publicly visible

**This guide provides the complete solution.**

---

## 📋 Prerequisites

### 1. GCP Project Setup

Create or select a GCP project:
```bash
gcloud projects create jadecli-workspace --name="Workspace Automation"
gcloud config set project jadecli-workspace
```

### 2. Enable Required APIs

```bash
# Enable APIs
gcloud services enable admin.googleapis.com
gcloud services enable groupssettings.googleapis.com
gcloud services enable cloudidentity.googleapis.com
```

Or via Console:
1. Go to [API Library](https://console.cloud.google.com/apis/library)
2. Enable:
   - Admin SDK API
   - Groups Settings API
   - Cloud Identity API (optional)

### 3. Create Service Account

```bash
# Create service account
gcloud iam service-accounts create workspace-automation \
    --display-name="Workspace Group Automation"

# Get service account email
SA_EMAIL=$(gcloud iam service-accounts list \
    --filter="name:workspace-automation" \
    --format="value(email)")

echo "Service Account: $SA_EMAIL"

# Create and download key
gcloud iam service-accounts keys create ~/workspace-sa-key.json \
    --iam-account=$SA_EMAIL
```

**Save the output email and key file path.**

### 4. Enable Domain-Wide Delegation

#### In GCP Console:
1. Go to [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Click your service account
3. Click "Show Domain-Wide Delegation"
4. Click "Enable Domain-Wide Delegation"
5. Save the **Client ID** (numeric ID)

#### In Google Workspace Admin Console:
1. Go to [Admin Console](https://admin.google.com)
2. Navigate: Security → Access and data control → API controls
3. Click "Manage Domain-Wide Delegation"
4. Click "Add new"
5. Enter:
   - **Client ID**: From step above
   - **OAuth Scopes**:
     ```
     https://www.googleapis.com/auth/admin.directory.group,
     https://www.googleapis.com/auth/apps.groups.settings
     ```
6. Click "Authorize"

---

## 🚀 Installation

### 1. Install Dependencies

```bash
cd /home/org-jadecli/projects/pm/scripts
pip install -r requirements-google.txt
```

### 2. Configure Credentials

```bash
# Copy example config
cp google_workspace_config.example.py google_workspace_config.py

# Edit with your values
nano google_workspace_config.py
```

Update these values:
```python
SERVICE_ACCOUNT_FILE = '/home/org-jadecli/workspace-sa-key.json'
ADMIN_USER_EMAIL = 'admin@yourdomain.com'  # Your admin email
WORKSPACE_DOMAIN = 'yourdomain.com'
```

### 3. Add to .gitignore

```bash
echo "google_workspace_config.py" >> .gitignore
echo "*-sa-key.json" >> .gitignore
```

---

## 💻 Usage

### Method 1: Single Group (Programmatic)

```python
from google_workspace_groups import GoogleWorkspaceGroupManager

# Initialize
manager = GoogleWorkspaceGroupManager(
    service_account_file='/path/to/key.json',
    admin_user_email='admin@yourdomain.com'
)

# Create and configure (all-in-one)
manager.create_and_configure_group(
    email='team@yourdomain.com',
    name='Team Alpha',
    description='Project team',
    members=[
        {'email': 'user1@yourdomain.com', 'role': 'MEMBER'},
        {'email': 'manager@yourdomain.com', 'role': 'OWNER'},
    ]
)
```

### Method 2: Batch Provisioning

Edit `google_workspace_config.py`:
```python
GROUPS_TO_CREATE = [
    {
        'email': 'engineering@yourdomain.com',
        'name': 'Engineering',
        'description': 'All engineers',
        'security_preset': 'internal_moderate',
        'members': [
            {'email': 'eng1@yourdomain.com', 'role': 'MEMBER'},
            {'email': 'cto@yourdomain.com', 'role': 'OWNER'},
        ]
    },
    # Add more groups...
]
```

Run provisioning:
```bash
python provision_groups.py
```

### Method 3: Step-by-Step (Manual Control)

```python
from google_workspace_groups import GoogleWorkspaceGroupManager

manager = GoogleWorkspaceGroupManager(
    service_account_file='/path/to/key.json',
    admin_user_email='admin@yourdomain.com'
)

# Step 1: Create group
group_id = manager.create_group(
    email='project@yourdomain.com',
    name='Project Team',
    description='Main project group'
)

# Step 2: Secure settings (CRITICAL!)
manager.secure_group_settings('project@yourdomain.com')

# Step 3: Add members
manager.add_member('project@yourdomain.com', 'user@yourdomain.com', 'MEMBER')
manager.add_member('project@yourdomain.com', 'owner@yourdomain.com', 'OWNER')
```

---

## 🔒 Security Presets

### internal_strict
**Use for**: Leadership, HR, Finance
- Only members can post
- Invitation required to join
- Only managers see member list
- All messages moderated
- No external members

### internal_moderate (Default)
**Use for**: Teams, departments, projects
- Domain users can post
- Invitation required to join
- Members see member list
- New members moderated
- No external members

### internal_open
**Use for**: Announcements, company-wide
- Domain users can post
- Domain users can join
- Domain can view members
- No moderation
- No external members

### external_collaboration
**Use for**: Partner collaboration, vendors
- Members can post
- Invitation required to join
- Members see member list
- New members moderated
- **External members allowed**

---

## 🛡️ Default Security Settings Applied

When you call `secure_group_settings()`, these defaults are applied:

| Setting | API Default (UNSAFE) | Our Default (SAFE) |
|---------|---------------------|-------------------|
| `whoCanPostMessage` | `ANYONE_CAN_POST` ⚠️ | `ALL_IN_DOMAIN_CAN_POST` ✓ |
| `whoCanJoin` | `ALL_IN_DOMAIN_CAN_JOIN` | `INVITED_CAN_JOIN` ✓ |
| `whoCanViewMembership` | `ALL_IN_DOMAIN_CAN_VIEW` | `ALL_MANAGERS_CAN_VIEW` ✓ |
| `allowExternalMembers` | `true` ⚠️ | `false` ✓ |
| `messageModerationLevel` | `MODERATE_NONE` | `MODERATE_NEW_MEMBERS` ✓ |

**Always call `secure_group_settings()` immediately after `create_group()`.**

---

## 📝 Complete Example: Multi-Team Setup

```python
from google_workspace_groups import GoogleWorkspaceGroupManager
from google_workspace_config import SERVICE_ACCOUNT_FILE, ADMIN_USER_EMAIL

manager = GoogleWorkspaceGroupManager(SERVICE_ACCOUNT_FILE, ADMIN_USER_EMAIL)

# Engineering team
manager.create_and_configure_group(
    email='engineering@company.com',
    name='Engineering',
    members=[
        {'email': 'cto@company.com', 'role': 'OWNER'},
        {'email': 'eng1@company.com', 'role': 'MEMBER'},
        {'email': 'eng2@company.com', 'role': 'MEMBER'},
    ],
    custom_settings={'whoCanPostMessage': 'ALL_MEMBERS_CAN_POST'}
)

# Product team
manager.create_and_configure_group(
    email='product@company.com',
    name='Product',
    members=[
        {'email': 'vp-product@company.com', 'role': 'OWNER'},
        {'email': 'pm1@company.com', 'role': 'MANAGER'},
        {'email': 'pm2@company.com', 'role': 'MEMBER'},
    ]
)

# All-company announcements
manager.create_and_configure_group(
    email='announce@company.com',
    name='Announcements',
    description='Company-wide announcements',
    custom_settings={
        'whoCanPostMessage': 'ALL_OWNERS_CAN_POST',
        'whoCanViewGroup': 'ALL_IN_DOMAIN_CAN_VIEW',
        'whoCanViewMembership': 'ALL_IN_DOMAIN_CAN_VIEW',
    }
)
```

---

## 🔍 Verification

### Check Group Settings
```python
settings = manager.get_group_settings('team@yourdomain.com')
print(f"Who can post: {settings['whoCanPostMessage']}")
print(f"Who can join: {settings['whoCanJoin']}")
print(f"External members: {settings['allowExternalMembers']}")
```

### List Members
```python
members = manager.list_members('team@yourdomain.com')
for member in members:
    print(f"{member['email']}: {member['role']}")
```

---

## ⚠️ Common Issues

### "Not Authorized to access this resource/api"
- **Cause**: Domain-Wide Delegation not configured
- **Fix**: Complete Step 4 in Prerequisites

### "Invalid scope"
- **Cause**: Scopes not authorized in Workspace Admin
- **Fix**: Add both scopes to Domain-Wide Delegation

### "Group already exists"
- **Cause**: Group email is taken
- **Fix**: Choose different email or delete existing group

### Settings not applying
- **Cause**: Calling `secure_group_settings()` too soon after creation
- **Fix**: Add 1-second delay between create and settings update

---

## 📚 API References

- [Admin SDK Directory API](https://developers.google.com/admin-sdk/directory/v1/guides/manage-groups)
- [Groups Settings API](https://developers.google.com/admin-sdk/groups-settings/v1/reference/groups)
- [Domain-Wide Delegation](https://developers.google.com/workspace/guides/create-credentials#optional_set_up_domain-wide_delegation_for_a_service_account)

---

## 🎯 Next Steps

1. **Test in non-production domain first**
2. **Create groups for your org structure**
3. **Automate from CSV/database**
4. **Schedule periodic member sync**
5. **Integrate with onboarding/offboarding**

---

## 📧 Support

For issues with this implementation:
- Check logs for detailed error messages
- Verify Domain-Wide Delegation scopes
- Ensure service account has necessary permissions
- Test with a simple group first

For Google Workspace API issues:
- [Workspace Admin Help](https://support.google.com/a)
- [API Support](https://developers.google.com/workspace/support)
