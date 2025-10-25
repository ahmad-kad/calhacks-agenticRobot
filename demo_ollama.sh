#!/bin/bash

# MERLIN + Ollama Demo Script
# Shows autonomous robot control using local LLM, no internet needed

set -e

export PYTHONPATH=/Users/ahmadkaddoura/calhacks:$PYTHONPATH

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                  MERLIN + Ollama Demo                         ║"
echo "║            Autonomous Robot with Local LLM Control            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check Ollama is running
echo "📋 Checking Ollama connectivity..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ Ollama not running on localhost:11434"
    echo ""
    echo "Start Ollama in another terminal:"
    echo "  ollama serve"
    exit 1
fi
echo "✅ Ollama is running"
echo ""

# Show available models
echo "📦 Available Models:"
curl -s http://localhost:11434/api/tags | python3 -c "
import sys, json
data = json.load(sys.stdin)
for model in data['models']:
    name = model['name']
    size = round(model['size'] / 1e9, 1)
    print(f'   • {name} ({size} GB)')
" 2>/dev/null || echo "   (Could not list models)"
echo ""

# Demo 1: Simple mission
echo "🤖 DEMO 1: Simple Pick-and-Place Mission"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
python main.py --backend mock --agent ollama --mission "Pick and place" | jq -r '.result'
echo ""
echo "✅ Mission 1 Complete"
echo ""

# Demo 2: Another mission
echo "🤖 DEMO 2: Navigation and Status Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
python main.py --backend mock --agent ollama --mission "Navigate and report status" | jq -r '.result'
echo ""
echo "✅ Mission 2 Complete"
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                     Demo Complete! ✅                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Key Features Demonstrated:"
echo "  ✅ Local LLM inference (no internet needed)"
echo "  ✅ Autonomous mission execution"
echo "  ✅ Real-time state machine (60 Hz)"
echo "  ✅ Battery management"
echo "  ✅ Gripper control"
echo ""
echo "Next Steps:"
echo "  1. Test with ManiSkill: python examples/test_maniskill.py"
echo "  2. View logs: tail -f merlin.log"
echo "  3. Try custom missions:"
echo "     python main.py --backend mock --agent ollama --mission 'Your mission here'"
echo ""
echo "For more details, see: OLLAMA_INTEGRATION_GUIDE.md"
