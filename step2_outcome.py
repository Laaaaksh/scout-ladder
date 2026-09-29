"""Rung 2: Outcomes. Tell the agent what "done" means and let a grader hold it to that.

Same agent, same sandbox. The only change: instead of a plain message we send a
`user.define_outcome` with a rubric. A separate grader (its own context window)
checks the work line by line and sends it back until it passes.
"""

from common import BUDGET, client, download_outputs, ensure_environment, run, show_cost
from scout import RUBRIC, TASK, scout_agent

session = client.beta.sessions.create(
    agent=scout_agent(),
    environment_id=ensure_environment(),
    title="Rung 2: graded run",
    budget=BUDGET,
)

run(session.id, kickoff=[
    {
        "type": "user.define_outcome",
        "description": TASK,
        "rubric": {"type": "text", "content": RUBRIC},
        "max_iterations": 3,
    },
])

download_outputs(session.id)
show_cost(session.id)
