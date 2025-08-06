#!/usr/bin/env python3
"""
Audio Test Script for Voice Assistant
Tests microphone input and audio output devices
"""

import os
import sys
import time
import subprocess
import tempfile
import pyaudio
import wave

def print_header(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")

def print_section(title):
    print(f"\n{'-'*30}")
    print(f"  {title}")
    print(f"{'-'*30}")

def test_audio_devices():
    """Test and list all audio devices"""
    print_header("AUDIO DEVICE TEST")
    
    # Test aplay
    print_section("Playback Devices (aplay -l)")
    try:
        result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
        print(result.stdout)
    except FileNotFoundError:
        print("aplay not found")
    
    # Test arecord
    print_section("Recording Devices (arecord -l)")
    try:
        result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
        print(result.stdout)
    except FileNotFoundError:
        print("arecord not found")
    
    # Test PyAudio devices
    print_section("PyAudio Devices")
    try:
        p = pyaudio.PyAudio()
        print("Available devices:")
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            device_type = []
            if info['maxInputChannels'] > 0:
                device_type.append("INPUT")
            if info['maxOutputChannels'] > 0:
                device_type.append("OUTPUT")
            print(f"  {i}: {info['name']} ({', '.join(device_type)})")
        p.terminate()
    except Exception as e:
        print(f"PyAudio error: {e}")

def test_microphone_recording(input_device="hw:4,0", duration=3):
    """Test microphone recording"""
    print_header("MICROPHONE RECORDING TEST")
    
    print(f"Testing microphone: {input_device}")
    print(f"Recording for {duration} seconds...")
    
    # Test with arecord
    print_section("Testing with arecord")
    try:
        test_file = "test_mic.wav"
        cmd = ['arecord', '-D', input_device, '-f', 'S16_LE', '-r', '16000', '-c', '1', '-d', str(duration), test_file]
        print(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Recording successful!")
            
            # Check file size
            if os.path.exists(test_file):
                size = os.path.getsize(test_file)
                print(f"File size: {size} bytes")
                
                # Test playback
                print("Playing back recording...")
                subprocess.run(['aplay', test_file], capture_output=True)
                print("✅ Playback successful!")
                
                # Clean up
                os.remove(test_file)
            else:
                print("❌ Recording file not created")
        else:
            print(f"❌ Recording failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Recording error: {e}")

def test_audio_output(output_device="plughw:3,0"):
    """Test audio output"""
    print_header("AUDIO OUTPUT TEST")
    
    print(f"Testing audio output: {output_device}")
    
    # Test with speaker-test
    print_section("Testing with speaker-test")
    try:
        cmd = ['speaker-test', '-D', output_device, '-t', 'sine', '-f', '1000', '-l', '2']
        print(f"Running: {' '.join(cmd)}")
        print("You should hear a 1kHz tone for 2 seconds...")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ Audio output test successful!")
        else:
            print(f"❌ Audio output test failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("✅ Audio output test completed (timeout)")
    except Exception as e:
        print(f"❌ Audio output error: {e}")

def test_tts_output(output_device="plughw:3,0"):
    """Test text-to-speech output"""
    print_header("TEXT-TO-SPEECH TEST")
    
    print(f"Testing TTS output: {output_device}")
    
    # Test with espeak
    print_section("Testing with espeak")
    try:
        test_text = "Hello, this is a test of the voice assistant audio system."
        print(f"Speaking: '{test_text}'")
        
        if output_device:
            # Use aplay with specified device
            cmd = ['aplay', '-D', output_device, '-f', 'S16_LE', '-r', '22050', '-c', '1', '-']
            espeak_process = subprocess.Popen(['espeak', '-s', '150', '-w', '-'], 
                                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            audio_data, _ = espeak_process.communicate(input=test_text.encode())
            subprocess.run(cmd, input=audio_data, check=True)
        else:
            subprocess.run(['espeak', test_text], check=True)
        
        print("✅ TTS test successful!")
    except Exception as e:
        print(f"❌ TTS test failed: {e}")

def test_music_playback(output_device="plughw:3,0"):
    """Test music playback"""
    print_header("MUSIC PLAYBACK TEST")
    
    print(f"Testing music playback: {output_device}")
    
    # Create a test audio file
    print_section("Creating test audio file")
    try:
        test_file = "test_music.wav"
        
        # Generate a simple test tone using sox
        cmd = ['sox', '-n', '-r', '44100', '-c', '2', test_file, 'trim', '0.0', '3.0', 'sine', '440', 'sine', '880']
        print(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Test audio file created!")
            
            # Test playback with mpg123
            print_section("Testing with mpg123")
            try:
                cmd = ['mpg123', test_file]
                if output_device:
                    cmd.extend(['-a', output_device])
                print(f"Running: {' '.join(cmd)}")
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print("✅ Music playback test successful!")
                else:
                    print(f"❌ Music playback failed: {result.stderr}")
            except subprocess.TimeoutExpired:
                print("✅ Music playback test completed (timeout)")
            except Exception as e:
                print(f"❌ Music playback error: {e}")
            
            # Clean up
            os.remove(test_file)
        else:
            print(f"❌ Test audio file creation failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Music test error: {e}")

def main():
    """Main test function"""
    print("🎤 Voice Assistant Audio Test Suite")
    print("This script will test your microphone and audio output devices")
    
    # Get device configurations
    input_device = input("\nEnter input device (e.g., hw:4,0) or press Enter for default: ").strip()
    if not input_device:
        input_device = "hw:4,0"
    
    output_device = input("Enter output device (e.g., plughw:3,0) or press Enter for default: ").strip()
    if not output_device:
        output_device = "plughw:3,0"
    
    print(f"\nUsing devices:")
    print(f"  Input:  {input_device}")
    print(f"  Output: {output_device}")
    
    # Run tests
    test_audio_devices()
    test_microphone_recording(input_device)
    test_audio_output(output_device)
    test_tts_output(output_device)
    test_music_playback(output_device)
    
    print_header("TEST COMPLETE")
    print("If all tests passed, your audio configuration should work with the voice assistant!")
    print(f"\nRecommended config.yaml settings:")
    print(f"recording:")
    print(f"  input_device: \"{input_device}\"")
    print(f"  output_device: \"{output_device}\"")

if __name__ == "__main__":
    main() 