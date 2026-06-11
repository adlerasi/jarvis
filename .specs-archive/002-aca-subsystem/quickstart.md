# Quickstart Validation Guide: ACA Subsystem

**Date**: 2026-06-10
**Prerequisites**: JARVIS running with Gemini or Ollama backend, screen_vision working, active desktop session unlocked.

## Validation Scenarios

### Scenario 1: Basic Goal Execution (MVP)

Verifies the core observe → plan → act → reflect loop.

**Setup**:
```bash
# Ensure JARVIS is running with a visible desktop
.venv/bin/python3 main.py
```

**Steps**:
1. Enable ACA (via JARVIS UI Agent Panel toggle or agent skill trigger)
2. Give a simple goal: "Open Notepad and type ACA test"
3. Observe the Agent Panel showing:
   - Goal text displayed
   - Task graph with 2+ steps rendered
   - Active step highlighted
   - Progress updates via `write_log()`
4. Wait for completion summary

**Expected Outcome**: Notepad opens, "ACA test" is typed, agent reports success summary.

**Validation Command**:
```bash
ls memory/agent/sessions/  # Should contain a session JSON file
python3 -c "import json; data=json.load(open('memory/agent/current_goal.json')); print(data['status'])"
# Should print: "completed"
```

---

### Scenario 2: Error Recovery

Verifies the agent detects and recovers from unexpected states.

**Setup**: Same as Scenario 1.

**Steps**:
1. Give goal: "Open Calculator and compute 15 * 3"
2. While agent is planning, manually open a different app (e.g., Paint) to create an unexpected state
3. Agent should:
   - Observe the unexpected app via screen_vision
   - Log the mismatch
   - Either close Paint and open Calculator, or adapt the plan

**Expected Outcome**: Agent adapts to the unexpected state and still completes the goal. Failure to adapt within 2 retries should escalate to user.

---

### Scenario 3: Human Approval Mode

Verifies high-risk actions pause for user confirmation.

**Setup**:
1. Enable approval mode in the Agent Panel
2. Give goal: "Clean up temp files in Downloads"

**Steps**:
1. Agent plans the steps
2. When cleanup_folder or shell command is queued:
   - Agent Panel shows approval request with action details
   - Request includes: tool name, parameters, risk level "high"
   - Approve and Deny buttons visible
3. Click "Approve"
4. Agent continues and completes the goal

**Expected Outcome**: Execution pauses before high-risk action. Action only executes after approval. Log shows approval request and response.

---

### Scenario 4: Execution Limits

Verifies the agent respects step and time limits.

**Setup**: None.

**Steps**:
1. Give a deliberately complex/vague goal: "Browse the web and find every mention of JARVIS"
2. Agent should limit to 20 steps max or 5 minutes wall-clock
3. After limit, agent halts and shows partial progress summary

**Expected Outcome**: Agent stops after hitting limits. User is notified with partial progress.

---

### Scenario 5: Agent Skill Trigger

Verifies the agent skill intercepts natural language automation requests.

**Steps**:
1. Speak or type: "Handle this automatically" or "Benim için hallet"
2. Agent Skill Manager should route to ACA
3. Agent Panel activates with listening state
4. Follow up with a goal

**Expected Outcome**: Skill triggers on matching phrases. Agent Panel activates without requiring manual toggle.

---

## Integration Test Commands

```bash
# Run ACA-specific unit tests
.venv/bin/python3 -m unittest tests.test_aca_subsystem -v

# Verify no existing tests broken
.venv/bin/python3 -m unittest tests.test_smoke -v

# Check agent memory persistence
ls -la memory/agent/

# Verify Agent Panel loads (manual: launch JARVIS and check UI)
```

## Rollback Instructions

If ACA causes issues:

1. Disable agent skill: Remove or rename `skills/agent/agent_skill.py`
2. Disable ACA module: Comment out `# from core.agent.agent_manager import AgentManager` in `main.py`
3. Remove agent data: `rm -rf memory/agent/` (optional, clears learned workflows)

## References

- [Data Model](./data-model.md) — entity definitions and persistence
- [Spec](./spec.md) — user stories, requirements, success criteria
- [Plan](./plan.md) — implementation plan, architecture decisions
