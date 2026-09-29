"""Pause the daily scout so it stops spending credits. Reversible: unpause any time.

    uv run stop_schedule.py            # pause
    uv run stop_schedule.py --resume   # unpause
"""

import sys

from common import client, load_state

deployment_id = load_state().get("deployment_id")
if not deployment_id:
    sys.exit("No deployment saved in .scout-state.json. Nothing to pause.")

if "--resume" in sys.argv:
    client.beta.deployments.unpause(deployment_id)
    print(f"Resumed {deployment_id}. Next run is at the next 8 AM IST.")
else:
    client.beta.deployments.pause(deployment_id)
    print(f"Paused {deployment_id}. No more scheduled runs until you pass --resume.")
