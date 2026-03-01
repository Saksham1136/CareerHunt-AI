#!/bin/bash
# ─────────────────────────────────────────────
# run.sh — One-command startup for Job Seeker AI
# Usage: bash run.sh
# ─────────────────────────────────────────────

echo "🤖 Multi-Agent AI Job Seeker — Starting Up..."
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1)
echo "📌 $PYTHON_VERSION"

# Check .env file
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "   → Copy .env.example to .env"
    echo "   → Add your Groq API key"
    echo "   → Run this script again"
    exit 1
fi

echo "✅ .env file found"

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt --quiet
else
    source venv/bin/activate
fi

echo "✅ Dependencies ready"
echo ""
echo "🚀 Launching Streamlit app..."
echo "   → App will open at: http://localhost:8501"
echo ""

# Run the Streamlit app from the ui/ directory
streamlit run ui/app.py --server.port 8501
