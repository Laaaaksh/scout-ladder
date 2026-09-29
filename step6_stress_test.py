"""Finale: the Startup Idea Stress-Tester. One lead agent, three specialists, working in parallel.

    uv run step6_stress_test.py "An app that books auto-rickshaws for school kids in Bhopal"

The lead gets `multiagent` on its config and, with it, tools to hand work to the roster.
Each specialist runs in its own thread with its own context, model and tools. They share
one sandbox, so they can pass files around. We still create one session and read one stream.
"""

import sys

from common import BUDGET, MODEL, SPECIALIST_MODEL, client, download_outputs, ensure_agent, ensure_environment, run, show_cost

READ_AND_SEARCH = {
    "type": "agent_toolset_20260401",
    "default_config": {"enabled": False},
    "configs": [{"name": n, "enabled": True} for n in ("read", "write", "glob", "grep", "web_search", "web_fetch")],
}

market = ensure_agent(
    "market_agent_id",
    name="Market Researcher",
    description="Sizes the market and finds competitors. Give it the idea; it reports who else does this, pricing, and demand signals, with source URLs.",
    model=SPECIALIST_MODEL,
    system="You research markets. Find real competitors (with URLs), how they price, and evidence of demand. Numbers need sources. Write your findings to /tmp/work/market.md, then report a 5-bullet summary.",
    tools=[READ_AND_SEARCH],
)
builder = ensure_agent(
    "builder_agent_id",
    name="Tech Feasibility",
    description="Judges how hard the idea is to build. Give it the idea; it reports the stack, the hardest part, and a 2-week MVP scope.",
    model=SPECIALIST_MODEL,
    system="You are a pragmatic senior engineer. For the idea you're given: pick a simple stack, name the single hardest technical risk, and scope an MVP one person can ship in 2 weeks. Write to /tmp/work/tech.md, then report a 5-bullet summary.",
    tools=[READ_AND_SEARCH],
)
skeptic = ensure_agent(
    "skeptic_agent_id",
    name="Devil's Advocate",
    description="Argues the idea will fail. Give it the idea; it reports the 3 strongest reasons, each backed by evidence.",
    model=SPECIALIST_MODEL,
    system="Your job is to kill the idea. Find the 3 strongest reasons it fails: regulation, unit economics, distribution, trust, incumbents. Back each with evidence (URL). Write to /tmp/work/risks.md, then report a 5-bullet summary.",
    tools=[READ_AND_SEARCH],
)

lead = ensure_agent(
    "lead_agent_id",
    name="Idea Lead",
    model=MODEL,
    system="""You stress-test startup ideas.
1. Send the idea to Market Researcher, Tech Feasibility and Devil's Advocate at the same time. Give each the full idea text; they cannot see this conversation.
2. When all three report back, read their files in /tmp/work/ and weigh them against each other.
3. Write /mnt/session/outputs/verdict.md: a one-line verdict (Build it / Pivot / Drop it), a score out of 10, the strongest argument on each side, and the first experiment to run this week.
Keep the verdict under 300 words. Be honest, not encouraging.""",
    tools=[{"type": "agent_toolset_20260401"}],
    multiagent={"type": "coordinator", "agents": [market, builder, skeptic]},
)

idea = " ".join(sys.argv[1:]) or "A WhatsApp bot that helps small kirana stores in Bhopal reorder stock automatically"
print(f"\nStress-testing: {idea}\n")

session = client.beta.sessions.create(
    agent=lead,
    environment_id=ensure_environment(),
    title=f"Stress test: {idea[:60]}",
    budget=BUDGET,
)
run(session.id, kickoff=[{"type": "user.message", "content": [{"type": "text", "text": f"Stress-test this idea: {idea}"}]}])

download_outputs(session.id)
show_cost(session.id)
