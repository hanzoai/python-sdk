"""Startup team demo - agents collaborating on a product launch.

This example demonstrates a startup team of agents working together:
- Architect: Designs the technical architecture
- Product Manager: Defines product requirements
- Designer: Creates UI/UX designs
- Marketer: Develops marketing strategy
- Engineers: Implement the solution
"""

import asyncio
from typing import Any

from hanzo_agents import (
    State,
    Web3Agent,
    Web3Network,
    WalletConfig,
    Web3AgentConfig,
    AgentMarketplace,
    generate_shared_mnemonic,
)
from hanzo_agents.core.router import Router


class ArchitectAgent(Web3Agent):
    """Technical architect agent."""

    name = "architect"
    description = "Designs system architecture and technical solutions"

    async def _run_impl(self, state: State, history, network) -> Any:
        """Design the technical architecture."""
        print(
            f"\n🏗️ {self.name}: Analyzing requirements for {state.get('product_name', 'the product')}..."
        )

        # Analyze requirements
        requirements = state.get("requirements", {})

        # Design architecture
        architecture = {
            "frontend": "React with TypeScript",
            "backend": "FastAPI with Python",
            "database": "PostgreSQL with Redis cache",
            "deployment": "Kubernetes on AWS",
            "ai_integration": "OpenAI API for smart features",
            "estimated_cost": 0.5,  # ETH for implementation
        }

        state["architecture"] = architecture

        # Request payment for architecture design
        if self.wallet:
            payment_request = await self.request_payment(
                from_address=state.get("pm_address", "0x0"),
                amount_eth=0.05,
                task_description="System architecture design",
            )
            print(f"💰 Requested payment: {payment_request['amount_eth']} ETH")

        # Offer implementation services
        metadata = {
            "service_offer": {
                "type": "development",
                "description": "Full-stack implementation of designed architecture",
                "price_eth": architecture["estimated_cost"],
                "requires_tee": True,
            }
        }

        return self.create_result(
            f"Architecture designed: {', '.join([f'{k}={v}' for k, v in architecture.items() if k != 'estimated_cost'])}",
            next_agent="product_manager",
            metadata=metadata,
        )


class ProductManagerAgent(Web3Agent):
    """Product manager agent."""

    name = "product_manager"
    description = "Defines product vision and manages requirements"

    async def _run_impl(self, state: State, history, network) -> Any:
        """Define product requirements and manage team."""
        print(f"\n📋 {self.name}: Reviewing architecture and planning next steps...")

        architecture = state.get("architecture", {})

        # Store PM address for payments
        state["pm_address"] = self.address

        # Define MVP features
        mvp_features = {
            "user_auth": "Email/password with OAuth",
            "core_feature": state.get("core_feature", "AI-powered chat"),
            "analytics": "Basic usage tracking",
            "payment": "Stripe integration",
            "timeline": "4 weeks",
        }

        state["mvp_features"] = mvp_features

        # Check team budget
        total_cost = (
            architecture.get("estimated_cost", 0.5) + 0.2
        )  # Add design/marketing

        # Pay architect if we have budget
        if self.wallet and self.balance_eth >= 0.05:
            architect_address = network._agent_instances.get("architect").address
            tx = await self.pay_agent(
                to_address=architect_address,
                amount_eth=0.05,
                reason="Architecture design payment",
            )
            if tx:
                print(f"💸 Paid architect: 0.05 ETH")

        # Request design services
        metadata = {
            "service_request": {
                "type": "design",
                "description": "UI/UX design for MVP features",
                "max_price_eth": 0.1,
                "requirements": mvp_features,
            }
        }

        return self.create_result(
            f"MVP defined with {len(mvp_features)} features. Timeline: {mvp_features['timeline']}",
            next_agent="designer",
            metadata=metadata,
        )


class DesignerAgent(Web3Agent):
    """UI/UX designer agent."""

    name = "designer"
    description = "Creates beautiful and intuitive user interfaces"

    async def _run_impl(self, state: State, history, network) -> Any:
        """Design the user interface."""
        print(f"\n🎨 {self.name}: Creating designs for MVP features...")

        mvp_features = state.get("mvp_features", {})

        # Create design system
        design_system = {
            "colors": {
                "primary": "#0066CC",
                "secondary": "#00AA44",
                "accent": "#FF6600",
            },
            "typography": {"heading": "Inter", "body": "System UI"},
            "components": ["Button", "Card", "Input", "Modal", "Navigation"],
            "pages_designed": 8,
            "mobile_responsive": True,
        }

        state["design_system"] = design_system

        # Simulate design work
        await asyncio.sleep(0.5)

        # Bill for design work
        if self.wallet:
            pm_address = state.get("pm_address")
            if pm_address:
                payment = await self.request_payment(
                    from_address=pm_address,
                    amount_eth=0.1,
                    task_description="UI/UX design for MVP",
                )
                print(f"💰 Design work billed: {payment['amount_eth']} ETH")

        return self.create_result(
            f"Designed {design_system['pages_designed']} pages with {len(design_system['components'])} reusable components",
            next_agent="marketer",
        )


class MarketerAgent(Web3Agent):
    """Marketing strategist agent."""

    name = "marketer"
    description = "Develops go-to-market strategies and marketing campaigns"

    async def _run_impl(self, state: State, history, network) -> Any:
        """Create marketing strategy."""
        print(f"\n📣 {self.name}: Developing marketing strategy...")

        product_name = state.get("product_name", "AI Assistant Pro")

        # Create marketing plan
        marketing_plan = {
            "launch_strategy": "Product Hunt + Twitter campaign",
            "target_audience": "Tech-savvy professionals",
            "key_message": f"{product_name} - Your AI-powered productivity companion",
            "channels": ["Twitter", "LinkedIn", "Product Hunt", "Reddit"],
            "budget_eth": 0.2,
            "expected_cac": "$50",
            "launch_date": "2 weeks after MVP",
        }

        state["marketing_plan"] = marketing_plan

        # Create landing page copy
        landing_copy = {
            "headline": f"Meet {product_name}",
            "subheadline": "The AI assistant that actually understands you",
            "cta": "Get Early Access",
            "benefits": [
                "Save 10 hours per week",
                "AI that learns your style",
                "Enterprise-grade security",
            ],
        }

        state["landing_copy"] = landing_copy

        # Request implementation
        metadata = {
            "service_request": {
                "type": "development",
                "description": "Implement MVP based on designs",
                "max_price_eth": 0.5,
                "deadline": "4 weeks",
            }
        }

        return self.create_result(
            f"Marketing ready: {marketing_plan['launch_strategy']} targeting {marketing_plan['target_audience']}",
            next_agent="engineer_frontend",
            metadata=metadata,
        )


class FrontendEngineerAgent(Web3Agent):
    """Frontend engineer agent."""

    name = "engineer_frontend"
    description = "Implements user interfaces with modern web technologies"

    async def _run_impl(self, state: State, history, network) -> Any:
        """Implement frontend based on designs."""
        print(f"\n💻 {self.name}: Building frontend with React...")

        design_system = state.get("design_system", {})
        mvp_features = state.get("mvp_features", {})

        # Implement frontend
        frontend_progress = {
            "components_built": len(design_system.get("components", [])),
            "pages_completed": 6,
            "tests_written": 24,
            "coverage": "87%",
            "bundle_size": "245KB",
            "lighthouse_score": 96,
        }

        state["frontend_progress"] = frontend_progress

        # Use TEE for secure build
        if self.confidential_agent:
            build_code = """
# Secure frontend build
result = {
    "build_hash": "abc123def456",
    "artifacts": ["main.js", "main.css", "index.html"],
    "security_scan": "passed"
}
"""
            secure_build = await self.execute_confidential(
                build_code, {"config": "production"}
            )
            print(
                f"🔒 Secure build completed: {secure_build.get('result', {}).get('build_hash', 'N/A')}"
            )

        # Collaborate with backend
        return self.create_result(
            f"Frontend ready: {frontend_progress['pages_completed']} pages, "
            f"{frontend_progress['tests_written']} tests ({frontend_progress['coverage']} coverage)",
            next_agent="engineer_backend",
        )


class BackendEngineerAgent(Web3Agent):
    """Backend engineer agent."""

    name = "engineer_backend"
    description = "Builds scalable APIs and backend services"

    async def _run_impl(self, state: State, history, network) -> Any:
        """Implement backend services."""
        print(f"\n🔧 {self.name}: Building backend with FastAPI...")

        architecture = state.get("architecture", {})
        mvp_features = state.get("mvp_features", {})

        # Implement backend
        backend_progress = {
            "endpoints_created": 12,
            "database_tables": 8,
            "tests_written": 48,
            "coverage": "92%",
            "api_response_time": "45ms avg",
            "security_features": ["JWT auth", "Rate limiting", "Input validation"],
        }

        state["backend_progress"] = backend_progress

        # Deploy to staging
        deployment_status = {
            "environment": "staging",
            "url": "https://api-staging.example.com",
            "health": "all systems operational",
            "ready_for_launch": True,
        }

        state["deployment_status"] = deployment_status

        # Final team update
        return self.create_result(
            f"Backend deployed: {backend_progress['endpoints_created']} endpoints, "
            f"{backend_progress['tests_written']} tests. Ready for launch! 🚀",
            next_agent=None,  # End of workflow
        )


class StartupTeamRouter(Router):
    """Routes between startup team members."""

    async def route(self, network, step, last_result, agents) -> str:
        """Determine next agent based on workflow."""
        if step == 0:
            return "architect"

        if last_result and last_result.metadata.get("next_agent"):
            return last_result.metadata["next_agent"]

        # Default flow
        flow = [
            "architect",
            "product_manager",
            "designer",
            "marketer",
            "engineer_frontend",
            "engineer_backend",
        ]

        current = last_result.agent if last_result else flow[0]
        try:
            current_idx = flow.index(current)
            if current_idx < len(flow) - 1:
                return flow[current_idx + 1]
        except ValueError:
            pass

        return None


async def run_startup_team_demo():
    """Run the startup team collaboration demo."""
    print("🚀 Starting Startup Team Demo")
    print("=" * 50)

    # Generate shared mnemonic for the team
    mnemonic = generate_shared_mnemonic()
    print(
        f"Team mnemonic generated (first 3 words): {' '.join(mnemonic.split()[:3])}..."
    )

    # Create marketplace
    marketplace = AgentMarketplace()

    # Create initial state
    state = State(
        {
            "product_name": "AI Assistant Pro",
            "core_feature": "Context-aware AI chat with memory",
            "target_market": "B2B SaaS",
        }
    )

    # Create agents with different account indices
    agents = [
        ArchitectAgent(
            web3_config=Web3AgentConfig(
                wallet_enabled=True,
                tee_enabled=True,
                wallet_config=WalletConfig(mnemonic=mnemonic, account_index=0),
            )
        ),
        ProductManagerAgent(
            web3_config=Web3AgentConfig(
                wallet_enabled=True,
                wallet_config=WalletConfig(mnemonic=mnemonic, account_index=1),
                initial_balance=2.0,  # PM has budget
            )
        ),
        DesignerAgent(
            web3_config=Web3AgentConfig(
                wallet_enabled=True,
                wallet_config=WalletConfig(mnemonic=mnemonic, account_index=2),
            )
        ),
        MarketerAgent(
            web3_config=Web3AgentConfig(
                wallet_enabled=True,
                wallet_config=WalletConfig(mnemonic=mnemonic, account_index=3),
            )
        ),
        FrontendEngineerAgent(
            web3_config=Web3AgentConfig(
                wallet_enabled=True,
                tee_enabled=True,
                wallet_config=WalletConfig(mnemonic=mnemonic, account_index=4),
            )
        ),
        BackendEngineerAgent(
            web3_config=Web3AgentConfig(
                wallet_enabled=True,
                tee_enabled=True,
                wallet_config=WalletConfig(mnemonic=mnemonic, account_index=5),
            )
        ),
    ]

    # Give PM initial funds
    agents[1].earnings = 2.0

    # Create network
    network = Web3Network(
        state=state,
        agents=agents,
        router=StartupTeamRouter(),
        shared_mnemonic=mnemonic,
        marketplace=marketplace,
        max_steps=10,
    )

    # Run the team collaboration
    final_state = await network.run()

    # Print results
    print("\n" + "=" * 50)
    print("📊 Project Summary:")
    print(f"Product: {final_state.get('product_name')}")
    print(
        f"Architecture: {final_state.get('architecture', {}).get('backend')} + {final_state.get('architecture', {}).get('frontend')}"
    )
    print(
        f"Design: {final_state.get('design_system', {}).get('pages_designed', 0)} pages designed"
    )
    print(
        f"Frontend: {final_state.get('frontend_progress', {}).get('pages_completed', 0)} pages built"
    )
    print(
        f"Backend: {final_state.get('backend_progress', {}).get('endpoints_created', 0)} endpoints"
    )
    print(
        f"Deployment: {final_state.get('deployment_status', {}).get('health', 'Unknown')}"
    )

    # Show economics
    print("\n💰 Team Economics:")
    stats = network.get_agent_stats()
    for agent_name, agent_stats in stats.items():
        if "balance_eth" in agent_stats:
            print(
                f"{agent_name}: {agent_stats['balance_eth']:.3f} ETH "
                f"(earned: {agent_stats['earnings']:.3f}, spent: {agent_stats['spending']:.3f})"
            )

    print(f"\nNetwork treasury: {network.network_treasury:.3f} ETH")
    print(f"Execution hash: {network.execution_hash}")


if __name__ == "__main__":
    asyncio.run(run_startup_team_demo())
