#!/bin/bash
# Audio Setup Script for Raspberry Pi Voice Assistant
# This script helps configure audio devices for the voice assistant

set -e

echo "🎤 Audio Setup for Voice Assistant..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

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
    print_warning "This script is designed for Raspberry Pi."
fi

print_status "Checking audio devices..."

# List all audio devices
echo ""
echo "📋 Available Audio Devices:"
echo "=========================="

echo ""
echo "🎵 Playback devices (aplay -l):"
aplay -l 2>/dev/null || echo "No playback devices found"

echo ""
echo "🎤 Recording devices (arecord -l):"
arecord -l 2>/dev/null || echo "No recording devices found"

echo ""
echo "🔌 USB devices:"
lsusb | grep -i audio || echo "No USB audio devices found"

echo ""
echo "📊 PyAudio device information:"
python3 -c "
import pyaudio
p = pyaudio.PyAudio()
print('Available devices:')
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f'  Input {i}: {info[\"name\"]}')
    if info['maxOutputChannels'] > 0:
        print(f'  Output {i}: {info[\"name\"]}')
p.terminate()
" 2>/dev/null || echo "PyAudio not available"

echo ""
print_status "Testing microphone..."

# Test recording
echo "Recording 3 seconds of audio for testing..."
if arecord -D hw:1,0 -f S16_LE -r 16000 -c 1 -d 3 test_audio.wav 2>/dev/null; then
    print_status "Recording successful! Playing back..."
    aplay test_audio.wav 2>/dev/null && print_status "Playback successful!"
    rm test_audio.wav
else
    print_warning "Recording failed. Trying default device..."
    if arecord -f S16_LE -r 16000 -c 1 -d 3 test_audio.wav 2>/dev/null; then
        print_status "Recording with default device successful!"
        aplay test_audio.wav 2>/dev/null && print_status "Playback successful!"
        rm test_audio.wav
    else
        print_error "Recording failed with all devices"
    fi
fi

echo ""
print_status "Configuration suggestions:"
echo "================================"

echo ""
echo "1. If your USB microphone is working, update config.yaml:"
echo "   recording:"
echo "     input_device: \"hw:1,0\"  # or the device name from PyAudio list"

echo ""
echo "2. If you want to use a specific device by name, use:"
echo "   recording:"
echo "     input_device: \"DCMT Technology USB Lavalier Mic Pro\""

echo ""
echo "3. Test your configuration:"
echo "   python -c \"from src.wake_word import WakeWordDetector; print('Audio test passed')\""

echo ""
print_status "Audio setup complete!" 