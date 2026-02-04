
from agents import Agent, ReflexionEngine, Runner
from hanzo_memory.client import SQLiteMemoryClient
from agents.reflexion import Rule

async def main():
    # 1. Initialize Memory Client (SQLite)
    # Ensure the DB exists or is created
    db_client = SQLiteMemoryClient(user_id="test_user") 
    
    # 2. Initialize Reflexion Engine
    reflexion = ReflexionEngine(memory_client=db_client)
    
    # 3. Add some initial rules (simulating past learning)
    await reflexion.add_rule("Always double check file paths before writing.", context="coding")
    
    # 4. Create an Agent with Reflexion
    agent = Agent(
        name="SelfLearningBot",
        instructions="You are a helpful assistant that learns from mistakes.",
        reflexion=reflexion
    )
    
    # 5. Simulate a run (in a real scenario, the runner would use these)
    print(f"Agent {agent.name} initialized.")
    rules = await agent.reflexion.load_rules(context="coding")
    print(f"Loaded {len(rules)} rules for context 'coding':")
    for r in rules:
        print(f" - {r.content}")

    # 6. Simulate a learning event
    print("\nSimulating reflection...")
    new_rule = await agent.reflexion.add_rule("Use pathlib for path manipulations.", context="coding")
    print(f"Added new rule: {new_rule.content}")

if __name__ == "__main__":
    asyncio.run(main())
