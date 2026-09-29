"""The AI Launch Scout: its job description, its rubric, and its agent config.

Every rung imports from here, so the agent only ever has one definition.
"""

from common import MODEL, TOPIC, ensure_agent

SYSTEM = f"""You are the AI Launch Scout. You track new launches and announcements in {TOPIC}.

How you work:
- Start by running `date` in bash so you know today's date. Never guess it.
- Search the web, then open the primary source (official blog, docs, GitHub release) before you trust a claim.
- Only report things announced in the last 7 days.
- Write for busy builders: what launched, why it matters, one line each. No hype words.
"""

TASK = """Find the 5 most notable launches or announcements in the last 7 days.
Write them to /mnt/session/outputs/brief.md as a short morning brief."""

# The grader reads this and scores each line on its own, so every line is a yes/no check.
RUBRIC = """# AI Launch Scout brief
- The file /mnt/session/outputs/brief.md exists.
- It lists exactly 5 items.
- Each item has: a bold title, a one-line "why it matters", and a source URL.
- Every source URL points to the primary source (company blog, docs, GitHub), not a news aggregator.
- Every item is dated within the last 7 days of today's date, and the date is shown.
- No two items are about the same launch.
- The whole brief is under 250 words.
"""


def scout_agent(ask_before_bash: bool = False) -> str:
    toolset = {"type": "agent_toolset_20260401", "default_config": {"enabled": True}}
    if ask_before_bash:
        # Rung 4: everything else runs freely, but bash needs a human "yes" first.
        toolset["configs"] = [{"name": "bash", "permission_policy": {"type": "always_ask"}}]
    return ensure_agent(
        "scout_agent_id",
        name="AI Launch Scout",
        model=MODEL,
        system=SYSTEM,
        tools=[toolset],
    )
