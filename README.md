# Scout Ladder

Build a Claude Managed Agent in six steps. Each step adds one feature.

Workshop: Agent & Learn, Claude Community Bhopal.

The agent is the AI Launch Scout. Every morning the scout searches the web for new launches in agentic AI, checks the primary sources, and writes a five-item brief. The finale is a second agent team: a lead plus three specialists who stress-test a startup idea.

## What you need

1. Python 3.10 or newer. [uv](https://docs.astral.sh/uv/) is the easiest way to run this repo.
2. An Anthropic API key with credits. Create one at https://platform.claude.com/settings/keys.

## Setup (2 minutes)

```bash
git clone https://github.com/Laaaaksh/scout-ladder.git
cd scout-ladder
cp .env.example .env        # then paste your key after ANTHROPIC_API_KEY=
uv sync                     # or: pip install -r requirements.txt
```

No uv? Replace `uv run` with `python` in every command below.

## The ladder

| Step | Command | Feature you add | What you see |
|---|---|---|---|
| 1 | `uv run step1_first_run.py` | Agent, Environment, Session, Events | The scout searches, reads, and writes `brief.md` while you watch |
| 2 | `uv run step2_outcome.py` | Outcomes | A separate grader checks the brief against a rubric and sends the scout back to fix gaps |
| 3 | `uv run step3_memory.py` (run twice) | Memory store | Run two skips everything run one already reported |
| 4 | `uv run step4_permissions.py` | Permission policy | The scout stops and asks you before every bash command |
| 5 | `uv run step5_schedule.py` | Scheduled deployment | The scout runs daily at 8 AM IST in Anthropic's cloud, with no server of yours |
| 6 | `uv run step6_stress_test.py "your idea"` | Multi-agent | A lead hands your idea to three specialists in parallel and writes a verdict |

Output files land in `outputs/<session-id>/`. Every run prints a Console link where you watch the full trace, tool calls, and cost.

## Where each feature lives in the code

- `scout.py` holds the scout's job description, rubric, and agent config. Edit the rubric and rerun step 2 to watch the grader hold the scout to your new rules.
- `common.py` holds the plumbing: the API client, saved IDs, the live event printer, and file downloads.
- Each `stepN_*.py` file is under 40 lines. Read one top to bottom before you run the next.

## Spending safety

- Every session has a hard cap of $3.00 (`SCOUT_BUDGET_CENTS=300` in `.env`). At the cap the session pauses. Nothing runs past the cap.
- A plain run costs about $1. A graded run (research, grading, one revision) costs $2 to $3.
- The daily schedule caps each run at $5 (`SCOUT_DEPLOY_BUDGET_CENTS=500`). Each day digs past everything already in memory, so later runs cost more.
- Step 5 creates a daily schedule. Stop the schedule when you finish:

```bash
uv run stop_schedule.py
```

- Agents, environments, and memory stores are created once. Their IDs live in `.scout-state.json`, so rerunning a step reuses them. Delete `.scout-state.json` to start fresh.

## Change the scout

Set these in `.env`:

- `SCOUT_TOPIC`: what the scout tracks. Try `Indian AI startups` or `open-source LLMs`.
- `SCOUT_MODEL`: defaults to `claude-opus-5`.
- `SCOUT_EFFORT`: how hard the model thinks before each step. Defaults to `medium`. Use `high` for deeper research at a higher cost.
- `SPECIALIST_MODEL`: the model for the three finale specialists. Defaults to `claude-sonnet-5`, which costs less.

## Next steps

- Docs: https://platform.claude.com/docs/en/managed-agents/overview
- Full apps built on Managed Agents: https://github.com/anthropics/claude-quickstarts/tree/main/managed-agents
- One notebook per feature: https://github.com/anthropics/claude-cookbooks/tree/main/managed_agents
- Build your own agent with Claude Code as your guide: https://github.com/anthropics/launch-your-agent
