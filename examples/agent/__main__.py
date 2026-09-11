"""agent — define one, run it, read the run back.

    POST /v1/agent            post_agent
    POST /v1/agent/{ref}/run  post_agent_by_ref_run
    GET  /v1/agent/runs       get_agent_runs

``ref`` is the agent's public id (``agent_...``) OR its org-unique name, which
is why the run below can use the name we just created without waiting for an id
to come back.

The read-back is the RUN list rather than the agent record: an agent you just
created tells you nothing you did not just send, while its runs are the part the
server actually produced. It reads the org's run feed and keeps this agent's
rows, because the document declares ``GET /v1/agent/{ref}/runs`` without its
``ref`` parameter and the generated method cannot take one.

    python -m examples.agent
"""

import time

from hanzoai.cloud import AgentApi, CreateAgentIn

from examples.client import MODEL, client, run

# Org-unique: a fixed name collides with itself on the second run.
NAME = f"example-greeter-{time.time_ns()}"


def main() -> None:
    with client() as api:
        agents = AgentApi(api)

        created = agents.post_agent(
            CreateAgentIn(
                name=NAME,
                model=MODEL,
                description="Created by the hanzoai SDK agent example.",
                instructions="You greet the user in one short sentence.",
            )
        )
        print(f"created {created.name} ({created.id}) on {created.model}")

        agents.post_agent_by_ref_run(NAME)
        print("run started")

        entries = [r for r in agents.get_agent_runs().runs or [] if r.agent == NAME][:5]
        print(f"{len(entries)} run(s):")
        for entry in entries:
            print(f"  {entry.to_str()}")


if __name__ == "__main__":
    run(main)
