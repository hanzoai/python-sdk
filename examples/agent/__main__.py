"""agent — define one, run it, read it back.

    POST /v1/agents            cloud_AgentsController.Create
    POST /v1/agents/{ref}/run  cloud_AgentsController.Run
    GET  /v1/agents/{ref}      cloud_AgentsController.Get

``ref`` is the agent's public id (``agent_...``) OR its org-unique name, which
is why the run and the read below can both use the name we just created without
waiting for an id to come back.

    python -m examples.agent
"""

import time

from hanzoai.cloud import AgentsAPIApi, CloudAgentsCreateAgentRequest, CloudAgentsRunRequest

from examples.client import MODEL, client, run

# Org-unique: a fixed name collides with itself on the second run.
NAME = f"example-greeter-{time.time_ns()}"


def main() -> None:
    with client() as api:
        agents = AgentsAPIApi(api)

        created = agents.cloud_agents_controller_create(
            CloudAgentsCreateAgentRequest(
                name=NAME,
                model=MODEL,
                description="Created by the hanzoai SDK agent example.",
                instructions="You greet the user in one short sentence.",
            )
        )
        print("created:", created)

        run_result = agents.cloud_agents_controller_run(
            NAME, CloudAgentsRunRequest(input="Greet a new Hanzo user.")
        )
        print("run:", run_result)

        print("read back:", agents.cloud_agents_controller_get(NAME))


if __name__ == "__main__":
    run(main)
