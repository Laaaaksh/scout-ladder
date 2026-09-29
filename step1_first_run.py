"""Rung 1: Agent + Environment + Session + Events.

The four building blocks. We describe the agent, pick a sandbox, start one job,
and watch the event stream while Claude searches, reads and writes on its own.
"""

from common import BUDGET, client, download_outputs, ensure_environment, run, show_cost
from scout import TASK, scout_agent

agent_id = scout_agent()               # 1. Agent: model + system prompt + tools
environment_id = ensure_environment()  # 2. Environment: the cloud sandbox it runs in

session = client.beta.sessions.create( # 3. Session: one running job
    agent=agent_id,
    environment_id=environment_id,
    title="Rung 1: first run",
    budget=BUDGET,
)

run(session.id, kickoff=[              # 4. Events: we send a message, it streams back
    {"type": "user.message", "content": [{"type": "text", "text": TASK}]},
])

download_outputs(session.id)
show_cost(session.id)
