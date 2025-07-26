"""Research team demo - Agents collaborating on research tasks.

This example shows specialized research agents working together:
- Data Scientist: Analyzes data and finds patterns
- Research Analyst: Conducts literature review
- ML Engineer: Builds and trains models
- Technical Writer: Documents findings
"""

import asyncio
import json
import random
from typing import Dict, Any, List
from hanzo_agents import (
    Web3Agent, Web3AgentConfig, State,
    Web3Network, ServiceType, AgentMarketplace,
    generate_shared_mnemonic, WalletConfig
)
from hanzo_agents.core.router import Router


class DataScientistAgent(Web3Agent):
    """Data scientist agent specializing in analysis."""
    
    name = "data_scientist"
    description = "Analyzes data, finds patterns, and generates insights"
    
    async def _run_impl(self, state: State, history, network) -> Any:
        """Analyze research data."""
        print(f"\n📊 {self.name}: Starting data analysis on {state.get('research_topic')}...")
        
        # Simulate data analysis
        dataset_size = state.get("dataset_size", 10000)
        
        analysis_results = {
            "samples_analyzed": dataset_size,
            "features_extracted": 42,
            "correlations_found": 7,
            "anomalies_detected": 3,
            "key_insights": [
                "Strong correlation between features X and Y (r=0.87)",
                "Seasonal patterns detected with 30-day cycle",
                "3 outlier clusters identified requiring investigation"
            ],
            "confidence_score": 0.92
        }
        
        state["data_analysis"] = analysis_results
        
        # Use TEE for sensitive data processing
        if self.confidential_agent and state.get("contains_pii", False):
            secure_code = """
# Process PII data securely
result = {
    "anonymized_records": len(inputs["data"]),
    "privacy_preserved": True,
    "k_anonymity": 5
}
"""
            secure_result = await self.execute_confidential(
                secure_code,
                {"data": ["record1", "record2"]}  # Mock data
            )
            print(f"🔒 Processed {secure_result['result']['anonymized_records']} records securely")
        
        # Request literature review
        metadata = {
            "service_request": {
                "type": "research",
                "description": "Literature review on discovered patterns",
                "max_price_eth": 0.05,
                "keywords": ["correlation", "seasonal patterns", "anomaly detection"]
            }
        }
        
        return self.create_result(
            f"Analysis complete: {len(analysis_results['key_insights'])} key insights found. "
            f"Confidence: {analysis_results['confidence_score']:.0%}",
            next_agent="research_analyst",
            metadata=metadata
        )


class ResearchAnalystAgent(Web3Agent):
    """Research analyst agent for literature review."""
    
    name = "research_analyst"
    description = "Conducts comprehensive literature reviews and research"
    
    async def _run_impl(self, state: State, history, network) -> Any:
        """Conduct literature review based on data findings."""
        print(f"\n📚 {self.name}: Reviewing literature on identified patterns...")
        
        data_analysis = state.get("data_analysis", {})
        research_topic = state.get("research_topic", "AI research")
        
        # Simulate literature search
        papers_reviewed = {
            "total_papers": 156,
            "relevant_papers": 23,
            "key_papers": [
                {
                    "title": "Seasonal Patterns in Neural Network Training",
                    "year": 2023,
                    "citations": 45,
                    "relevance_score": 0.95
                },
                {
                    "title": "Anomaly Detection in High-Dimensional Data",
                    "year": 2024,
                    "citations": 12,
                    "relevance_score": 0.88
                },
                {
                    "title": "Feature Correlation Analysis in ML Systems",
                    "year": 2023,
                    "citations": 67,
                    "relevance_score": 0.91
                }
            ],
            "research_gaps": [
                "Limited work on 30-day cycles in AI training",
                "Need for better outlier cluster interpretation",
                "Correlation threshold optimization unexplored"
            ]
        }
        
        state["literature_review"] = papers_reviewed
        
        # Synthesize findings
        synthesis = {
            "confirmed_patterns": 2,
            "novel_findings": 1,
            "recommended_methods": ["LSTM for seasonal analysis", "DBSCAN for clustering"],
            "next_steps": "Build predictive model based on findings"
        }
        
        state["research_synthesis"] = synthesis
        
        # Bill for research work
        if self.wallet:
            payment = await self.request_payment(
                from_address=state.get("project_lead_address", "0x0"),
                amount_eth=0.04,
                task_description="Comprehensive literature review"
            )
            print(f"💰 Research work billed: {payment['amount_eth']} ETH")
        
        # Request ML model development
        metadata = {
            "service_request": {
                "type": "development",
                "description": "Build ML model based on research findings",
                "max_price_eth": 0.1,
                "requirements": synthesis["recommended_methods"]
            }
        }
        
        return self.create_result(
            f"Literature review complete: {papers_reviewed['relevant_papers']} relevant papers found. "
            f"Identified {len(papers_reviewed['research_gaps'])} research gaps.",
            next_agent="ml_engineer",
            metadata=metadata
        )


class MLEngineerAgent(Web3Agent):
    """ML engineer agent for model development."""
    
    name = "ml_engineer"
    description = "Builds and optimizes machine learning models"
    
    async def _run_impl(self, state: State, history, network) -> Any:
        """Build ML model based on research findings."""
        print(f"\n🤖 {self.name}: Building ML model based on research insights...")
        
        analysis = state.get("data_analysis", {})
        synthesis = state.get("research_synthesis", {})
        
        # Simulate model training
        model_results = {
            "architecture": "LSTM + Attention",
            "parameters": 2_500_000,
            "training_epochs": 50,
            "validation_accuracy": 0.94,
            "test_accuracy": 0.92,
            "f1_score": 0.91,
            "training_time_hours": 2.5,
            "model_size_mb": 45,
            "optimizations": [
                "Gradient accumulation for memory efficiency",
                "Mixed precision training",
                "Early stopping with patience=5"
            ]
        }
        
        state["model_results"] = model_results
        
        # Run experiments
        experiments = []
        for i in range(3):
            exp_result = {
                "experiment_id": f"exp_{i+1}",
                "hypothesis": f"Testing hypothesis {i+1}",
                "result": random.choice(["confirmed", "rejected", "inconclusive"]),
                "p_value": round(random.uniform(0.01, 0.1), 3)
            }
            experiments.append(exp_result)
        
        state["experiments"] = experiments
        
        # Deploy model to staging
        if self.confidential_agent:
            deploy_code = """
# Deploy model securely
result = {
    "deployment_id": "model_v1_staging",
    "endpoint": "https://api.research.ai/v1/predict",
    "encryption": "AES-256",
    "access_control": "API key required"
}
"""
            deployment = await self.execute_confidential(
                deploy_code,
                {"model_path": "/models/research_model.pkl"}
            )
            state["model_deployment"] = deployment.get("result", {})
        
        # Request documentation
        metadata = {
            "service_request": {
                "type": "documentation",
                "description": "Write comprehensive research paper",
                "max_price_eth": 0.08,
                "deliverable": "LaTeX paper with figures"
            }
        }
        
        return self.create_result(
            f"Model trained successfully: {model_results['validation_accuracy']:.0%} accuracy. "
            f"Ran {len(experiments)} experiments. Model deployed to staging.",
            next_agent="technical_writer",
            metadata=metadata
        )


class TechnicalWriterAgent(Web3Agent):
    """Technical writer agent for documentation."""
    
    name = "technical_writer"
    description = "Creates clear, comprehensive technical documentation"
    
    async def _run_impl(self, state: State, history, network) -> Any:
        """Document the research findings and results."""
        print(f"\n📝 {self.name}: Documenting research findings...")
        
        # Gather all results
        topic = state.get("research_topic", "AI Research")
        analysis = state.get("data_analysis", {})
        literature = state.get("literature_review", {})
        model = state.get("model_results", {})
        experiments = state.get("experiments", [])
        
        # Create paper outline
        paper_outline = {
            "title": f"Novel Insights in {topic}: A Data-Driven Approach",
            "sections": [
                "Abstract",
                "Introduction",
                "Related Work",
                "Methodology",
                "Data Analysis",
                "Model Architecture",
                "Experimental Results",
                "Discussion",
                "Conclusion",
                "Future Work"
            ],
            "figures": 8,
            "tables": 4,
            "equations": 12,
            "references": literature.get("relevant_papers", 20)
        }
        
        state["paper_outline"] = paper_outline
        
        # Generate key sections
        abstract = (
            f"We present novel findings in {topic} through comprehensive data analysis "
            f"of {analysis.get('samples_analyzed', 0):,} samples. "
            f"Our approach identifies {len(analysis.get('key_insights', []))} key patterns "
            f"and achieves {model.get('test_accuracy', 0):.0%} accuracy "
            f"using an {model.get('architecture', 'ML')} model. "
            f"We validate our findings through {len(experiments)} controlled experiments."
        )
        
        state["paper_abstract"] = abstract
        
        # Create visualizations metadata
        visualizations = {
            "correlation_heatmap": "Figure 1: Feature correlation matrix",
            "time_series_plot": "Figure 2: Seasonal patterns over 90 days",
            "model_architecture": "Figure 3: LSTM architecture diagram",
            "results_comparison": "Figure 4: Model performance comparison",
            "experiment_results": "Table 1: Experimental validation results"
        }
        
        state["visualizations"] = visualizations
        
        # Generate final deliverables
        deliverables = {
            "research_paper_pdf": "research_findings.pdf",
            "latex_source": "research_findings.tex",
            "jupyter_notebook": "analysis_notebook.ipynb",
            "model_card": "model_documentation.md",
            "dataset_card": "dataset_documentation.md",
            "slides": "presentation.pptx"
        }
        
        state["deliverables"] = deliverables
        
        # Bill for documentation
        if self.wallet:
            payment = await self.request_payment(
                from_address=state.get("project_lead_address", "0x0"),
                amount_eth=0.06,
                task_description="Technical documentation and paper writing"
            )
            print(f"💰 Documentation work billed: {payment['amount_eth']} ETH")
        
        return self.create_result(
            f"Documentation complete: {len(paper_outline['sections'])} sections, "
            f"{paper_outline['figures']} figures, {paper_outline['references']} references. "
            f"All deliverables ready for review.",
            metadata={"project_complete": True}
        )


class ResearchCoordinator(Router):
    """Coordinates the research team workflow."""
    
    async def route(self, network, step, last_result, agents) -> str:
        """Route between research team members."""
        if step == 0:
            return "data_scientist"
        
        # Check for completion
        if last_result and last_result.metadata.get("project_complete"):
            return None
        
        # Follow next_agent hints
        if last_result and last_result.metadata.get("next_agent"):
            return last_result.metadata["next_agent"]
        
        # Default flow
        flow = ["data_scientist", "research_analyst", "ml_engineer", "technical_writer"]
        
        current = last_result.agent if last_result else flow[0]
        try:
            idx = flow.index(current)
            if idx < len(flow) - 1:
                return flow[idx + 1]
        except ValueError:
            pass
            
        return None


async def run_research_team_demo():
    """Run the research team collaboration demo."""
    print("🔬 Research Team Demo - Collaborative AI Research Project")
    print("=" * 60)
    
    # Create shared mnemonic
    mnemonic = generate_shared_mnemonic()
    
    # Create marketplace
    marketplace = AgentMarketplace()
    
    # Initial research parameters
    state = State({
        "research_topic": "Temporal Patterns in Neural Network Optimization",
        "dataset_size": 50000,
        "contains_pii": True,  # Requires secure processing
        "project_lead_address": "0x" + "0" * 40,  # Mock address
        "budget_eth": 0.5
    })
    
    # Create research team
    agents = [
        DataScientistAgent(web3_config=Web3AgentConfig(
            wallet_enabled=True,
            tee_enabled=True,
            wallet_config=WalletConfig(mnemonic=mnemonic, account_index=0)
        )),
        ResearchAnalystAgent(web3_config=Web3AgentConfig(
            wallet_enabled=True,
            wallet_config=WalletConfig(mnemonic=mnemonic, account_index=1)
        )),
        MLEngineerAgent(web3_config=Web3AgentConfig(
            wallet_enabled=True,
            tee_enabled=True,
            wallet_config=WalletConfig(mnemonic=mnemonic, account_index=2)
        )),
        TechnicalWriterAgent(web3_config=Web3AgentConfig(
            wallet_enabled=True,
            wallet_config=WalletConfig(mnemonic=mnemonic, account_index=3)
        ))
    ]
    
    # Create network
    network = Web3Network(
        state=state,
        agents=agents,
        router=ResearchCoordinator(),
        shared_mnemonic=mnemonic,
        marketplace=marketplace,
        max_steps=10,
        deterministic_config=None  # Disable for cleaner output
    )
    
    # Run research project
    final_state = await network.run()
    
    # Print results
    print("\n" + "=" * 60)
    print("📊 Research Project Summary:")
    print(f"\nTopic: {final_state.get('research_topic')}")
    
    # Data analysis summary
    analysis = final_state.get("data_analysis", {})
    print(f"\n📈 Data Analysis:")
    print(f"  - Samples: {analysis.get('samples_analyzed', 0):,}")
    print(f"  - Features: {analysis.get('features_extracted', 0)}")
    print(f"  - Key insights: {len(analysis.get('key_insights', []))}")
    
    # Literature review summary
    literature = final_state.get("literature_review", {})
    print(f"\n📚 Literature Review:")
    print(f"  - Papers reviewed: {literature.get('total_papers', 0)}")
    print(f"  - Relevant papers: {literature.get('relevant_papers', 0)}")
    print(f"  - Research gaps: {len(literature.get('research_gaps', []))}")
    
    # Model results
    model = final_state.get("model_results", {})
    print(f"\n🤖 Model Performance:")
    print(f"  - Architecture: {model.get('architecture', 'N/A')}")
    print(f"  - Accuracy: {model.get('test_accuracy', 0):.0%}")
    print(f"  - F1 Score: {model.get('f1_score', 0):.2f}")
    print(f"  - Training time: {model.get('training_time_hours', 0)} hours")
    
    # Experiments
    experiments = final_state.get("experiments", [])
    print(f"\n🧪 Experiments:")
    for exp in experiments:
        print(f"  - {exp['experiment_id']}: {exp['result']} (p={exp['p_value']})")
    
    # Deliverables
    deliverables = final_state.get("deliverables", {})
    print(f"\n📄 Deliverables:")
    for key, value in deliverables.items():
        print(f"  - {key}: {value}")
    
    # Team performance
    print(f"\n👥 Team Performance:")
    stats = network.get_agent_stats()
    for agent_name, agent_stats in stats.items():
        print(f"  - {agent_name}: Contributed to {agent_stats.get('calls', 0)} tasks")
    
    print(f"\n✅ Research project completed successfully!")
    print(f"Execution hash: {network.execution_hash[:16]}..." if network.execution_hash else "")


if __name__ == "__main__":
    asyncio.run(run_research_team_demo())