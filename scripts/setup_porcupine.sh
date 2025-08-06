#!/bin/bash
# openWakeWord Setup Script for Raspberry Pi Voice Assistant
# This script helps set up Porcupine wake word detection

set -e  # Exit on any error

echo "🎤 Setting up Porcupine Wake Word Detection..."

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

# Create directories
print_status "Creating directories..."
mkdir -p ~/porcupine/keywords
mkdir -p ~/porcupine/models

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install Porcupine
print_status "Installing Porcupine..."
pip install pvporcupine==1.9.0

# Download a built-in wake word for testing
print_status "Downloading built-in wake word for testing..."
cd ~/porcupine/keywords

# Download Picovoice wake word (built-in)
if [ ! -f "picovoice_linux.ppn" ]; then
    print_status "Downloading 'Picovoice' wake word..."
    wget -q https://github.com/Picovoice/porcupine/raw/master/resources/keyword_files/linux/arm/picovoice_linux.ppn
    print_status "Downloaded picovoice_linux.ppn"
else
    print_status "picovoice_linux.ppn already exists"
fi

# Set proper permissions
chmod 644 *.ppn

# Test Porcupine installation
print_status "Testing Porcupine installation..."
cd - > /dev/null  # Return to original directory

# Create a simple test script
cat > test_porcupine.py << 'EOF'
#!/usr/bin/env python3
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.wake_word import WakeWordDetector
    print("✅ Porcupine import successful")
    
    # Test initialization
    wd = WakeWordDetector(
        keyword_path=os.path.expanduser("~/porcupine/keywords/picovoice_linux.ppn"),
        sensitivity=0.5
    )
    print("✅ Wake word detector initialized successfully")
    wd.close()
    print("✅ Porcupine setup complete!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the virtual environment and dependencies are installed")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
EOF

# Run the test
print_status "Running Porcupine test..."
python test_porcupine.py

# Clean up test file
rm test_porcupine.py

print_status "Porcupine setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Go to https://console.picovoice.ai/ to create a custom 'Jarvis' wake word"
echo "2. Download the .ppn file for Linux ARM platform"
echo "3. Copy it to ~/porcupine/keywords/jarvis_linux.ppn"
echo "4. Update config.yaml with the correct path"
echo ""
echo "🔧 For now, you can test with the built-in 'Picovoice' wake word:"
echo "   Update config.yaml: keyword_path: '~/porcupine/keywords/picovoice_linux.ppn'"
echo "   Then say 'Picovoice' to activate the assistant" 