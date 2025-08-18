#!/bin/bash
# Demo: Using GPT-4o/GPT-5 as orchestrator for code review

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Hanzo Dev - GPT-5/Codex Orchestrator Demo              ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "This demo shows how to use GPT-5 or GPT-4o as the orchestrator"
echo "to review code and coordinate multiple AI agents."
echo ""
echo "Available orchestrators:"
echo "  • gpt-5         - Most advanced model (when available)"
echo "  • gpt-4o        - GPT-4 optimized, excellent for code"
echo "  • gpt-4-turbo   - Fast GPT-4 variant"
echo "  • gpt-4         - Standard GPT-4"
echo "  • claude-3-5    - Claude 3.5 Sonnet"
echo "  • local:llama3  - Local Llama 3 (via hanzo net)"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

# Example 1: GPT-4o orchestrating code review
echo "Example 1: GPT-4o Orchestrating Code Review"
echo "--------------------------------------------"
echo "Command: hanzo dev --orchestrator gpt-4o --instances 3"
echo ""
echo "This will:"
echo "  1. Start GPT-4o as the main orchestrator"
echo "  2. Create 3 worker agents for parallel processing"
echo "  3. Enable System 2 thinking with critic agents"
echo "  4. Review and improve code continuously"
echo ""

# Example 2: GPT-5 with local workers (cost-optimized)
echo "Example 2: GPT-5 with Local Workers (90% Cost Reduction)"
echo "--------------------------------------------------------"
echo "Command: hanzo dev --orchestrator gpt-5 --use-hanzo-net"
echo ""
echo "This will:"
echo "  1. Use GPT-5 for high-level orchestration only"
echo "  2. Deploy local models for simple tasks"
echo "  3. Route complex tasks to API models"
echo "  4. Save 90% on API costs"
echo ""

# Example 3: Full code review with reporting
echo "Example 3: Comprehensive Code Review"
echo "------------------------------------"
cat << 'EOF'
# Start hanzo dev with GPT-4o
hanzo dev --orchestrator gpt-4o \
          --instances 3 \
          --critic-instances 2 \
          --enable-guardrails \
          --workspace . \
          << 'REVIEW'
Please perform a comprehensive code review of the hanzo dev module:

1. Security Analysis:
   - Check for vulnerabilities
   - Review authentication patterns
   - Validate input sanitization

2. Performance Review:
   - Identify bottlenecks
   - Suggest optimizations
   - Review async patterns

3. Architecture Assessment:
   - Evaluate design patterns
   - Check SOLID principles
   - Review module coupling

4. Code Quality:
   - Check for duplication
   - Review naming conventions
   - Assess test coverage

Generate a detailed report with actionable recommendations.
REVIEW
EOF

echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "To run any of these examples, simply execute the command shown."
echo "Make sure you have your OPENAI_API_KEY set for GPT models."
echo ""
echo "For more information: hanzo dev --help"