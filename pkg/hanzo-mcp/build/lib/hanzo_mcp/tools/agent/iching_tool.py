"""I Ching tool for creative problem solving using Hanzo principles."""

import random
from enum import Enum
from typing import List, override

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.common.base import BaseTool


class HanzoPrinciple(Enum):
    """Hanzo principles organized by category."""

    # Empathy
    AUTONOMY = ("Autonomy", "Trust fully; freedom fuels genius", "🦅")
    BALANCE = ("Balance", "Steady wins; burnout loses every time", "⚖️")
    CUSTOMER_OBSESSION = (
        "Customer Obsession",
        "Coach relentlessly; their victories yours",
        "🎓",
    )
    HUMILITY = ("Humility", "Quiet confidence; greatness emerges naturally", "🧘")
    INTEGRITY = ("Integrity", "Principles never break; reputation never fades", "🛡️")
    SELFLESSNESS = ("Selflessness", "Elevate others; personal success follows", "🤝")

    # Science
    CURIOSITY = ("Curiosity", "Question always; truth never ends", "🌱")
    EMPIRICISM = ("Empiricism", "Hypothesize, measure; reality defines truth", "🔬")
    PRECISION = (
        "Precision",
        "Discipline in data; eliminate guesswork completely",
        "🎯",
    )
    VALIDATION = ("Validation", "Test assumptions hard; illusions crumble fast", "✅")
    OBJECTIVITY = ("Objectivity", "Ego out; results speak plainly", "🧊")
    REPEATABILITY = (
        "Repeatability",
        "Do it again; success repeats systematically",
        "🔄",
    )

    # Design
    ACCESSIBILITY = (
        "Accessibility",
        "Open doors wide; adoption thrives naturally",
        "🌐",
    )
    BEAUTY = ("Beauty", "Form speaks louder; aesthetics lift utility", "🎨")
    CLARITY = ("Clarity", "Obvious is perfect; complexity hidden cleanly", "🔍")
    CONSISTENCY = ("Consistency", "Uniform patterns; predictable results always", "🎯")
    SIMPLICITY = ("Simplicity", "Cut ruthlessly; essential alone remains", "🪶")
    FLOW = ("Flow", "Remove friction; natural motion prevails", "🌊")

    # Engineering
    BATTERIES_INCLUDED = (
        "Batteries Included",
        "Ready instantly; everything you need to start",
        "🔋",
    )
    CONCURRENCY = ("Concurrency", "Parallel flows; frictionless scale", "⚡")
    COMPOSABLE = ("Composable", "Modular magic; pieces multiply power", "🧩")
    INTEROPERABLE = (
        "Interoperable",
        "Integrate effortlessly; value compounds infinitely",
        "🔗",
    )
    ORTHOGONAL = ("Orthogonal", "Each tool exact; no overlap, no waste", "⚙️")
    SCALABLE = ("Scalable", "Growth limitless; obstacles removed at inception", "📈")

    # Scale
    DISRUPTION = ("Disruption", "Reinvent boldly; transcend competition entirely", "💥")
    EXPERIMENTATION = ("Experimentation", "Test quickly; iterate endlessly", "🧪")
    EXPONENTIALITY = ("Exponentiality", "Compound constantly; incremental fades", "📈")
    VELOCITY = ("Velocity", "Ship fast; refine faster", "🚀")
    URGENCY = ("Urgency", "Act now; delays destroy opportunity", "⏱️")

    # Wisdom
    ADAPTABILITY = (
        "Adaptability",
        "Pivot sharply; fluid response accelerates evolution",
        "🌊",
    )
    DECENTRALIZATION = (
        "Decentralization",
        "Distribute power; resilience born from autonomy",
        "🕸️",
    )
    FREEDOM = (
        "Freedom",
        "Democratize creativity; tools liberated, gatekeepers removed",
        "🗽",
    )
    LONGEVITY = (
        "Longevity",
        "Build timelessly; greatness endures beyond lifetimes",
        "⏳",
    )
    SECURITY = ("Security", "Encryption first; privacy non-negotiable", "🔐")
    ZEN = ("Zen", "Calm mastery; effortless excellence every moment", "☯️")


class Hexagram:
    """I Ching hexagram with interpretation."""

    HEXAGRAMS = {
        "111111": (
            "乾 (Qián)",
            "Creative",
            "Initiating force, pure yang energy. Time for bold action.",
        ),
        "000000": (
            "坤 (Kūn)",
            "Receptive",
            "Pure receptivity, yielding. Time to listen and adapt.",
        ),
        "100010": (
            "屯 (Zhūn)",
            "Initial Difficulty",
            "Growing pains. Persevere through early challenges.",
        ),
        "010001": (
            "蒙 (Méng)",
            "Youthful Folly",
            "Beginner's mind. Learn humbly, question assumptions.",
        ),
        "111010": (
            "需 (Xū)",
            "Waiting",
            "Strategic patience. Prepare while waiting for the right moment.",
        ),
        "010111": (
            "訟 (Sòng)",
            "Conflict",
            "Address conflicts directly but seek resolution, not victory.",
        ),
        "010000": (
            "師 (Shī)",
            "Army",
            "Organize resources, build strong teams, lead by example.",
        ),
        "000010": (
            "比 (Bǐ)",
            "Holding Together",
            "Unity and collaboration. Strengthen bonds.",
        ),
        "111011": (
            "小畜 (Xiǎo Chù)",
            "Small Accumulation",
            "Small consistent improvements compound over time.",
        ),
        "110111": (
            "履 (Lǚ)",
            "Treading",
            "Careful progress. Mind the details while moving forward.",
        ),
        "111000": (
            "泰 (Tài)",
            "Peace",
            "Harmony achieved. Maintain balance while building.",
        ),
        "000111": (
            "否 (Pǐ)",
            "Standstill",
            "Blockage present. Pause, reassess, find new paths.",
        ),
        "101111": (
            "同人 (Tóng Rén)",
            "Fellowship",
            "Community strength. Build alliances and share knowledge.",
        ),
        "111101": (
            "大有 (Dà Yǒu)",
            "Great Possession",
            "Abundance available. Share generously to multiply value.",
        ),
        "001000": (
            "謙 (Qiān)",
            "Modesty",
            "Humble confidence. Let work speak for itself.",
        ),
        "000100": (
            "豫 (Yù)",
            "Enthusiasm",
            "Infectious energy. Channel excitement into action.",
        ),
        "100110": (
            "隨 (Suí)",
            "Following",
            "Adaptive leadership. Know when to lead and when to follow.",
        ),
        "011001": (
            "蠱 (Gǔ)",
            "Work on Decay",
            "Fix technical debt. Address root causes.",
        ),
        "110000": (
            "臨 (Lín)",
            "Approach",
            "Opportunity approaching. Prepare to receive it.",
        ),
        "000011": (
            "觀 (Guān)",
            "Contemplation",
            "Step back for perspective. See the whole system.",
        ),
        "100101": (
            "噬嗑 (Shì Kè)",
            "Biting Through",
            "Remove obstacles decisively. Clear blockages.",
        ),
        "101001": ("賁 (Bì)", "Grace", "Polish and refine. Beauty enhances function."),
        "000001": (
            "剝 (Bō)",
            "Splitting Apart",
            "Decay phase. Let go of what's not working.",
        ),
        "100000": (
            "復 (Fù)",
            "Return",
            "New cycle begins. Start fresh with lessons learned.",
        ),
        "100111": (
            "無妄 (Wú Wàng)",
            "Innocence",
            "Act with pure intention. Avoid overthinking.",
        ),
        "111001": (
            "大畜 (Dà Chù)",
            "Great Accumulation",
            "Build reserves. Invest in infrastructure.",
        ),
        "100001": (
            "頤 (Yí)",
            "Nourishment",
            "Feed growth. Provide resources teams need.",
        ),
        "011110": (
            "大過 (Dà Guò)",
            "Great Excess",
            "Extraordinary measures needed. Bold action required.",
        ),
        "010010": (
            "坎 (Kǎn)",
            "Abysmal",
            "Navigate danger carefully. Trust your training.",
        ),
        "101101": (
            "離 (Lí)",
            "Clinging Fire",
            "Clarity and vision. Illuminate the path forward.",
        ),
        "001110": (
            "咸 (Xián)",
            "Influence",
            "Mutual attraction. Build on natural affinities.",
        ),
        "011100": (
            "恆 (Héng)",
            "Duration",
            "Persistence pays. Maintain steady effort.",
        ),
        "001111": ("遯 (Dùn)", "Retreat", "Strategic withdrawal. Regroup and refocus."),
        "111100": (
            "大壯 (Dà Zhuàng)",
            "Great Power",
            "Strength available. Use power responsibly.",
        ),
        "000101": (
            "晉 (Jìn)",
            "Progress",
            "Advance steadily. Each step builds momentum.",
        ),
        "101000": (
            "明夷 (Míng Yí)",
            "Darkening Light",
            "Work quietly. Keep brilliance hidden for now.",
        ),
        "101011": (
            "家人 (Jiā Rén)",
            "Family",
            "Team harmony. Strengthen internal culture.",
        ),
        "110101": (
            "睽 (Kuí)",
            "Opposition",
            "Creative tension. Find synthesis in differences.",
        ),
        "001010": (
            "蹇 (Jiǎn)",
            "Obstruction",
            "Difficulty ahead. Find alternative routes.",
        ),
        "010100": (
            "解 (Xiè)",
            "Deliverance",
            "Breakthrough achieved. Consolidate gains.",
        ),
        "110001": ("損 (Sǔn)", "Decrease", "Simplify ruthlessly. Less is more."),
        "100011": ("益 (Yì)", "Increase", "Multiply value. Invest in growth."),
        "111110": (
            "夬 (Guài)",
            "Breakthrough",
            "Decisive moment. Act with conviction.",
        ),
        "011111": (
            "姤 (Gòu)",
            "Coming to Meet",
            "Unexpected encounter. Stay alert to opportunity.",
        ),
        "000110": (
            "萃 (Cuì)",
            "Gathering",
            "Convergence point. Bring elements together.",
        ),
        "011000": (
            "升 (Shēng)",
            "Pushing Upward",
            "Gradual ascent. Build systematically.",
        ),
        "010110": ("困 (Kùn)", "Exhaustion", "Resources depleted. Rest and recharge."),
        "011010": ("井 (Jǐng)", "The Well", "Deep resources. Draw from fundamentals."),
        "101110": (
            "革 (Gé)",
            "Revolution",
            "Transform completely. Embrace radical change.",
        ),
        "011101": (
            "鼎 (Dǐng)",
            "The Cauldron",
            "Transformation vessel. Cook new solutions.",
        ),
        "100100": (
            "震 (Zhèn)",
            "Thunder",
            "Shocking awakening. Respond to wake-up calls.",
        ),
        "001001": (
            "艮 (Gèn)",
            "Mountain",
            "Stillness and stability. Find solid ground.",
        ),
        "001011": (
            "漸 (Jiàn)",
            "Gradual Progress",
            "Step by step. Patient development.",
        ),
        "110100": (
            "歸妹 (Guī Mèi)",
            "Marrying Maiden",
            "New partnerships. Align expectations.",
        ),
        "101100": ("豐 (Fēng)", "Abundance", "Peak achievement. Prepare for cycles."),
        "001101": ("旅 (Lǚ)", "The Wanderer", "Explorer mindset. Learn from journey."),
        "011011": (
            "巽 (Xùn)",
            "Gentle Wind",
            "Subtle influence. Persistent gentle pressure.",
        ),
        "110110": ("兌 (Duì)", "Joy", "Infectious happiness. Celebrate progress."),
        "010011": ("渙 (Huàn)", "Dispersion", "Break up rigidity. Dissolve barriers."),
        "110010": (
            "節 (Jié)",
            "Limitation",
            "Healthy constraints. Focus through limits.",
        ),
        "110011": (
            "中孚 (Zhōng Fú)",
            "Inner Truth",
            "Authentic core. Build from truth.",
        ),
        "001100": (
            "小過 (Xiǎo Guò)",
            "Small Excess",
            "Minor adjustments. Fine-tune carefully.",
        ),
        "101010": (
            "既濟 (Jì Jì)",
            "After Completion",
            "Success achieved. Maintain vigilance.",
        ),
        "010101": (
            "未濟 (Wèi Jì)",
            "Before Completion",
            "Almost there. Final push needed.",
        ),
    }

    def __init__(self, lines: str):
        self.lines = lines
        self.name, self.title, self.meaning = self.HEXAGRAMS.get(
            lines,
            ("Unknown", "Mystery", "The pattern is unclear. Trust your intuition."),
        )

    def get_changing_lines(self) -> List[int]:
        """Identify which lines are changing (would be 6 or 9 in traditional I Ching)."""
        # For simplicity, randomly select 0-2 changing lines
        num_changes = random.choice([0, 1, 1, 2])
        if num_changes == 0:
            return []
        positions = list(range(6))
        return sorted(random.sample(positions, num_changes))


class IChing:
    """I Ching oracle for engineering guidance."""

    def __init__(self):
        self.principles = list(HanzoPrinciple)

    def cast_hexagram(self) -> Hexagram:
        """Cast a hexagram using virtual coins."""
        lines = ""
        for _ in range(6):
            # Three coin tosses: heads=3, tails=2
            coins = sum(random.choice([2, 3]) for _ in range(3))
            # 6=old yin(changing 0), 7=young yang(1), 8=young yin(0), 9=old yang(changing 1)
            if coins in [6, 8]:
                lines += "0"
            else:
                lines += "1"
        return Hexagram(lines)

    def select_principles(self, hexagram: Hexagram, challenge: str) -> List[HanzoPrinciple]:
        """Select relevant Hanzo principles based on hexagram and challenge."""
        # Use hexagram pattern to deterministically but creatively select principles
        selected = []

        # Primary principle based on hexagram pattern
        primary_index = sum(int(bit) * (2**i) for i, bit in enumerate(hexagram.lines)) % len(self.principles)
        selected.append(self.principles[primary_index])

        # Supporting principles based on challenge keywords
        keywords = challenge.lower().split()
        keyword_matches = {
            "scale": [HanzoPrinciple.SCALABLE, HanzoPrinciple.EXPONENTIALITY],
            "speed": [HanzoPrinciple.VELOCITY, HanzoPrinciple.URGENCY],
            "quality": [HanzoPrinciple.PRECISION, HanzoPrinciple.VALIDATION],
            "team": [HanzoPrinciple.AUTONOMY, HanzoPrinciple.BALANCE],
            "design": [HanzoPrinciple.SIMPLICITY, HanzoPrinciple.BEAUTY],
            "bug": [HanzoPrinciple.EMPIRICISM, HanzoPrinciple.OBJECTIVITY],
            "refactor": [HanzoPrinciple.CLARITY, HanzoPrinciple.COMPOSABLE],
            "security": [HanzoPrinciple.SECURITY, HanzoPrinciple.INTEGRITY],
            "performance": [HanzoPrinciple.CONCURRENCY, HanzoPrinciple.ORTHOGONAL],
            "user": [HanzoPrinciple.CUSTOMER_OBSESSION, HanzoPrinciple.ACCESSIBILITY],
        }

        for keyword, principles in keyword_matches.items():
            if keyword in keywords:
                selected.extend(principles)

        # Add complementary principle based on changing lines
        changing_lines = hexagram.get_changing_lines()
        if changing_lines:
            complement_index = (primary_index + sum(changing_lines)) % len(self.principles)
            selected.append(self.principles[complement_index])

        # Ensure uniqueness and limit to 3-5 principles
        seen = set()
        unique_selected = []
        for principle in selected:
            if principle not in seen:
                seen.add(principle)
                unique_selected.append(principle)

        return unique_selected[:5]

    def generate_guidance(self, hexagram: Hexagram, principles: List[HanzoPrinciple], challenge: str) -> str:
        """Generate creative guidance combining I Ching wisdom and Hanzo principles."""
        guidance = f"☯️ I CHING GUIDANCE FOR ENGINEERING CHALLENGE ☯️\n\n"
        guidance += f"**Your Challenge:** {challenge}\n\n"

        guidance += f"**Hexagram Cast:** {hexagram.name} - {hexagram.title}\n"
        guidance += f"**Pattern:** {''.join('━━━' if l == '1' else '━ ━' for l in hexagram.lines[::-1])}\n"
        guidance += f"**Ancient Wisdom:** {hexagram.meaning}\n\n"

        guidance += "**Hanzo Principles to Apply:**\n\n"

        for principle in principles:
            name, wisdom, emoji = principle.value
            guidance += f"{emoji} **{name}**\n"
            guidance += f"   *{wisdom}*\n\n"

        # Generate specific actionable advice
        guidance += "**Synthesized Approach:**\n\n"

        # Hexagram-specific guidance
        if "Creative" in hexagram.title:
            guidance += "• This is a time for bold innovation. Don't hold back on ambitious ideas.\n"
        elif "Receptive" in hexagram.title:
            guidance += "• Listen deeply to user needs and system constraints before acting.\n"
        elif "Difficulty" in hexagram.title:
            guidance += "• Challenges are teachers. Each obstacle reveals the path forward.\n"
        elif "Waiting" in hexagram.title:
            guidance += "• Strategic patience required. Prepare thoroughly before implementation.\n"
        elif "Conflict" in hexagram.title:
            guidance += "• Technical disagreements? Seek data-driven resolution.\n"
        elif "Peace" in hexagram.title:
            guidance += "• Harmony achieved. Now build sustainably on this foundation.\n"

        # Principle-specific actionable advice
        principle_actions = {
            HanzoPrinciple.SCALABLE: "• Design for 10x growth from day one. Remove scaling bottlenecks now.",
            HanzoPrinciple.VELOCITY: "• Ship an MVP today. Perfect is the enemy of shipped.",
            HanzoPrinciple.SIMPLICITY: "• Delete half your code. The best code is no code.",
            HanzoPrinciple.EMPIRICISM: "• Measure everything. Let data guide your decisions.",
            HanzoPrinciple.CUSTOMER_OBSESSION: "• Talk to users now. Their pain is your roadmap.",
            HanzoPrinciple.CONCURRENCY: "• Parallelize everything possible. Sequential is slow.",
            HanzoPrinciple.SECURITY: "• Security is not optional. Encrypt by default.",
            HanzoPrinciple.ZEN: "• Find calm in the chaos. Clear mind writes better code.",
        }

        for principle in principles:
            if principle in principle_actions:
                guidance += principle_actions[principle] + "\n"

        # Changing lines wisdom
        changing_lines = hexagram.get_changing_lines()
        if changing_lines:
            guidance += f"\n**Lines in Transition:** {', '.join(str(i + 1) for i in changing_lines)}\n"
            guidance += "• Change is imminent in these areas. Prepare for transformation.\n"

        # Final synthesis
        guidance += "\n**The Way Forward:**\n"
        guidance += self._synthesize_action_plan(hexagram, principles, challenge)

        guidance += "\n\n*Remember: The I Ching reveals patterns, not prescriptions. "
        guidance += "Let this wisdom guide your intuition as you craft your solution.*"

        return guidance

    def _synthesize_action_plan(self, hexagram: Hexagram, principles: List[HanzoPrinciple], challenge: str) -> str:
        """Create a specific action plan based on the reading."""
        plan = ""

        # Determine the nature of the challenge
        if any(word in challenge.lower() for word in ["bug", "error", "fix", "broken"]):
            plan += "1. **Diagnose systematically** - Use empirical debugging, not guesswork\n"
            plan += "2. **Fix root cause** - Address the source, not just symptoms\n"
            plan += "3. **Prevent recurrence** - Add tests and monitoring\n"
        elif any(word in challenge.lower() for word in ["scale", "performance", "slow"]):
            plan += "1. **Measure first** - Profile to find actual bottlenecks\n"
            plan += "2. **Parallelize** - Use concurrency where possible\n"
            plan += "3. **Simplify** - Remove complexity before optimizing\n"
        elif any(word in challenge.lower() for word in ["design", "architect", "structure"]):
            plan += "1. **Start simple** - MVP first, elaborate later\n"
            plan += "2. **Stay flexible** - Design for change\n"
            plan += "3. **Think holistically** - Consider entire system\n"
        elif any(word in challenge.lower() for word in ["team", "collaborate", "people"]):
            plan += "1. **Enable autonomy** - Trust your team\n"
            plan += "2. **Maintain balance** - Sustainable pace wins\n"
            plan += "3. **Share knowledge** - Elevate everyone\n"
        else:
            plan += "1. **Clarify intent** - What problem are you really solving?\n"
            plan += "2. **Start small** - Build incrementally\n"
            plan += "3. **Iterate rapidly** - Fast feedback loops\n"

        return plan


class IChingTool(BaseTool):
    """Tool for applying I Ching wisdom to engineering challenges."""

    name = "iching"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Apply I Ching wisdom and Hanzo principles to engineering challenges.

This tool casts an I Ching hexagram and selects relevant Hanzo principles
to provide creative guidance for your engineering challenge.

Parameters:
- challenge: Description of the engineering challenge or question

The oracle will:
1. Cast a hexagram representing the current situation
2. Select relevant Hanzo principles
3. Synthesize actionable guidance
4. Provide specific recommendations

Example:
iching(
    challenge="How should I approach refactoring this legacy codebase?"
)

Use this when you need:
- Fresh perspective on a problem
- Creative approach to challenges
- Wisdom for difficult decisions
- Alignment with Hanzo principles"""

    def __init__(self):
        """Initialize the I Ching tool."""
        super().__init__()
        self.oracle = IChing()

    async def call(self, ctx: MCPContext, challenge: str) -> str:
        """Cast I Ching and provide guidance."""
        # Cast hexagram
        hexagram = self.oracle.cast_hexagram()

        # Select relevant principles
        principles = self.oracle.select_principles(hexagram, challenge)

        # Generate guidance
        guidance = self.oracle.generate_guidance(hexagram, principles, challenge)

        return guidance

    def register(self, server: FastMCP) -> None:
        """Register the tool with the MCP server."""
        tool_self = self

        @server.tool(name=self.name, description=self.description)
        async def iching(ctx: MCPContext, challenge: str) -> str:
            return await tool_self.call(ctx, challenge)
