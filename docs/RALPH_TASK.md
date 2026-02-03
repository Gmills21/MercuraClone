---
task: Integrate Ralph Wiggum for autonomous AI development
test_command: "echo 'Ralph integration test'"
---

# Task: Ralph Wiggum Integration for MercuraClone

Integrate Ralph Wiggum script wrapper to enable autonomous AI development with deliberate context management. This allows AI agents to run in a "memory loop" where progress persists in files and git rather than LLM context.

## Requirements

1. **Ralph Wiggum Setup**: Script wrapper that forces Cursor's agent to run in memory loop
2. **Context Management**: State lives in files/git, not LLM context window
3. **Token Tracking**: Monitor context usage and rotate when approaching limits
4. **Error Handling**: Detect failures and learn from them via guardrails
5. **Git Integration**: Automatic commits to maintain state across iterations

## Success Criteria

1. [x] Ralph Wiggum scripts installed in .cursor/ralph-scripts/
2. [x] .ralph/ state directory initialized with guardrails.md, progress.md, logs
3. [x] RALPH_TASK.md template created for task definitions
4. [x] Windows-compatible PowerShell setup script created
5. [x] Integration documented for AI agent command usage
6. [ ] Test Ralph loop with a simple task
7. [ ] Verify context rotation works at token limits
8. [ ] Confirm git commits are created automatically
9. [ ] Validate error detection and guardrail learning

## How Ralph Works

Ralph treats LLM context like memory:
- `malloc()` = reading files, tool outputs, conversation
- **No `free()`** - context cannot be selectively released
- Solution: Deliberately rotate to fresh context before pollution builds up

### The Memory Loop

```
Iteration 1                    Iteration 2                    Iteration N
┌──────────────────┐          ┌──────────────────┐          ┌──────────────────┐
│ Fresh context    │          │ Fresh context    │          │ Fresh context    │
│       │          │          │       │          │          │       │          │
│       ▼          │          │       ▼          │          │       ▼          │
│ Read RALPH_TASK  │          │ Read RALPH_TASK  │          │ Read RALPH_TASK  │
│ Read guardrails  │──────────│ Read guardrails  │──────────│ Read guardrails  │
│ Read progress    │  (state  │ Read progress    │  (state  │ Read progress    │
│       │          │  in git) │       │          │  in git) │       │          │
│       ▼          │          │       ▼          │          │       ▼          │
│ Work on criteria │          │ Work on criteria │          │ Work on criteria │
│ Commit to git    │          │ Commit to git    │          │ Commit to git    │
│       │          │          │       │          │          │       │          │
│       ▼          │          │       ▼          │          │       ▼          │
│ 80k tokens       │          │ 80k tokens       │          │ All [x] done!    │
│ ROTATE ──────────┼──────────┼──────────────────┼──────────┼──► COMPLETE      │
└──────────────────┘          └──────────────────┘          └──────────────────┘
```

## Usage Instructions

### Starting Ralph for AI Agent Commands

1. **Edit RALPH_TASK.md** with your specific task and success criteria
2. **Run Ralph setup**:
   ```powershell
   # Windows PowerShell
   .\scripts\ralph-setup.ps1

   # Or use the batch file
   .\.cursor\ralph-scripts\ralph-setup.bat
   ```
3. **Monitor progress**:
   ```bash
   tail -f .ralph/activity.log
   cat .ralph/errors.log
   ```

### Task Definition Format

Each task should have:
- **Frontmatter**: `task` and `test_command` fields
- **Clear requirements**: What needs to be accomplished
- **Checkbox criteria**: Specific, testable success criteria
- **Context**: Any relevant background information

### Example Task for This Project

```markdown
---
task: Add user authentication to the API
test_command: "python -m pytest tests/test_auth.py"
---

# Task: Implement User Authentication

Add JWT-based authentication to the FastAPI backend.

## Requirements

1. Password hashing with bcrypt
2. JWT token generation and validation
3. Protected routes with dependency injection
4. User registration and login endpoints

## Success Criteria

1. [ ] POST /auth/register creates user with hashed password
2. [ ] POST /auth/login returns JWT token for valid credentials
3. [ ] GET /protected requires valid JWT token
4. [ ] Invalid tokens return 401 Unauthorized
5. [ ] All auth tests pass
```

## Context Rotation Signals

Ralph monitors context usage and sends signals:

| Signal | Token % | Action |
|--------|---------|--------|
| 🟢 Healthy | < 60% | Continue working |
| 🟡 Warning | 60-80% | Wrap up current work |
| 🔴 Critical | > 80% | Rotate to fresh context |
| ROTATE | ≥ 80k | Force context rotation |
| GUTTER | Pattern | Agent stuck, manual intervention needed |

## Learning from Failures

When errors occur, Ralph adds "Signs" to `.ralph/guardrails.md`:

```markdown
### Sign: Check imports before adding
- **Trigger**: Adding a new import statement
- **Instruction**: First check if import already exists in file
- **Added after**: Iteration 3 - duplicate import caused build failure
```

Future iterations read guardrails first and follow them.

## Git Integration

Ralph commits frequently to maintain state:

```bash
git add -A && git commit -m 'ralph: implement user auth endpoint'
git add -A && git commit -m 'ralph: add JWT validation middleware'
git push  # After every 2-3 commits
```

**Important**: Commits ARE the agent's memory. Next iteration picks up from git history.

## Monitoring and Troubleshooting

### Real-time Monitoring

```bash
# Watch activity in real-time
tail -f .ralph/activity.log

# Example output:
# [12:34:56] 🟢 READ src/auth.py (245 lines, ~24.5KB)
# [12:34:58] 🟢 WRITE src/routes/auth.py (50 lines, 2.1KB)
# [12:35:01] 🟢 SHELL python -m pytest → exit 0
# [12:35:10] 🟢 TOKENS: 45,230 / 80,000 (56%)
```

### Error Detection

```bash
# Check for failures
cat .ralph/errors.log

# Check guardrails for learned lessons
cat .ralph/guardrails.md
```

### Common Issues

1. **"cursor-agent CLI not found"**: Install from https://cursor.com/install
2. **Context rotates too frequently**: Task too complex, break into smaller pieces
3. **Agent keeps failing**: Check `.ralph/errors.log` and add guardrails
4. **Task never completes**: Criteria too vague, make them specific and testable

## Integration Benefits

- **Autonomous development**: AI agents work independently on complex tasks
- **Context management**: Prevents "gutter" situations from context pollution
- **State persistence**: Progress survives IDE restarts and context rotations
- **Learning system**: Agents improve over time via guardrails
- **Git-native workflow**: All changes tracked and revertible

## Ralph Instructions for Agents

1. Work on the next unchecked criterion in RALPH_TASK.md
2. Check off completed criteria with `[x]`
3. Run tests after changes
4. Commit changes frequently with descriptive messages
5. When ALL criteria are `[x]`, output `<ralph>COMPLETE</ralph>`
6. If stuck 3+ times on same issue, output `<ralph>GUTTER</ralph>`

---

## Ralph Instructions

1. Read this RALPH_TASK.md file completely
2. Read .ralph/guardrails.md for lessons learned
3. Read .ralph/progress.md for current status
4. Work on the next incomplete criterion (marked [ ])
5. Mark completed criteria as [x] when done
6. Commit changes with descriptive messages
7. When all criteria are [x], output: `<ralph>COMPLETE</ralph>`
8. If stuck on same issue 3+ times, output: `<ralph>GUTTER</ralph>`
