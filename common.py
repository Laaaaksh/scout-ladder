"""Shared plumbing for every rung: client, saved IDs, the event printer, and downloads.

The rung files stay short because everything boring lives here.
"""

import json
import os
import sys
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY (or an `ant auth login` profile)


def _preflight() -> None:
    """Fail in plain English before the demo starts, not with a stack trace halfway through.

    The two things that break most in a workshop room: no key set up, and a key that's
    wrong or has no credits. One cheap list call catches both.
    """
    try:
        client.beta.environments.list(limit=1)
    except TypeError:  # the SDK found no credentials at all
        sys.exit("No API key found. Copy .env.example to .env and paste your key from "
                 "https://platform.claude.com/settings/keys (or run `ant auth login`).")
    except anthropic.AuthenticationError:
        sys.exit("Your API key was rejected. Check ANTHROPIC_API_KEY in .env (no quotes, no spaces).")
    except anthropic.PermissionDeniedError as err:
        sys.exit(f"Your key works but can't use Managed Agents: {err.message}")


_preflight()

MODEL = os.getenv("SCOUT_MODEL", "claude-opus-5")
SPECIALIST_MODEL = os.getenv("SPECIALIST_MODEL", "claude-sonnet-5")
TOPIC = os.getenv("SCOUT_TOPIC", "agentic AI (AI agents, agent frameworks, agent products)")
WORKSPACE = os.getenv("ANTHROPIC_WORKSPACE", "default")

# Hard spend cap per session, in US cents as a string ("100" = $1.00).
# Every session in this repo gets it, so a runaway loop can never eat your credits.
BUDGET = {"type": "limit", "max_list_cost": {"amount": os.getenv("SCOUT_BUDGET_CENTS", "100"), "currency": "USD"}}

STATE_FILE = Path(__file__).with_name(".scout-state.json")
OUTPUT_DIR = Path(__file__).with_name("outputs")


# ---------------------------------------------------------------- saved IDs
# Agents, environments and memory stores are create-once objects. We save their IDs so
# re-running a rung (which you will do on stage) reuses them instead of piling up copies.

def load_state() -> dict:
    return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}


def save_state(**updates) -> None:
    state = load_state() | updates
    STATE_FILE.write_text(json.dumps(state, indent=2))


def ensure_environment() -> str:
    env_id = load_state().get("environment_id")
    if env_id:
        return env_id
    env = client.beta.environments.create(
        name="scout-sandbox",
        config={"type": "cloud", "networking": {"type": "unrestricted"}},
    )
    save_state(environment_id=env.id)
    print(f"Created environment {env.id}")
    return env.id


def ensure_agent(key: str, **config) -> str:
    """Create the agent the first time; after that, update it in place (a new version)."""
    agent_id = load_state().get(key)
    if agent_id:
        agent = client.beta.agents.update(agent_id, **config)
        print(f"Agent {config['name']}: {agent.id} (version {agent.version})")
        return agent.id
    agent = client.beta.agents.create(**config)
    save_state(**{key: agent.id})
    print(f"Created agent {config['name']}: {agent.id} (version {agent.version})")
    return agent.id


def console_link(session_id: str) -> str:
    return f"https://platform.claude.com/workspaces/{WORKSPACE}/sessions/{session_id}"


# ---------------------------------------------------------------- live event printer

DIM, BOLD, CYAN, GREEN, YELLOW, RED, MAGENTA, RESET = (
    "\033[2m", "\033[1m", "\033[36m", "\033[32m", "\033[33m", "\033[31m", "\033[35m", "\033[0m",
)


def _to_plain(obj):
    """json.dumps fallback. SDK responses are pydantic models, not dicts, so turn them into dicts."""
    return obj.model_dump(mode="json") if hasattr(obj, "model_dump") else str(obj)


def _short(value, limit=110) -> str:
    # default=_to_plain: printing any SDK object (errors, costs, tool inputs) must never crash a run
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=_to_plain)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _tool_summary(name: str, tool_input: dict) -> str:
    for field in ("query", "url", "command", "file_path", "path", "pattern"):
        if isinstance(tool_input, dict) and field in tool_input:
            return _short(tool_input[field])
    return _short(tool_input)


def _ask_permission(event) -> dict:
    """Terminal prompt for an always_ask tool call. Returns the user.tool_confirmation event."""
    print(f"\n{YELLOW}{BOLD}  ✋ Agent wants to run {event.name}:{RESET} {_tool_summary(event.name, event.input)}")
    answer = input(f"{YELLOW}     Allow? [y/n] {RESET}").strip().lower()
    if answer.startswith("y"):
        return {"type": "user.tool_confirmation", "tool_use_id": event.id, "result": "allow"}
    return {
        "type": "user.tool_confirmation",
        "tool_use_id": event.id,
        "result": "deny",
        "deny_message": "The human denied this command. Continue without it.",
    }


def _print_event(event) -> dict | None:
    """Print one event. Returns a confirmation event to send back, if the agent is waiting on one."""
    kind = event.type
    if kind == "agent.message":
        for block in event.content:
            if block.type == "text" and block.text.strip():
                print(f"\n{BOLD}🤖 {RESET}{block.text.strip()}\n")
    elif kind in ("agent.tool_use", "agent.mcp_tool_use"):
        if getattr(event, "evaluated_permission", None) == "ask":
            return _ask_permission(event)
        print(f"{CYAN}  🔧 {event.name}{RESET} {DIM}{_tool_summary(event.name, event.input)}{RESET}")
    elif kind == "span.outcome_evaluation_start":
        print(f"\n{MAGENTA}  📝 Grader checking iteration {event.iteration + 1}…{RESET}")
    elif kind == "span.outcome_evaluation_end":
        color = GREEN if event.result == "satisfied" else YELLOW
        print(f"{color}{BOLD}  📝 Grader: {event.result}{RESET} {DIM}{_short(event.explanation, 300)}{RESET}\n")
    elif kind == "session.thread_created":
        print(f"{MAGENTA}  🧵 New sub-agent thread: {event.agent_name}{RESET}")
    elif kind == "agent.thread_message_sent":
        print(f"{MAGENTA}  ➡️  Lead → {event.to_agent_name}:{RESET} {DIM}{_short(_text_of(event.content), 160)}{RESET}")
    elif kind == "agent.thread_message_received":
        print(f"{MAGENTA}  ⬅️  {event.from_agent_name} reported back{RESET} {DIM}{_short(_text_of(event.content), 160)}{RESET}")
    elif kind == "session.error":
        print(f"{RED}  ⚠️  session error: {_short(getattr(event, 'error', event), 300)}{RESET}")
    return None


def _text_of(content) -> str:
    if isinstance(content, str):
        return content
    return " ".join(getattr(b, "text", "") for b in (content or []))


def _is_done(event) -> bool:
    if event.type == "session.status_terminated":
        return True
    if event.type == "session.status_idle":
        reason = getattr(event.stop_reason, "type", None)
        if reason == "budget_reached":
            print(f"{RED}{BOLD}  💸 Hit the session budget ({BUDGET['max_list_cost']['amount']}¢). Stopping.{RESET}")
        return reason != "requires_action"
    return False


def run(session_id: str, kickoff: list[dict] | None = None) -> None:
    """Stream a session until it's truly idle. Sends `kickoff` after the stream opens.

    Venue Wi-Fi drops connections, so if the stream dies we reconnect and replay
    anything we missed from the event list (deduped by event ID) instead of crashing.
    """
    print(f"{DIM}Watch it live: {console_link(session_id)}{RESET}\n")
    seen: set[str] = set()
    pending_kickoff = kickoff
    for attempt in range(5):
        try:
            with client.beta.sessions.events.stream(session_id=session_id) as stream:
                if pending_kickoff:
                    client.beta.sessions.events.send(session_id=session_id, events=pending_kickoff)
                    pending_kickoff = None
                elif attempt > 0:  # reconnect: catch up on anything that happened while we were gone
                    for event in client.beta.sessions.events.list(session_id=session_id):
                        if event.id not in seen:
                            seen.add(event.id)
                            if _handle(session_id, event):
                                return
                for event in stream:
                    if event.id in seen:
                        continue
                    seen.add(event.id)
                    if _handle(session_id, event):
                        return
            return
        except (anthropic.APIConnectionError, anthropic.APITimeoutError) as err:
            wait = 2 ** attempt
            print(f"{YELLOW}  (stream dropped: {err.__class__.__name__}; reconnecting in {wait}s){RESET}")
            time.sleep(wait)
    sys.exit(f"Gave up reconnecting. The session keeps running server-side: {console_link(session_id)}")


def _handle(session_id: str, event) -> bool:
    reply = _print_event(event)
    if reply:
        client.beta.sessions.events.send(session_id=session_id, events=[reply])
    return _is_done(event)


# ---------------------------------------------------------------- outputs

def download_outputs(session_id: str) -> list[Path]:
    """Save whatever the agent wrote to /mnt/session/outputs/ into ./outputs/<session>/."""
    target = OUTPUT_DIR / session_id
    for _ in range(5):  # files take a second or two to show up after the session idles
        files = client.beta.files.list(scope_id=session_id, betas=["managed-agents-2026-04-01"]).data
        if files:
            break
        time.sleep(2)
    saved = []
    for f in files:
        target.mkdir(parents=True, exist_ok=True)
        path = target / f.filename
        client.beta.files.download(f.id).write_to_file(path)
        saved.append(path)
        print(f"{GREEN}  📄 Saved {path.relative_to(Path.cwd()) if path.is_relative_to(Path.cwd()) else path}{RESET}")
    if not saved:
        print(f"{YELLOW}  No output files yet. Check the Console: {console_link(session_id)}{RESET}")
    return saved


def format_money(money) -> str:
    """The API sends money as {"amount": "42", "currency": "USD"}: whole cents, as a string."""
    cents = int(money.amount)
    symbol = "$" if money.currency == "USD" else f"{money.currency} "
    return f"{symbol}{cents // 100}.{cents % 100:02d}"


def show_cost(session_id: str) -> None:
    # Cosmetic, so it never gets to fail a run whose real work already finished.
    try:
        session = client.beta.sessions.retrieve(session_id)
        cost = getattr(getattr(session, "usage", None), "list_cost", None)
        if cost is not None:
            print(f"{DIM}  Session cost (list price): {format_money(cost)}{RESET}")
    except Exception as err:  # noqa: BLE001
        print(f"{DIM}  (couldn't read the cost: {err.__class__.__name__}. See the Console link above.){RESET}")
