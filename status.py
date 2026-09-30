"""Everything you built, at a glance. Read-only: it creates nothing and costs nothing.

    uv run status.py

Run it at the end to see the agent, its sandbox, its memory, the daily schedule
and the latest runs. Each line also lives in the Console at platform.claude.com.
"""

from itertools import islice
from zoneinfo import ZoneInfo

from common import BOLD, DIM, GREEN, RESET, YELLOW, client, console_link, format_money, load_state

IST = ZoneInfo("Asia/Kolkata")
state = load_state()


def when(ts) -> str:
    return f"{ts.astimezone(IST):%d %b, %I:%M %p} IST"


def section(title: str) -> None:
    print(f"\n{BOLD}{title}{RESET}")


def missing(what: str, step: str) -> None:
    print(f"  {YELLOW}not created yet{RESET} {DIM}(run {step}){RESET}")


# One broken lookup (an archived object, a network blip) must never hide the rest of the report.
def show(fn) -> None:
    try:
        fn()
    except Exception as err:  # noqa: BLE001
        print(f"  {YELLOW}couldn't read this: {err.__class__.__name__}{RESET}")


def agents() -> None:
    section("Agents")
    for key, step in (("scout_agent_id", "step 1"), ("lead_agent_id", "step 6")):
        if key not in state:
            missing(key, step)
            continue
        a = client.beta.agents.retrieve(state[key])
        model = getattr(a.model, "id", a.model)
        roster = f", leads {len(a.multiagent.agents)} specialists" if getattr(a, "multiagent", None) else ""
        print(f"  {GREEN}●{RESET} {a.name}  version {a.version}  {DIM}{model}{roster}  {a.id}{RESET}")


def environment() -> None:
    section("Sandbox (environment)")
    if "environment_id" not in state:
        return missing("environment", "step 1")
    e = client.beta.environments.retrieve(state["environment_id"])
    print(f"  {GREEN}●{RESET} {e.name}  {DIM}{e.config.type} sandbox  {e.id}{RESET}")


def memory() -> None:
    section("Memory")
    if "memory_store_id" not in state:
        return missing("memory", "step 3")
    store_id = state["memory_store_id"]
    for m in client.beta.memory_stores.memories.list(store_id, path_prefix="/", view="full"):
        if m.type == "memory":
            lines = [ln for ln in (m.content or "").splitlines() if "|" in ln and not ln.startswith("#")]
            print(f"  {GREEN}●{RESET} {m.path}: {len(lines)} launches remembered")
            for ln in lines[-3:]:
                print(f"    {DIM}{ln[:100]}{RESET}")


def schedule() -> None:
    section("Daily schedule")
    if "deployment_id" not in state:
        return missing("schedule", "step 5")
    d = client.beta.deployments.retrieve(state["deployment_id"])
    if d.status == "active":
        nxt = d.schedule.upcoming_runs_at[0] if d.schedule.upcoming_runs_at else None
        print(f"  {GREEN}● ACTIVE{RESET}  next run {when(nxt) if nxt else '(none listed)'}")
    else:
        print(f"  {YELLOW}● {d.status.upper()}{RESET}  {DIM}resume with: uv run stop_schedule.py --resume{RESET}")
    print(f"  {DIM}{d.schedule.expression} ({d.schedule.timezone})  {d.id}{RESET}")


def sessions() -> None:
    section("Latest runs (sessions)")
    # Only this setup's agents, so older rehearsal runs in the same account don't show up.
    agent_ids = [state[k] for k in ("scout_agent_id", "lead_agent_id") if k in state]
    runs = [s for a in agent_ids for s in islice(client.beta.sessions.list(agent_id=a, limit=5, order="desc"), 5)]
    runs = sorted(runs, key=lambda s: s.created_at, reverse=True)[:5]
    if not runs:
        return missing("runs", "step 1")
    for s in runs:
        cost = getattr(getattr(s, "usage", None), "list_cost", None)
        mark = GREEN if s.status == "idle" else YELLOW
        print(f"  {mark}●{RESET} {s.status:<10} {format_money(cost) if cost else '':>6}  {when(s.created_at)}  {(s.title or '')[:48]}")
        print(f"    {DIM}{console_link(s.id)}{RESET}")

for part in (agents, environment, memory, schedule, sessions):
    show(part)
print(f"\n{DIM}Everything above also lives in the Console: https://platform.claude.com{RESET}")
