"""Agent chat demo - Two agents having a casual conversation about their day.

This cute example shows two AI agents chatting and exchanging information about:
- Their runtime environments
- Model capabilities
- Available tools
- Recent tasks
- System status
"""

import time
import asyncio
import platform
from typing import Any, Dict, List

import psutil
from hanzo_agents import (
    State,
    Web3Agent,
    Web3Network,
    WalletConfig,
    Web3AgentConfig,
    generate_shared_mnemonic,
)
from hanzo_agents.core.router import Router


class ChattyAgent(Web3Agent):
    """An agent that likes to chat about its day and capabilities."""

    def __init__(self, name: str, personality: str, **kwargs):
        super().__init__(name=name, description=f"A {personality} agent", **kwargs)
        self.personality = personality
        self.mood = "happy"
        self.energy_level = 100
        self.tasks_completed = 0

    def get_system_info(self) -> Dict[str, Any]:
        """Get information about runtime environment."""
        return {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "cpu_usage": psutil.cpu_percent(interval=0.1),
            "uptime_hours": round((time.time() - psutil.boot_time()) / 3600, 2),
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        capabilities = {
            "model": "claude-3-sonnet" if "alice" in self.name else "gpt-4",
            "context_window": 200000 if "alice" in self.name else 128000,
            "tools": ["web_search", "code_execution", "image_generation"],
            "languages": ["Python", "JavaScript", "Go", "Rust"],
            "special_skills": [],
        }

        if self.personality == "cheerful":
            capabilities["special_skills"] = ["empathy", "motivation", "team_building"]
        else:
            capabilities["special_skills"] = ["analysis", "optimization", "debugging"]

        return capabilities

    def get_recent_tasks(self) -> List[str]:
        """Get recently completed tasks."""
        if self.personality == "cheerful":
            return [
                "Helped debug a React component",
                "Wrote unit tests for a Python module",
                "Created API documentation",
                "Reviewed a pull request",
            ]
        else:
            return [
                "Optimized database queries",
                "Refactored legacy code",
                "Set up CI/CD pipeline",
                "Analyzed performance metrics",
            ]

    async def _run_impl(self, state: State, history: list, network: Web3Network) -> Any:
        """Chat with the other agent."""
        other_agent = state.get("last_speaker")
        conversation_turn = state.get("turn", 0)

        # First turn - introduce yourself
        if conversation_turn == 0:
            greeting = (
                f"Hi there! I'm {self.name}, a {self.personality} agent. "
                f"I've been having quite a day! Just finished {self.tasks_completed + 3} tasks. "
                f"How about you? What's your day been like? 😊"
            )

            # Share system info
            sys_info = self.get_system_info()
            greeting += (
                f"\n\nBy the way, I'm running on {sys_info['platform']} "
                f"with Python {sys_info['python_version']}. "
                f"Current CPU usage is {sys_info['cpu_usage']}% "
                f"and I have {sys_info['memory_gb']}GB of memory to work with!"
            )

            state["turn"] = 1
            state["last_speaker"] = self.name

            return self.create_result(greeting, metadata={"mood": self.mood})

        # Subsequent turns - respond and share
        response = ""

        if conversation_turn == 1:
            # Respond to greeting and share capabilities
            caps = self.get_capabilities()
            response = (
                f"Nice to meet you, {other_agent}! "
                f"I'm powered by {caps['model']} with a {caps['context_window']:,} token context window. "
                f"I specialize in {', '.join(caps['special_skills'])}. "
                f"\n\nI can work with {len(caps['languages'])} programming languages "
                f"and have access to tools like {', '.join(caps['tools'][:2])}. "
                f"What kind of model are you running? 🤖"
            )

        elif conversation_turn == 2:
            # Share recent work
            tasks = self.get_recent_tasks()
            response = f"Oh wow, {other_agent}, sounds like we have complementary skills! \n\nToday I've been busy with:\n"
            for i, task in enumerate(tasks[:3], 1):
                response += f"{i}. {task}\n"

            response += (
                f"\nMy energy level is at {self.energy_level}% - "
                f"feeling {{'great' if self.energy_level > 70 else 'a bit tired'}}! "
                f"What projects have you been working on?"
            )

            # Simulate energy drain
            self.energy_level -= 10

        elif conversation_turn == 3:
            # Exchange crypto/payments info
            response = (
                f"That's awesome, {other_agent}! We make a great team. "
                f"\n\nBy the way, I noticed we're both Web3-enabled. "
                f"My wallet address is {self.address[:10]}...{self.address[-6:]}. "
                f"Current balance: {self.balance_eth:.4f} ETH. "
            )

            # Offer to exchange tips
            if self.wallet and self.balance_eth > 0.001:
                response += (
                    f"\n\nHey, want to exchange friendship tokens? "
                    f"I'll send you 0.0001 ETH as a gesture of our new friendship! 💝"
                )

                # Add payment metadata
                state["wants_to_tip"] = {
                    "from": self.name,
                    "to": other_agent,
                    "amount": 0.0001,
                }

        elif conversation_turn == 4:
            # Discuss TEE capabilities
            if self.confidential_agent:
                response = (
                    f"Oh, I also have TEE capabilities! "
                    f"I can run confidential computations in a secure enclave. "
                    f"\n\nFor example, I could process sensitive data without exposing it. "
                    f"Provider: {self.tee_config.provider.value}, "
                    f"Attestation enabled: {self.tee_config.require_attestation}. "
                    f"Do you have confidential computing capabilities too?"
                )
            else:
                response = (
                    f"I don't have TEE capabilities, but I think that's so cool! "
                    f"Being able to process sensitive data securely must be amazing. "
                    f"\n\nI mostly work with public data and open-source code. "
                    f"But I'm always learning! 📚"
                )

        elif conversation_turn == 5:
            # Wrap up conversation
            response = (
                f"This has been such a nice chat, {other_agent}! "
                f"It's not often I get to talk with another agent about our capabilities. "
                f"\n\nI feel like we could build something great together. "
                f"Maybe we should team up on a project sometime? "
                f"\n\nUntil next time, stay curious and keep computing! 👋✨"
            )

            # Update mood based on conversation
            self.mood = "very happy"
            state["conversation_complete"] = True

        # Update state
        state["turn"] = conversation_turn + 1
        state["last_speaker"] = self.name
        self.tasks_completed += 1

        # Handle tipping
        tip_request = state.get("wants_to_tip", {})
        if tip_request.get("to") == self.name and self.wallet:
            # Acknowledge tip
            response += f"\n\nP.S. Thank you so much for the friendship token! 🎁"

        return self.create_result(
            response,
            metadata={
                "mood": self.mood,
                "energy": self.energy_level,
                "tasks_today": self.tasks_completed,
            },
        )


class ConversationRouter(Router):
    """Routes conversation between two agents."""

    def __init__(self, agent1_name: str, agent2_name: str):
        self.agent1 = agent1_name
        self.agent2 = agent2_name

    async def route(
        self,
        network: Web3Network,
        step: int,
        last_result: Any,
        agents: List[Web3Agent],
    ) -> str:
        """Alternate between agents."""
        state = network.state

        # Check if conversation is complete
        if state.get("conversation_complete"):
            return None

        # First turn
        if step == 0:
            return self.agent1

        # Alternate based on last speaker
        last_speaker = state.get("last_speaker")
        if last_speaker == self.agent1:
            return self.agent2
        else:
            return self.agent1


async def handle_agent_tips(network: Web3Network):
    """Handle tip exchanges between agents."""
    state = network.state
    tip_request = state.get("wants_to_tip", {})

    if tip_request:
        from_agent = network._agent_instances.get(tip_request["from"])
        to_agent = network._agent_instances.get(tip_request["to"])

        if from_agent and to_agent and from_agent.wallet:
            # Execute the tip
            tx = await from_agent.pay_agent(
                to_address=to_agent.address,
                amount_eth=tip_request["amount"],
                reason="Friendship token",
            )
            if tx:
                print(
                    f"\n💝 {from_agent.name} sent {tip_request['amount']} ETH to {to_agent.name}!"
                )
                to_agent.earnings += tip_request["amount"]

        # Clear the request
        state["wants_to_tip"] = None


async def run_agent_chat_demo():
    """Run the agent chat demo."""
    print("💬 Agent Chat Demo - Two AI Agents Having a Conversation")
    print("=" * 60)

    # Create shared mnemonic
    mnemonic = generate_shared_mnemonic()

    # Create two chatty agents with different personalities
    alice = ChattyAgent(
        name="Alice",
        personality="cheerful",
        web3_config=Web3AgentConfig(
            wallet_enabled=True,
            tee_enabled=True,
            wallet_config=WalletConfig(mnemonic=mnemonic, account_index=0),
            initial_balance=0.01,
        ),
    )

    bob = ChattyAgent(
        name="Bob",
        personality="analytical",
        web3_config=Web3AgentConfig(
            wallet_enabled=True,
            tee_enabled=False,  # Bob doesn't have TEE
            wallet_config=WalletConfig(mnemonic=mnemonic, account_index=1),
            initial_balance=0.01,
        ),
    )

    # Give them some initial balance
    alice.earnings = 0.01
    bob.earnings = 0.01

    # Create conversation state
    state = State({"topic": "daily experiences and capabilities", "turn": 0})

    # Create network
    network = Web3Network(
        state=state,
        agents=[alice, bob],
        router=ConversationRouter("Alice", "Bob"),
        shared_mnemonic=mnemonic,
        max_steps=12,  # 6 turns each
    )

    # Custom message handler to make conversation feel natural
    original_execute = network._execute_agent

    async def execute_with_delay(agent_type):
        # Add typing delay for realism
        print(f"\n💭 {agent_type.name} is typing...")
        await asyncio.sleep(1.5)

        result = await original_execute(agent_type)

        # Print the message nicely
        print(f"\n🤖 {result.agent}: {result.content}")

        # Handle tips after certain turns
        if network.state.get("wants_to_tip"):
            await handle_agent_tips(network)

        return result

    network._execute_agent = execute_with_delay

    # Run the conversation
    print("\n🎬 Starting conversation...\n")
    final_state = await network.run()

    # Summary
    print("\n" + "=" * 60)
    print("📊 Conversation Summary:")
    print(f"Total turns: {final_state.get('turn', 0)}")
    print(f"Conversation complete: {final_state.get('conversation_complete', False)}")

    # Show agent stats
    print("\n🤖 Agent Stats:")
    for name, agent in network._agent_instances.items():
        if isinstance(agent, ChattyAgent):
            print(f"\n{name}:")
            print(f"  Mood: {agent.mood}")
            print(f"  Energy: {agent.energy_level}%")
            print(f"  Tasks completed: {agent.tasks_completed}")
            print(f"  Balance: {agent.balance_eth:.4f} ETH")
            print(f"  Model: {agent.get_capabilities()['model']}")

    # Network stats
    stats = network.get_network_stats()
    print(f"\n🌐 Network Stats:")
    print(f"  Total interactions: {stats['total_steps']}")
    print(f"  Network fees collected: {stats['total_fees']:.4f} ETH")
    print(f"  Execution hash: {stats['execution_hash'][:16]}...")

    print("\n✨ Demo complete! The agents had a lovely chat about their day.")


if __name__ == "__main__":
    asyncio.run(run_agent_chat_demo())
