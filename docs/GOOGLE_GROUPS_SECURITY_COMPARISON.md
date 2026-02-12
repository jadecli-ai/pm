# Google Workspace Groups - Security Comparison

## ⚠️ The Problem: Unsafe API Defaults

When you create a Google Workspace group via the Directory API, it uses **insecure defaults** that expose your organization to risks.

---

## 📊 Complete Settings Comparison

| Setting | API Default | Our Default | Impact |
|---------|-------------|-------------|---------|
| **whoCanPostMessage** | `ANYONE_CAN_POST` ⚠️ | `ALL_IN_DOMAIN_CAN_POST` | **Critical**: Anyone on the internet can send emails to your group! |
| **whoCanJoin** | `ALL_IN_DOMAIN_CAN_JOIN` | `INVITED_CAN_JOIN` | **High**: Any employee can join without approval |
| **whoCanViewMembership** | `ALL_IN_DOMAIN_CAN_VIEW` | `ALL_MANAGERS_CAN_VIEW` | **Medium**: Member list visible to all employees |
| **whoCanViewGroup** | `ALL_IN_DOMAIN_CAN_VIEW` | `ALL_MEMBERS_CAN_VIEW` | **Medium**: Group details visible to all employees |
| **allowExternalMembers** | `true` ⚠️ | `false` | **High**: External emails can be added as members |
| **allowWebPosting** | `true` | `true` | **Info**: Web interface posting allowed |
| **messageModerationLevel** | `MODERATE_NONE` | `MODERATE_NEW_MEMBERS` | **Medium**: No spam/abuse protection |
| **spamModerationLevel** | `MODERATE` | `MODERATE` | **Info**: Google's spam filtering (same) |
| **whoCanContactOwner** | `ANYONE_CAN_CONTACT` ⚠️ | `ALL_MANAGERS_CAN_CONTACT` | **Medium**: Anyone can email group owners |

---

## 🚨 Risk Scenarios (API Defaults)

### Scenario 1: Spam/Phishing Attack
**API Default**: `whoCanPostMessage = ANYONE_CAN_POST`

```
❌ Attacker on the internet → Sends email to hr@yourcompany.com
✓ Email appears to come from your official HR group
✓ All employees receive phishing email
✓ Email looks legitimate (from your domain group)
```

**Our Fix**: `whoCanPostMessage = ALL_IN_DOMAIN_CAN_POST`
- Only domain users can post
- External emails are rejected

### Scenario 2: Data Leakage
**API Default**: `whoCanViewMembership = ALL_IN_DOMAIN_CAN_VIEW`

```
❌ Any employee → Views leadership@company.com members
✓ Sees complete executive roster
✓ Can identify decision makers
✓ Potential social engineering targets
```

**Our Fix**: `whoCanViewMembership = ALL_MANAGERS_CAN_VIEW`
- Only group managers see full member list
- Protects sensitive group membership

### Scenario 3: Unauthorized Access
**API Default**: `whoCanJoin = ALL_IN_DOMAIN_CAN_JOIN`

```
❌ Disgruntled employee → Joins executives@company.com
✓ Sees all executive communications
✓ Accesses confidential strategy discussions
✓ No approval required
```

**Our Fix**: `whoCanJoin = INVITED_CAN_JOIN`
- Managers must explicitly invite members
- No self-service joining

### Scenario 4: External Infiltration
**API Default**: `allowExternalMembers = true`

```
❌ Compromised account → Adds external@attacker.com
✓ External attacker joins internal group
✓ Receives all group communications
✓ Can post to group (if posting allowed)
```

**Our Fix**: `allowExternalMembers = false`
- Only domain accounts allowed
- External addresses automatically rejected

---

## ✅ Our Security Defaults

### Default Settings (Applied Automatically)
```python
{
    "whoCanPostMessage": "ALL_IN_DOMAIN_CAN_POST",          # Domain only
    "whoCanJoin": "INVITED_CAN_JOIN",                       # Invitation required
    "whoCanViewMembership": "ALL_MANAGERS_CAN_VIEW",        # Managers only
    "whoCanViewGroup": "ALL_MEMBERS_CAN_VIEW",              # Members only
    "allowExternalMembers": "false",                        # Internal only
    "allowWebPosting": "true",                              # Web UI allowed
    "messageModerationLevel": "MODERATE_NEW_MEMBERS",       # First post moderated
    "spamModerationLevel": "MODERATE",                      # Google spam filter
    "whoCanContactOwner": "ALL_MANAGERS_CAN_CONTACT",       # Managers only
}
```

---

## 🔒 Security Preset Comparison

### 1. internal_strict (Leadership, HR, Finance)
```python
{
    "whoCanPostMessage": "ALL_MEMBERS_CAN_POST",            # Members only
    "whoCanJoin": "INVITED_CAN_JOIN",                       # Invitation required
    "whoCanViewMembership": "ALL_MANAGERS_CAN_VIEW",        # Managers only
    "whoCanViewGroup": "ALL_MEMBERS_CAN_VIEW",              # Members only
    "allowExternalMembers": "false",                        # No external
    "messageModerationLevel": "MODERATE_ALL_MESSAGES",      # All posts moderated
}
```
**Use for**: Confidential groups (executives, HR, finance, legal)

### 2. internal_moderate (Default - Teams, Departments)
```python
{
    "whoCanPostMessage": "ALL_IN_DOMAIN_CAN_POST",          # Domain can post
    "whoCanJoin": "INVITED_CAN_JOIN",                       # Invitation required
    "whoCanViewMembership": "ALL_MEMBERS_CAN_VIEW",         # Members see list
    "whoCanViewGroup": "ALL_MEMBERS_CAN_VIEW",              # Members only
    "allowExternalMembers": "false",                        # No external
    "messageModerationLevel": "MODERATE_NEW_MEMBERS",       # First post moderated
}
```
**Use for**: Regular teams, departments, project groups

### 3. internal_open (Announcements, Company-Wide)
```python
{
    "whoCanPostMessage": "ALL_IN_DOMAIN_CAN_POST",          # Domain can post
    "whoCanJoin": "ALL_IN_DOMAIN_CAN_JOIN",                 # Domain can join
    "whoCanViewMembership": "ALL_IN_DOMAIN_CAN_VIEW",       # Domain sees members
    "whoCanViewGroup": "ALL_IN_DOMAIN_CAN_VIEW",            # Domain sees group
    "allowExternalMembers": "false",                        # No external
    "messageModerationLevel": "MODERATE_NONE",              # No moderation
}
```
**Use for**: Company announcements, public internal lists

### 4. external_collaboration (Partners, Vendors)
```python
{
    "whoCanPostMessage": "ALL_MEMBERS_CAN_POST",            # Members only
    "whoCanJoin": "INVITED_CAN_JOIN",                       # Invitation required
    "whoCanViewMembership": "ALL_MEMBERS_CAN_VIEW",         # Members see list
    "whoCanViewGroup": "ALL_MEMBERS_CAN_VIEW",              # Members only
    "allowExternalMembers": "true",                         # External allowed ⚠️
    "messageModerationLevel": "MODERATE_NEW_MEMBERS",       # First post moderated
}
```
**Use for**: Partner collaboration, vendor communication (carefully!)

---

## 📋 Option Reference

### whoCanPostMessage
| Option | Meaning |
|--------|---------|
| `ANYONE_CAN_POST` ⚠️ | **Anyone on the internet** can post |
| `ALL_IN_DOMAIN_CAN_POST` ✓ | Any employee can post |
| `ALL_MEMBERS_CAN_POST` ✓✓ | Only group members can post |
| `ALL_MANAGERS_CAN_POST` ✓✓✓ | Only managers can post |
| `ALL_OWNERS_CAN_POST` ✓✓✓✓ | Only owners can post (read-only for others) |

### whoCanJoin
| Option | Meaning |
|--------|---------|
| `ANYONE_CAN_JOIN` ⚠️ | **Anyone on the internet** can join |
| `ALL_IN_DOMAIN_CAN_JOIN` | Any employee can self-join |
| `INVITED_CAN_JOIN` ✓ | Invitation required |
| `CAN_REQUEST_TO_JOIN` | Users can request, managers approve |

### whoCanViewMembership
| Option | Meaning |
|--------|---------|
| `ALL_IN_DOMAIN_CAN_VIEW` | All employees see member list |
| `ALL_MEMBERS_CAN_VIEW` ✓ | Only members see full list |
| `ALL_MANAGERS_CAN_VIEW` ✓✓ | Only managers see full list |
| `ALL_OWNERS_CAN_VIEW` ✓✓✓ | Only owners see full list |

### messageModerationLevel
| Option | Meaning |
|--------|---------|
| `MODERATE_NONE` | No moderation |
| `MODERATE_NEW_MEMBERS` ✓ | First post from new members moderated |
| `MODERATE_ALL_MESSAGES` ✓✓ | All messages moderated |
| `MODERATE_NON_MEMBERS` | Messages from non-members moderated |

---

## 🎯 Quick Decision Guide

**Q: Who should see this group's emails?**
- Everyone in company → `internal_open`
- Only specific team → `internal_moderate`
- Highly confidential → `internal_strict`
- Includes external partners → `external_collaboration`

**Q: Who should be able to post?**
- Anyone in company → `ALL_IN_DOMAIN_CAN_POST`
- Only team members → `ALL_MEMBERS_CAN_POST`
- Only leadership → `ALL_OWNERS_CAN_POST`

**Q: Who should join automatically?**
- Open to all employees → `ALL_IN_DOMAIN_CAN_JOIN`
- Invitation required → `INVITED_CAN_JOIN` ✓ (recommended)

**Q: Do you need external members?**
- Yes, for partners → `allowExternalMembers: true` (use `external_collaboration` preset)
- No, internal only → `allowExternalMembers: false` ✓ (default)

---

## ⚡ Quick Fix Examples

### Fix Unsafe API Default
```python
# ✗ UNSAFE - Uses API defaults
from googleapiclient.discovery import build
service = build('admin', 'directory_v1', credentials=creds)
service.groups().insert(body={'email': 'team@domain.com', 'name': 'Team'}).execute()
# Result: ANYONE_CAN_POST ⚠️

# ✓ SAFE - Use our toolkit
from google_workspace_groups import GoogleWorkspaceGroupManager
manager = GoogleWorkspaceGroupManager(sa_file, admin_email)
manager.create_and_configure_group('team@domain.com', 'Team')
# Result: ALL_IN_DOMAIN_CAN_POST ✓
```

### Verify Settings
```python
settings = manager.get_group_settings('team@domain.com')
print(settings['whoCanPostMessage'])
# Should be: "ALL_IN_DOMAIN_CAN_POST" (not "ANYONE_CAN_POST")
```

---

## 📖 References

- [Groups Settings API](https://developers.google.com/admin-sdk/groups-settings/v1/reference/groups)
- [Security Best Practices](https://support.google.com/a/answer/167430)
- [Group Access Levels](https://support.google.com/a/answer/167096)

---

**Last Updated**: 2026-02-12
**Version**: 1.0.0
