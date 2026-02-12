# Claude Code Task Alignment Test

> Integration test verifying entity ↔ Claude Code task conversion

## Overview

This test validates that our PM entities (especially Tasks) correctly align with Claude Code's built-in task system defined by:
- `TaskCreate` - Create new task
- `TaskUpdate` - Update task status/fields
- `TaskGet` - Retrieve task details
- `TaskList` - List all tasks

## Field Mapping

### TaskCreate Parameters

| TaskCreate | Entity Task Field | Notes |
|------------|-------------------|-------|
| `subject` | `subject` | Direct mapping, imperative form |
| `description` | Body content | Full markdown description |
| `activeForm` | `activeForm` | Present continuous form |

### TaskUpdate Parameters

| TaskUpdate | Entity Task Field | Notes |
|------------|-------------------|-------|
| `taskId` | (Claude internal) | Not in entity |
| `status` | `status` | pending/in_progress/completed |
| `subject` | `subject` | Can be updated |
| `description` | Body content | Can be updated |
| `activeForm` | `activeForm` | Can be updated |
| `owner` | `owner` | Agent assignment |
| `addBlocks` | `blocks` | Task IDs this blocks |
| `addBlockedBy` | `blockedBy` | Task IDs blocking this |

## Test Cases

### TC-001: Create Task from Entity

**Given** a Task entity file:
```yaml
---
id: "TASK-004"
subject: "Implement JWT token generation"
activeForm: "Implementing JWT token generation"
status: pending
---

# Implement JWT Token Generation
...description...
```

**When** agent creates Claude Code task:
```javascript
TaskCreate({
  subject: "Implement JWT token generation",
  description: "# Implement JWT Token Generation\n...",
  activeForm: "Implementing JWT token generation"
})
```

**Then** task is created with matching fields.

---

### TC-002: Update Task Status

**Given** entity status change:
```yaml
status: pending -> in_progress
version: "1.0.0" -> "1.0.1"
```

**When** agent updates Claude Code task:
```javascript
TaskUpdate({
  taskId: "<claude-task-id>",
  status: "in_progress"
})
```

**Then** status synced, entity version bumped.

---

### TC-003: Add Dependencies

**Given** entity dependency added:
```yaml
blockedBy:
  - "TASK-003"  # Added
```

**When** mapping to Claude Code:
```javascript
TaskUpdate({
  taskId: "<claude-task-id>",
  addBlockedBy: ["<task-003-claude-id>"]
})
```

**Then** dependency reflected in both systems.

---

### TC-004: Complete Task

**Given** entity marked complete:
```yaml
status: completed
version: "1.0.1" -> "1.1.0"  # Minor bump for completion
```

**When** agent updates Claude Code:
```javascript
TaskUpdate({
  taskId: "<claude-task-id>",
  status: "completed"
})
```

**Then** task marked done in both systems.

---

## Validation Rules

### V-001: Subject Format
- Must be imperative: "Implement X", "Add Y", "Fix Z"
- Max 70 characters
- No trailing punctuation

### V-002: ActiveForm Format
- Must be present continuous: "Implementing X", "Adding Y"
- Matches subject semantically
- Used in spinner/progress display

### V-003: Status Transitions
Valid transitions:
```
pending -> in_progress
in_progress -> completed
in_progress -> pending (blocked)
pending -> deleted
in_progress -> deleted
```

### V-004: Version Bump Rules
| Change | Version Bump |
|--------|--------------|
| Status to completed | MINOR |
| Status to in_progress | PATCH |
| Add/remove dependency | MINOR |
| Fix typo in description | PATCH |
| Change acceptance criteria | MAJOR |

## Live Integration Test

### Setup
```bash
# Start Claude Code in test mode
claude --test-mode

# Load test entities
./tests/load-fixtures.sh
```

### Run Test
```bash
# Agent executes test sequence
claude << 'EOF'
Read pm/tests/fixtures/TASK-TEST-001.md
Create Claude Code task from entity fields
Verify task appears in TaskList
Update status to in_progress
Verify status change
Mark complete
Verify completion
EOF
```

### Expected Output
```
✓ TC-001: Task created with correct subject
✓ TC-002: Status updated to in_progress
✓ TC-003: Dependencies added correctly
✓ TC-004: Task completed successfully
```

## Agent Implementation

SDM/Staff Engineer agents should:

1. **Read entity file** before creating Claude Code task
2. **Extract required fields**: subject, description, activeForm
3. **Create task** using TaskCreate
4. **Track mapping** between entity ID and Claude task ID
5. **Update entity version** when task status changes
6. **Sync dependencies** using addBlocks/addBlockedBy

### Example Agent Workflow

```markdown
## Starting TASK-004

1. Read pm/entities/examples/TASK-004.md
2. TaskCreate with entity fields
3. TaskUpdate status=in_progress
4. Work on implementation...
5. TaskUpdate status=completed
6. Edit TASK-004.md: status=completed, version bump
7. Commit: "feat(auth): implement JWT generation - TASK-004"
```
