#!/bin/bash
# openWakeWord Setup Script for Raspberry Pi Voice Assistant

set -e  # Exit on any error

echo "🎤 Setting up openWakeWord for Voice Assistant..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    print_warning "This script is designed for Raspberry Pi. Continue anyway? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install openWakeWord and dependencies
print_status "Installing openWakeWord and dependencies..."
pip install openwakeword==0.6.0
pip install onnxruntime

# Test openWakeWord installation
print_status "Testing openWakeWord installation..."
cd - > /dev/null  # Return to original directory

# Create a simple test script
cat > test_openwakeword.py << 'EOF'
#!/usr/bin/env python3
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import openwakeword
    print("✅ openWakeWord import successful")
    
    # Test model loading
    print("Loading openWakeWord model...")
    oww = openwakeword.Model(
        wakeword_models=["jarvis"],
        inference_framework="onnx"
    )
    print("✅ openWakeWord model loaded successfully")
    
    # Test wake word detector
    from src.wake_word import WakeWordDetector
    print("✅ Wake word detector import successful")
    
    # Test initialization (without audio)
    wd = WakeWordDetector(
        wake_word="jarvis",
        sensitivity=0.5
    )
    print("✅ Wake word detector initialized successfully")
    wd.close()
    print("✅ openWakeWord setup complete!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the virtual environment and dependencies are installed")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
EOF

# Run the test
print_status "Running openWakeWord test..."
python test_openwakeword.py

# Clean up test file
rm test_openwakeword.py

print_status "openWakeWord setup complete!"
echo ""
echo "📋 Available wake words:"
echo "The following wake words are available in openWakeWord:"
echo "- jarvis"
echo "- alexa" 
echo "- hey_google"
echo "- hey_siri"
echo "- computer"
echo "- and many more..."
echo ""
echo "🔧 To use a different wake word:"
echo "1. Update config.yaml: wake_word: 'your_wake_word'"
echo "2. Restart the voice assistant"
echo ""
echo "🎤 Your voice assistant is now ready to use openWakeWord!" 