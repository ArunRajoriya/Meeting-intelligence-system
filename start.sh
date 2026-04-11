#!/bin/bash

# Meeting Intelligence System - Startup Script

echo "=================================="
echo "Meeting Intelligence System"
echo "=================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if [ ! -f "venv/bin/uvicorn" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Creating template .env file..."
    cat > .env << EOF
GROQ_API_KEY=your_groq_api_key_here

# Optional transcription providers (uncomment and add key)
# OPENAI_API_KEY=your_openai_key_here
# ASSEMBLYAI_API_KEY=your_assemblyai_key_here
EOF
    echo "✅ Template .env created. Please add your API keys!"
    echo ""
    echo "Get your Groq API key from: https://console.groq.com/keys"
    echo ""
    exit 1
fi

# Create meeting_notes directory if it doesn't exist
if [ ! -d "meeting_notes" ]; then
    mkdir -p meeting_notes
    echo "✅ Created meeting_notes directory"
fi

# Start the server
echo ""
echo "🚀 Starting server..."
echo "=================================="
echo ""
echo "Server will be available at:"
echo "  - API: http://localhost:8000"
echo "  - Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
