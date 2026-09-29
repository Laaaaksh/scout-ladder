"""Rung 5: Scheduled deployment. The scout runs every morning at 8 AM IST, with no server of ours.

A deployment bundles agent + environment + memory + kickoff event + a cron schedule.
Each firing becomes a normal session. `run()` fires one right now so we can test it.
Unattended runs can't answer "allow bash?", so this uses the scout without the ask gate.
"""

from common import BUDGET, client, console_link, ensure_environment, load_state, save_state
from scout import RUBRIC, TASK, scout_agent
from step3_memory import MEMORY

config = dict(
    name="AI Launch Scout: daily 8 AM",
    agent=scout_agent(ask_before_bash=False),
    environment_id=ensure_environment(),
    resources=[MEMORY],
    initial_events=[
        {"type": "user.define_outcome", "description": TASK, "rubric": {"type": "text", "content": RUBRIC}},
    ],
    schedule={"type": "cron", "expression": "0 8 * * *", "timezone": "Asia/Kolkata"},
    budget=BUDGET,  # applied to each run separately
)

deployment_id = load_state().get("deployment_id")
if deployment_id:
    deployment = client.beta.deployments.update(deployment_id, **config)
else:
    deployment = client.beta.deployments.create(**config)
    save_state(deployment_id=deployment.id)

print(f"Deployment {deployment.id} is {deployment.status}")
print("Next runs (UTC):")
for when in deployment.schedule.upcoming_runs_at[:3]:
    print(f"  {when}")

# Don't wait until tomorrow: fire one run right now.
run_record = client.beta.deployments.run(deployment.id)
session_id = getattr(run_record, "session_id", None)
print(f"\nManual run started: {run_record.id}")
if session_id:
    print(f"Watch it: {console_link(session_id)}")
