"""agent — define one, run it, read the run back.

    POST /v1/agents            post_agents
    POST /v1/agents/{ref}/run  post_agents_by_ref_run
    GET  /v1/agents/{ref}/runs get_agents_by_ref_runs

``ref`` is the agent's public id (``agent_...``) OR its org-unique name, which
is why the run and the read below can both use the name we just created without
waiting for an id to come back.

The read-back is the RUN list rather than the agent record: an agent you just
created tells you nothing you did not just send, while its runs are the part the
server actually produced.

    python -m examples.agent
"""

import time

from hanzoai.cloud import AgentsApi, CreateAgentIn

from examples.client import MODEL, client, run

# Org-unique: a fixed name collides with itself on the second run.
NAME = f"example-greeter-{time.time_ns()}"


def main() -> None:
    with client() as api:
        agents = AgentsApi(api)

        created = agents.post_agents(
            CreateAgentIn(
                name=NAME,
                model=MODEL,
                description="Created by the hanzoai SDK agent example.",
                instructions="You greet the user in one short sentence.",
            )
        )
        print(f"created {created.name} ({created.id}) on {created.model}")

        agents.post_agents_by_ref_run(NAME)
        print("run started")

        runs = agents.get_agents_by_ref_runs(NAME, limit=5)
        entries = runs.runs or []
        print(f"{len(entries)} run(s):")
        for entry in entries:
            print(f"  {entry.to_str()}")


if __name__ == "__main__":
    run(main)
