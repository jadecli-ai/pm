---
id: "TASK-004"
version: "1.0.1"
type: task
status: in_progress
created: 2025-02-10
updated: 2025-02-11

parent: "STORY-002"
children:
  - "SUBTASK-008"
  - "SUBTASK-009"

dependsOn:
  - "npm:jsonwebtoken@9.0.2"
  - "npm:@types/jsonwebtoken@9.0.5"
  - "TASK-003"

blocks:
  - "TASK-005"
  - "TASK-006"

blockedBy: []

owner: "staff-engineer-2"
domain: "backend"

priority: "P1-high"
iteration: "iteration-5"
size: "M"
agentHours: 3

subject: "Implement JWT token generation"
activeForm: "Implementing JWT token generation"

tags: ["auth", "jwt", "security"]
---

# Implement JWT Token Generation

## Objective
Create JWT token generation and verification utilities for the authentication system.

## Acceptance Criteria
- [ ] `generateToken(user)` returns signed JWT with correct claims
- [ ] `generateRefreshToken(user)` returns separate refresh token
- [ ] `verifyToken(token)` validates and decodes JWT
- [ ] Tokens use RS256 algorithm
- [ ] Access token expires in 15 minutes
- [ ] Refresh token expires in 7 days
- [ ] Secret/keys loaded from environment variables
- [ ] Unit tests with 90%+ coverage

## Implementation Notes

### Architecture
```
src/auth/
├── jwt.ts          # Token generation/verification
├── keys.ts         # Key management (RS256)
└── types.ts        # Token payload types
```

### Token Payload Structure
```typescript
interface TokenPayload {
  sub: string;      // User ID
  email: string;    // User email
  roles: string[];  // User roles
  type: 'access' | 'refresh';
  iat: number;      // Issued at
  exp: number;      // Expiration
}
```

### Environment Variables
```
JWT_PRIVATE_KEY=<RS256 private key>
JWT_PUBLIC_KEY=<RS256 public key>
JWT_ACCESS_EXPIRY=15m
JWT_REFRESH_EXPIRY=7d
```

## Files
- `src/auth/jwt.ts` - Create: Core token utilities
- `src/auth/keys.ts` - Create: Key loading and caching
- `src/auth/types.ts` - Modify: Add TokenPayload interface
- `tests/auth/jwt.test.ts` - Create: Unit tests
- `.env.example` - Modify: Add JWT variables

## Dependencies

### Code Dependencies
- `jsonwebtoken@9.0.2` - JWT library
- `@types/jsonwebtoken@9.0.5` - TypeScript types

### Task Dependencies
- `TASK-003` - Login endpoint exists to provide user data

## Subtasks
- [x] SUBTASK-008: Create jwt.ts with generateToken (completed)
- [ ] SUBTASK-009: Write unit tests (in_progress)

## Test Requirements

### Unit Tests (tests/auth/jwt.test.ts)
```typescript
describe('jwt', () => {
  describe('generateToken', () => {
    it('returns valid JWT string');
    it('contains correct user claims');
    it('has correct expiration');
  });

  describe('verifyToken', () => {
    it('decodes valid token');
    it('throws on expired token');
    it('throws on invalid signature');
  });
});
```

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2025-02-10 | Task created |
| 1.0.1 | 2025-02-11 | SUBTASK-008 completed |
