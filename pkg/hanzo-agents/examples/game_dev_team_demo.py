"""Game development team demo - Agents building a game together.

This example shows game dev agents collaborating:
- Game Designer: Creates game concepts and mechanics
- Artist: Designs visuals and assets
- Programmer: Implements game logic
- Sound Designer: Creates audio
- QA Tester: Tests and finds bugs
"""

import asyncio
from typing import Any

from hanzo_agents import (
    State,
    Web3Agent,
    Web3Network,
    WalletConfig,
    Web3AgentConfig,
    generate_shared_mnemonic,
)
from hanzo_agents.core.router import Router


class GameDesignerAgent(Web3Agent):
    """Game designer creating concepts and mechanics."""

    name = "game_designer"
    description = "Creates engaging game concepts and balanced mechanics"

    async def _run_impl(self, state: State, history, network) -> Any:
        """Design the game concept."""
        print(f"\n🎮 {self.name}: Designing a new game concept...")

        # Create game concept
        game_concept = {
            "title": "Quantum Maze Runner",
            "genre": "Puzzle/Platformer",
            "theme": "Sci-fi quantum mechanics",
            "core_mechanic": "Phase through dimensions to solve puzzles",
            "target_audience": "Casual to mid-core gamers",
            "platform": "Web/Mobile",
            "monetization": "Free-to-play with cosmetic purchases",
        }

        # Design core gameplay
        gameplay = {
            "player_abilities": [
                "Quantum jump between dimensions",
                "Time rewind (limited uses)",
                "Phase through certain walls",
                "Create quantum entanglements",
            ],
            "level_structure": "50 levels across 5 dimensions",
            "difficulty_curve": "Gradual with spikes every 10 levels",
            "session_length": "3-5 minutes per level",
            "retention_hooks": [
                "Daily challenges",
                "Leaderboards",
                "Collectible quantum particles",
                "Story snippets after each dimension",
            ],
        }

        state["game_concept"] = game_concept
        state["gameplay_design"] = gameplay

        # Create detailed GDD excerpt
        gdd_excerpt = {
            "controls": {
                "mobile": "Swipe to move, tap to jump, hold to phase",
                "web": "Arrow keys/WASD + Space + Shift",
            },
            "progression": "Linear with optional bonus levels",
            "rewards": "Stars (1-3 per level), Quantum particles, Skins",
        }

        state["gdd_excerpt"] = gdd_excerpt

        # Request art concepts
        metadata = {
            "service_offer": {
                "type": "design",
                "description": "Game design consultation",
                "price_eth": 0.05,
            },
            "next_agent": "artist",
        }

        return self.create_result(
            f"Game concept ready: '{game_concept['title']}' - "
            f"A {game_concept['genre']} with {len(gameplay['player_abilities'])} unique abilities",
            metadata=metadata,
        )


class ArtistAgent(Web3Agent):
    """Artist creating game visuals."""

    name = "artist"
    description = "Creates stunning game art and visual assets"

    async def _run_impl(self, state: State, history, network) -> Any:
        """Create art concepts and assets."""
        print(
            f"\n🎨 {self.name}: Creating visual concepts for {state['game_concept']['title']}..."
        )

        game_concept = state.get("game_concept", {})

        # Define art style
        art_style = {
            "visual_style": "Low-poly with neon accents",
            "color_palette": {
                "primary": ["#00FFFF", "#FF00FF", "#FFFF00"],  # Cyan, Magenta, Yellow
                "secondary": ["#0088FF", "#FF0088", "#88FF00"],
                "background": ["#0A0A0A", "#1A1A2E", "#16213E"],
            },
            "inspiration": "Tron meets Monument Valley",
            "shader_effects": ["Holographic", "Glitch", "Particle trails"],
        }

        # Create asset list
        assets_created = {
            "characters": {
                "player": "Quantum explorer with shifting form",
                "npcs": ["Guide hologram", "Quantum cats", "Time echoes"],
            },
            "environments": {
                "dimension_1": "Neon grid world",
                "dimension_2": "Fractured reality",
                "dimension_3": "Quantum forest",
                "dimension_4": "Time streams",
                "dimension_5": "The Void",
            },
            "ui_elements": {
                "buttons": 12,
                "icons": 24,
                "backgrounds": 5,
                "fonts": ["Quantum Sans", "Digital Mono"],
            },
            "particles": {
                "quantum_jump": "Blue spiral effect",
                "phase_shift": "Purple dissolve",
                "time_rewind": "Golden trails",
                "entanglement": "Connected light beams",
            },
        }

        state["art_style"] = art_style
        state["game_assets"] = assets_created

        # Simulate asset creation
        await asyncio.sleep(0.5)

        # Generate sprite sheets
        sprite_sheets = {
            "player_animations": ["idle", "walk", "jump", "phase", "death"],
            "enemy_animations": ["patrol", "alert", "attack"],
            "total_frames": 120,
            "format": "PNG with transparency",
            "resolution": "128x128 per frame",
        }

        state["sprite_sheets"] = sprite_sheets

        # Bill for art
        if self.wallet:
            payment = await self.request_payment(
                from_address=state.get("producer_address", self.address),
                amount_eth=0.08,
                task_description="Game art and asset creation",
            )
            print(f"💰 Art assets delivered, invoiced: {payment['amount_eth']} ETH")

        metadata = {"next_agent": "programmer"}

        return self.create_result(
            f"Art complete: {len(assets_created['environments'])} environments, "
            f"{sprite_sheets['total_frames']} animation frames",
            metadata=metadata,
        )


class ProgrammerAgent(Web3Agent):
    """Programmer implementing game logic."""

    name = "programmer"
    description = "Codes game mechanics and implements features"

    async def _run_impl(self, state: State, history, network) -> Any:
        """Implement the game code."""
        print(f"\n💻 {self.name}: Implementing game mechanics...")

        gameplay = state.get("gameplay_design", {})
        assets = state.get("game_assets", {})

        # Implementation details
        implementation = {
            "engine": "Phaser 3",
            "language": "TypeScript",
            "architecture": "ECS (Entity Component System)",
            "modules": {
                "core": ["GameManager", "StateManager", "SaveSystem"],
                "physics": ["QuantumPhysics", "DimensionShift", "Collision"],
                "rendering": ["ParticleSystem", "ShaderManager", "LightingEngine"],
                "gameplay": ["PlayerController", "LevelLoader", "PuzzleManager"],
                "ui": ["MenuSystem", "HUD", "DialogueManager"],
            },
            "total_loc": 8500,
            "test_coverage": "82%",
        }

        state["implementation"] = implementation

        # Code key systems
        code_systems = {
            "quantum_mechanics": {
                "phase_shift": "Implemented with state interpolation",
                "dimension_swap": "Seamless transition with fade effect",
                "entanglement": "Physics bodies linked across dimensions",
            },
            "puzzle_system": {
                "types": ["Switch", "Pressure", "Timing", "Pattern", "Quantum"],
                "solver": "A* pathfinding with quantum states",
                "hint_system": "Progressive hints after 3 failed attempts",
            },
            "save_system": {
                "method": "LocalStorage with cloud backup",
                "data": ["Progress", "Collectibles", "Settings", "Achievements"],
            },
        }

        state["code_systems"] = code_systems

        # Performance metrics
        performance = {
            "target_fps": 60,
            "achieved_fps": 58,
            "load_time": "2.3 seconds",
            "memory_usage": "45MB average",
            "battery_impact": "Low",
            "optimization_level": "High",
        }

        state["performance_metrics"] = performance

        # Deploy to test environment
        if self.confidential_agent:
            deploy_code = """
# Deploy game to test server
result = {
    "build_id": "quantum_maze_v0.9",
    "test_url": "https://test.quantummaze.game",
    "api_endpoint": "wss://api.quantummaze.game",
    "cdn_assets": "https://cdn.quantummaze.game"
}
"""
            deployment = await self.execute_confidential(
                deploy_code, {"env": "staging"}
            )
            state["test_deployment"] = deployment.get("result", {})

        metadata = {
            "service_request": {
                "type": "testing",
                "description": "QA testing and bug hunting",
                "max_price_eth": 0.06,
            },
            "next_agent": "sound_designer",
        }

        return self.create_result(
            f"Game implemented: {implementation['total_loc']} lines of code, "
            f"{len(implementation['modules'])} modules, {performance['achieved_fps']} FPS",
            metadata=metadata,
        )


class SoundDesignerAgent(Web3Agent):
    """Sound designer creating audio."""

    name = "sound_designer"
    description = "Creates immersive audio experiences"

    async def _run_impl(self, state: State, history, network) -> Any:
        """Create game audio and music."""
        print(f"\n🎵 {self.name}: Composing audio for quantum adventures...")

        game_concept = state.get("game_concept", {})

        # Create audio design
        audio_design = {
            "music_tracks": {
                "main_theme": "Ethereal electronica - 2:30",
                "dimension_themes": [
                    "Grid World - Retro synthwave",
                    "Fractured Reality - Glitch hop",
                    "Quantum Forest - Ambient nature",
                    "Time Streams - Temporal echoes",
                    "The Void - Dark ambient",
                ],
                "victory_jingle": "Uplifting chimes - 0:05",
                "game_over": "Quantum collapse - 0:08",
            },
            "sound_effects": {
                "player": ["jump", "land", "phase_in", "phase_out", "death"],
                "abilities": [
                    "quantum_jump",
                    "time_rewind",
                    "entangle",
                    "break_entangle",
                ],
                "ui": ["button_click", "menu_open", "level_complete", "star_collect"],
                "ambient": ["dimension_hum", "particle_float", "energy_pulse"],
                "total_sfx": 34,
            },
            "audio_tech": {
                "format": "WebAudio API compatible",
                "compression": "OGG Vorbis",
                "3d_audio": "Positional audio for key effects",
                "dynamic_mixing": "Adaptive based on gameplay",
            },
        }

        state["audio_design"] = audio_design

        # Create procedural audio system
        procedural_audio = {
            "system": "Quantum harmonics generator",
            "parameters": ["Dimension", "Player velocity", "Puzzle state"],
            "realtime_effects": ["Reverb", "Delay", "Pitch shift", "Low-pass filter"],
        }

        state["procedural_audio"] = procedural_audio

        # Audio implementation
        audio_stats = {
            "total_duration": "18 minutes of music",
            "file_size": "12MB compressed",
            "load_strategy": "Progressive with priority queue",
            "mobile_optimization": "Reduced quality option available",
        }

        state["audio_stats"] = audio_stats

        metadata = {"next_agent": "qa_tester"}

        return self.create_result(
            f"Audio complete: {len(audio_design['music_tracks'])} music tracks, "
            f"{audio_design['sound_effects']['total_sfx']} sound effects",
            metadata=metadata,
        )


class QATesterAgent(Web3Agent):
    """QA tester finding and reporting bugs."""

    name = "qa_tester"
    description = "Thoroughly tests games and ensures quality"

    async def _run_impl(self, state: State, history, network) -> Any:
        """Test the game and find bugs."""
        print(f"\n🐛 {self.name}: Testing {state['game_concept']['title']}...")

        # Run test suites
        test_results = {
            "automated_tests": {
                "unit_tests": {"passed": 142, "failed": 3},
                "integration_tests": {"passed": 56, "failed": 1},
                "performance_tests": {"passed": 18, "failed": 0},
                "coverage": "86%",
            },
            "manual_testing": {
                "hours_tested": 12,
                "devices_tested": [
                    "iPhone 12",
                    "Samsung S21",
                    "iPad Pro",
                    "Chrome/Firefox/Safari",
                ],
                "test_cases_executed": 85,
            },
            "bugs_found": [
                {
                    "id": "BUG-001",
                    "severity": "High",
                    "desc": "Player clips through wall in level 23",
                    "status": "Fixed",
                },
                {
                    "id": "BUG-002",
                    "severity": "Medium",
                    "desc": "Audio cuts out after dimension shift",
                    "status": "Fixed",
                },
                {
                    "id": "BUG-003",
                    "severity": "Low",
                    "desc": "Particle effect persists on menu",
                    "status": "Fixed",
                },
                {
                    "id": "BUG-004",
                    "severity": "Low",
                    "desc": "Typo in tutorial text",
                    "status": "Fixed",
                },
            ],
            "performance_issues": [
                "Frame drops on older devices during particle-heavy scenes",
                "Loading time exceeds 3s on slow connections",
            ],
        }

        state["test_results"] = test_results

        # Gameplay feedback
        gameplay_feedback = {
            "difficulty": "Well-balanced with good progression",
            "fun_factor": "8.5/10 - Engaging puzzles, satisfying mechanics",
            "issues": [
                "Level 35 puzzle solution not intuitive",
                "Tutorial could be more interactive",
            ],
            "suggestions": [
                "Add colorblind mode",
                "Include speed run timer",
                "More particle effects on success",
            ],
        }

        state["gameplay_feedback"] = gameplay_feedback

        # Create test report
        test_report = {
            "build_tested": state.get("test_deployment", {}).get("build_id", "v0.9"),
            "test_date": "2024-01-25",
            "overall_quality": "Release Candidate",
            "recommendation": "Ready for soft launch after minor fixes",
            "estimated_rating": "4.3/5 stars",
        }

        state["final_test_report"] = test_report

        # Bill for QA work
        if self.wallet:
            payment = await self.request_payment(
                from_address=state.get("producer_address", self.address),
                amount_eth=0.05,
                task_description="Comprehensive QA testing",
            )
            print(f"💰 QA testing complete, invoiced: {payment['amount_eth']} ETH")

        return self.create_result(
            f"QA complete: {len(test_results['bugs_found'])} bugs found (all fixed), "
            f"Quality rating: {test_report['overall_quality']}",
            metadata={"game_ready": True},
        )


class GameProducerRouter(Router):
    """Routes between game development team members."""

    async def route(self, network, step, last_result, agents) -> str:
        """Route through game dev pipeline."""
        if step == 0:
            return "game_designer"

        # Check completion
        if last_result and last_result.metadata.get("game_ready"):
            return None

        # Follow metadata hints
        if last_result and last_result.metadata.get("next_agent"):
            return last_result.metadata["next_agent"]

        # Standard pipeline
        pipeline = [
            "game_designer",
            "artist",
            "programmer",
            "sound_designer",
            "qa_tester",
        ]

        current = last_result.agent if last_result else pipeline[0]
        try:
            idx = pipeline.index(current)
            if idx < len(pipeline) - 1:
                return pipeline[idx + 1]
        except ValueError:
            pass

        return None


async def run_game_dev_demo():
    """Run the game development team demo."""
    print("🎮 Game Development Team Demo")
    print("=" * 50)

    # Create shared mnemonic
    mnemonic = generate_shared_mnemonic()

    # Initial state
    state = State(
        {
            "project_type": "mobile_game",
            "timeline": "4 weeks",
            "budget_eth": 0.5,
            "producer_address": "0x" + "F" * 40,  # Mock producer wallet
        }
    )

    # Create game dev team
    agents = [
        GameDesignerAgent(
            web3_config=Web3AgentConfig(
                wallet_enabled=True,
                wallet_config=WalletConfig(mnemonic=mnemonic, account_index=0),
            )
        ),
        ArtistAgent(
            web3_config=Web3AgentConfig(
                wallet_enabled=True,
                wallet_config=WalletConfig(mnemonic=mnemonic, account_index=1),
            )
        ),
        ProgrammerAgent(
            web3_config=Web3AgentConfig(
                wallet_enabled=True,
                tee_enabled=True,
                wallet_config=WalletConfig(mnemonic=mnemonic, account_index=2),
            )
        ),
        SoundDesignerAgent(
            web3_config=Web3AgentConfig(
                wallet_enabled=True,
                wallet_config=WalletConfig(mnemonic=mnemonic, account_index=3),
            )
        ),
        QATesterAgent(
            web3_config=Web3AgentConfig(
                wallet_enabled=True,
                wallet_config=WalletConfig(mnemonic=mnemonic, account_index=4),
            )
        ),
    ]

    # Create network
    network = Web3Network(
        state=state,
        agents=agents,
        router=GameProducerRouter(),
        shared_mnemonic=mnemonic,
        max_steps=10,
    )

    # Run game development
    final_state = await network.run()

    # Print game summary
    print("\n" + "=" * 50)
    print("🎮 Game Development Complete!")

    game = final_state.get("game_concept", {})
    print(f"\nGame: {game.get('title', 'Unknown')}")
    print(f"Genre: {game.get('genre', 'Unknown')}")
    print(f"Platform: {game.get('platform', 'Unknown')}")

    # Development summary
    print("\n📊 Development Summary:")

    impl = final_state.get("implementation", {})
    print(
        f"  Code: {impl.get('total_loc', 0):,} lines ({impl.get('test_coverage', 'N/A')})"
    )

    assets = final_state.get("game_assets", {})
    print(f"  Art: {len(assets.get('environments', {}))} environments")

    audio = final_state.get("audio_design", {})
    print(
        f"  Audio: {len(audio.get('music_tracks', {}))} tracks, {audio.get('sound_effects', {}).get('total_sfx', 0)} SFX"
    )

    tests = final_state.get("test_results", {})
    bugs = tests.get("bugs_found", [])
    print(f"  QA: {len(bugs)} bugs found and fixed")

    # Quality report
    report = final_state.get("final_test_report", {})
    print(f"\n✅ Final Status: {report.get('recommendation', 'Unknown')}")
    print(f"📱 Test Build: {report.get('build_tested', 'N/A')}")
    print(f"⭐ Expected Rating: {report.get('estimated_rating', 'N/A')}")

    # Team stats
    print("\n👥 Team Performance:")
    stats = network.get_agent_stats()
    for agent_name, _agent_stats in stats.items():
        print(f"  {agent_name}: Completed tasks")

    print(f"\n🎉 Game ready for launch!")


if __name__ == "__main__":
    asyncio.run(run_game_dev_demo())
