# PM System Scripts

Automation scripts for the jadecli PM system.

## 📁 Directory Structure

```
scripts/
├── google_workspace_groups.py          # Core library for group management
├── google_workspace_config.example.py  # Configuration template
├── provision_groups.py                 # Batch provisioning
├── import_groups_from_csv.py          # CSV import tool
├── requirements-google.txt             # Python dependencies
├── QUICKSTART_GOOGLE_GROUPS.md        # 5-minute quick start
└── README.md                          # This file
```

## 🚀 Quick Start

### Google Workspace Groups

**Complete programmatic control over Google Workspace groups with proper security defaults.**

#### Problem Solved
API-created groups default to "Anyone on the web can post" - a major security risk. This toolkit ensures groups are secure by default.

#### 5-Minute Setup
```bash
# 1. Install
pip install -r requirements-google.txt

# 2. Configure
cp google_workspace_config.example.py google_workspace_config.py
# Edit with your service account path and admin email

# 3. Create your first group
python3 << 'EOF'
from google_workspace_groups import GoogleWorkspaceGroupManager

manager = GoogleWorkspaceGroupManager(
    service_account_file='/path/to/sa-key.json',
    admin_user_email='admin@yourdomain.com'
)

manager.create_and_configure_group(
    email='test@yourdomain.com',
    name='Test Group',
    members=[{'email': 'you@yourdomain.com', 'role': 'OWNER'}]
)
EOF
```

#### Bulk Import from CSV
```bash
# Create example CSV
python import_groups_from_csv.py --create-example

# Edit groups_example.csv with your data

# Dry run (preview)
python import_groups_from_csv.py groups_example.csv

# Execute
python import_groups_from_csv.py groups_example.csv --execute
```

## 📚 Documentation

- **Quick Start**: `QUICKSTART_GOOGLE_GROUPS.md` - Get running in 5 minutes
- **Full Setup**: `../docs/GOOGLE_WORKSPACE_SETUP.md` - Complete GCP/Workspace configuration
- **API Docs**: Inline docstrings in `google_workspace_groups.py`

## 🔒 Security

### Default Security Settings

All groups created via this toolkit get secure defaults:

| Setting | API Default (UNSAFE) | Our Default (SAFE) |
|---------|---------------------|-------------------|
| Who can post | Anyone on web ⚠️ | Domain users only ✓ |
| Who can join | All domain users | Invitation required ✓ |
| Member visibility | All domain | Managers only ✓ |
| External members | Allowed ⚠️ | Blocked ✓ |

### Security Presets

Choose from 4 presets in `google_workspace_config.py`:

1. **internal_strict** - Leadership, HR, Finance
   - Only members can post
   - Invitation required
   - All messages moderated

2. **internal_moderate** (Default) - Teams, departments
   - Domain can post
   - Invitation required
   - New members moderated

3. **internal_open** - Announcements, company-wide
   - Domain can post
   - Domain can join
   - No moderation

4. **external_collaboration** - Partners, vendors
   - External members allowed
   - All messages moderated
   - Invitation required

## 🎯 Common Use Cases

### Engineering Team
```python
manager.create_and_configure_group(
    email='engineering@company.com',
    name='Engineering',
    members=[
        {'email': 'cto@company.com', 'role': 'OWNER'},
        {'email': 'eng1@company.com', 'role': 'MEMBER'},
    ]
)
```

### Announcements (Read-Only)
```python
manager.create_and_configure_group(
    email='announce@company.com',
    name='Announcements',
    custom_settings={
        'whoCanPostMessage': 'ALL_OWNERS_CAN_POST',
        'whoCanViewGroup': 'ALL_IN_DOMAIN_CAN_VIEW',
    }
)
```

### Partner Collaboration
```python
manager.create_and_configure_group(
    email='partners@company.com',
    name='Partners',
    custom_settings={
        'allowExternalMembers': 'true',
        'messageModerationLevel': 'MODERATE_ALL_MESSAGES',
    }
)
```

## 🛠️ Prerequisites

### GCP Setup
1. Create GCP project
2. Enable APIs:
   - Admin SDK API
   - Groups Settings API
3. Create service account
4. Enable Domain-Wide Delegation

### Workspace Setup
1. Navigate to Admin Console → Security → API Controls
2. Manage Domain-Wide Delegation
3. Add Client ID with scopes:
   ```
   https://www.googleapis.com/auth/admin.directory.group,
   https://www.googleapis.com/auth/apps.groups.settings
   ```

See `../docs/GOOGLE_WORKSPACE_SETUP.md` for detailed instructions.

## 📊 CSV Import Format

```csv
group_email,group_name,description,security_preset,member_email,member_role
team@company.com,Team Alpha,Project team,internal_moderate,owner@company.com,OWNER
team@company.com,Team Alpha,Project team,internal_moderate,member@company.com,MEMBER
dept@company.com,Department,Dept group,internal_strict,manager@company.com,MANAGER
```

Multiple rows with same `group_email` add members to the same group.

## ⚠️ Common Issues

### "Not Authorized to access this resource/api"
- **Fix**: Complete Domain-Wide Delegation in Workspace Admin Console

### "Invalid scope"
- **Fix**: Add both required scopes to Domain-Wide Delegation

### Settings not applying
- **Fix**: Ensure you call `secure_group_settings()` after `create_group()`
- **Better**: Use `create_and_configure_group()` instead

### Group already exists
- **Fix**: Choose different email or delete existing group first

## 🔄 Workflow

```
┌────────────────────────────────────────────────────────────┐
│                     Create Group                           │
│              (Directory API)                               │
└─────────────────────┬──────────────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────────────────────┐
│              Secure Settings ⚠️ CRITICAL                    │
│           (Groups Settings API)                            │
│  Fixes: "Anyone on web can post" → "Domain only"          │
└─────────────────────┬──────────────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────────────────────┐
│                  Add Members                               │
│              (Directory API)                               │
└────────────────────────────────────────────────────────────┘
```

## 📝 Examples

See `QUICKSTART_GOOGLE_GROUPS.md` and `../docs/GOOGLE_WORKSPACE_SETUP.md` for complete examples.

## 🤝 Contributing

When adding new scripts:
1. Add inline docstrings
2. Update this README
3. Add example usage
4. Follow PM system conventions (see `../pm/CLAUDE.md`)

## 📄 License

Part of the jadecli PM system. Internal use only.
