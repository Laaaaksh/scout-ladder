"""Rung 4: Permission policies. A human checkpoint in one line of config.

We update the agent (it becomes version N+1) so bash is `always_ask`. Web search and
file tools still run freely, but every shell command pauses until you type y or n.
"""

from common import BUDGET, client, download_outputs, ensure_environment, run, show_cost
from scout import RUBRIC, TASK, scout_agent
from step3_memory import MEMORY

session = client.beta.sessions.create(
    agent=scout_agent(ask_before_bash=True),
    environment_id=ensure_environment(),
    title="Rung 4: ask before bash",
    resources=[MEMORY],
    budget=BUDGET,
)

run(session.id, kickoff=[
    {"type": "user.define_outcome", "description": TASK, "rubric": {"type": "text", "content": RUBRIC}},
])

download_outputs(session.id)
show_cost(session.id)
