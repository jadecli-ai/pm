# PM System Integration Tests

> Tests validating entity schema and Claude Code task alignment

## Test Categories

### 1. Schema Validation
Validates that entity files conform to their schemas.

### 2. Claude Code Task Alignment
Verifies entities can be converted to/from Claude Code TaskCreate/TaskUpdate.

### 3. Dependency Graph
Validates dependency relationships are consistent.

### 4. SemVer Compliance
Checks version bumps follow semver rules.

## Running Tests

```bash
# Run all tests
./tests/run-tests.sh

# Run specific test
./tests/run-tests.sh --test schema

# Validate single entity
./tests/validate-entity.sh pm/entities/examples/TASK-004.md
```

## Test Files

| File | Purpose |
|------|---------|
| `run-tests.sh` | Test runner |
| `validate-entity.sh` | Single entity validator |
| `claude-code-alignment.md` | Claude Code integration test spec |
| `fixtures/` | Test fixture entities |
