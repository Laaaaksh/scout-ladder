"""Rung 3: Memory. Run it twice; the second run skips what the first one already reported.

A memory store is a folder that outlives the session. It shows up inside the sandbox at
/mnt/memory/<store-name>/ and the agent reads and writes it with its normal file tools.
"""

from common import BUDGET, client, download_outputs, ensure_environment, load_state, run, save_state, show_cost
from scout import RUBRIC, TASK, scout_agent

MEMORY_INSTRUCTIONS = """seen.md here lists launches you already reported.
At the start, read seen.md (it may not exist yet) and never report anything listed there.
After the brief is final, append one line per reported item: date | title | URL.
Touch no other files here. Keep memory work to those two steps."""


def ensure_memory_store() -> str:
    store_id = load_state().get("memory_store_id")
    if store_id:
        return store_id
    store = client.beta.memory_stores.create(
        name="Scout Memory",
        description="Launches the AI Launch Scout has already reported, one per line in seen.md.",
    )
    save_state(memory_store_id=store.id)
    print(f"Created memory store {store.id}")
    return store.id


MEMORY = {
    "type": "memory_store",
    "memory_store_id": ensure_memory_store(),
    "access": "read_write",
    "instructions": MEMORY_INSTRUCTIONS,
}

if __name__ == "__main__":
    session = client.beta.sessions.create(
        agent=scout_agent(),
        environment_id=ensure_environment(),
        title="Rung 3: run with memory",
        resources=[MEMORY],
        budget=BUDGET,
    )

    run(session.id, kickoff=[
        {"type": "user.define_outcome", "description": TASK, "rubric": {"type": "text", "content": RUBRIC}},
    ])

    download_outputs(session.id)
    show_cost(session.id)

    # Peek at what it remembered. This lives in Anthropic's cloud, not on this laptop.
    print("\nWhat the scout now remembers:")
    for memory in client.beta.memory_stores.memories.list(MEMORY["memory_store_id"], path_prefix="/", view="full"):
        if memory.type == "memory":
            print(f"--- {memory.path}\n{memory.content}")
