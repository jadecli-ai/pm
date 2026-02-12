# Google Workspace Groups - Quick Start

## 🚀 5-Minute Setup

### 1. Install Dependencies
```bash
pip install -r requirements-google.txt
```

### 2. Configure
```bash
cp google_workspace_config.example.py google_workspace_config.py
nano google_workspace_config.py  # Edit with your values
```

### 3. Test with One Group
```python
from google_workspace_groups import GoogleWorkspaceGroupManager

manager = GoogleWorkspaceGroupManager(
    service_account_file='/path/to/key.json',
    admin_user_email='admin@yourdomain.com'
)

# Create a secure group (all-in-one)
manager.create_and_configure_group(
    email='test-team@yourdomain.com',
    name='Test Team',
    description='Testing group automation',
    members=[
        {'email': 'your-email@yourdomain.com', 'role': 'OWNER'}
    ]
)
```

---

## 📁 CSV Import (Bulk)

### Create Example CSV
```bash
python import_groups_from_csv.py --create-example
```

### Edit CSV
```csv
group_email,group_name,description,security_preset,member_email,member_role
eng@company.com,Engineering,Engineers,internal_moderate,cto@company.com,OWNER
eng@company.com,Engineering,Engineers,internal_moderate,eng1@company.com,MEMBER
```

### Dry Run (Preview)
```bash
python import_groups_from_csv.py groups.csv
```

### Execute
```bash
python import_groups_from_csv.py groups.csv --execute
```

---

## 🔒 Security Presets

Choose from `google_workspace_config.py`:
- `internal_strict` - Leadership, HR, Finance
- `internal_moderate` - Teams, departments (default)
- `internal_open` - Announcements, company-wide
- `external_collaboration` - Partners, vendors

---

## ✅ Verification

```python
# Check settings
settings = manager.get_group_settings('team@yourdomain.com')
print(settings['whoCanPostMessage'])  # Should NOT be "ANYONE_CAN_POST"

# List members
members = manager.list_members('team@yourdomain.com')
for m in members:
    print(f"{m['email']}: {m['role']}")
```

---

## 🎯 Common Workflows

### Engineering Team
```python
manager.create_and_configure_group(
    email='engineering@company.com',
    name='Engineering',
    members=[
        {'email': 'cto@company.com', 'role': 'OWNER'},
        {'email': 'eng1@company.com', 'role': 'MEMBER'},
    ],
    custom_settings={'whoCanPostMessage': 'ALL_MEMBERS_CAN_POST'}
)
```

### Announcements (Read-Only for Most)
```python
manager.create_and_configure_group(
    email='announce@company.com',
    name='Announcements',
    custom_settings={
        'whoCanPostMessage': 'ALL_OWNERS_CAN_POST',  # Only owners post
        'whoCanViewGroup': 'ALL_IN_DOMAIN_CAN_VIEW',
    }
)
```

### External Collaboration
```python
manager.create_and_configure_group(
    email='partners@company.com',
    name='Partner Collaboration',
    custom_settings={
        'allowExternalMembers': 'true',
        'messageModerationLevel': 'MODERATE_ALL_MESSAGES',
    }
)
```

---

## ⚠️ Critical: Security

**ALWAYS call `secure_group_settings()` after `create_group()`:**

```python
# ✗ UNSAFE - Uses insecure defaults!
group_id = manager.create_group('team@domain.com', 'Team')

# ✓ SAFE - Use all-in-one method
manager.create_and_configure_group('team@domain.com', 'Team')

# ✓ SAFE - Manual steps
group_id = manager.create_group('team@domain.com', 'Team')
manager.secure_group_settings('team@domain.com')  # MUST do this!
```

---

## 📖 Full Documentation

See `docs/GOOGLE_WORKSPACE_SETUP.md` for:
- Complete GCP setup instructions
- Domain-Wide Delegation configuration
- API scope details
- Troubleshooting guide
- API references
