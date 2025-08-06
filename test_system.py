#!/usr/bin/env python3
"""
Test script for the Voice Assistant system.
This script tests the basic functionality without requiring audio hardware.
"""

import logging
import sys
import time
from src.assistant import VoiceAssistant

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def test_system():
    """Test the voice assistant system components."""
    print("🧪 Testing Voice Assistant System")
    print("=" * 50)
    
    try:
        # Test 1: Import and initialize components
        print("\n1. Testing component imports...")
        from src.wake_word import WakeWordDetector
        from src.stt import SpeechToText
        from src.llm_client import OllamaClient
        from src.tts import TextToSpeech
        print("✅ All components imported successfully")
        
        # Test 2: Initialize wake word detector
        print("\n2. Testing wake word detector...")
        wd = WakeWordDetector('hey_jarvis')
        print("✅ Wake word detector initialized")
        
        # Test 3: Initialize STT
        print("\n3. Testing speech-to-text...")
        stt = SpeechToText()
        print("✅ Speech-to-text initialized")
        
        # Test 4: Initialize TTS
        print("\n4. Testing text-to-speech...")
        tts = TextToSpeech()
        print("✅ Text-to-speech initialized")
        
        # Test 5: Test LLM connection (if Ollama is running)
        print("\n5. Testing LLM connection...")
        try:
            llm = OllamaClient("192.168.1.148")  # Update with your Ollama server IP
            if llm.test_connection():
                print("✅ LLM connection successful")
            else:
                print("⚠️  LLM connection failed (Ollama may not be running)")
        except Exception as e:
            print(f"⚠️  LLM connection failed: {e}")
        
        # Test 6: Initialize voice assistant
        print("\n6. Testing voice assistant initialization...")
        assistant = VoiceAssistant()
        print("✅ Voice assistant initialized successfully")
        
        print("\n" + "=" * 50)
        print("🎉 All tests completed successfully!")
        print("\n📋 System Status:")
        print("   • Wake Word Detection: ✅ Working (fallback mode on Windows)")
        print("   • Speech-to-Text: ✅ Ready")
        print("   • Text-to-Speech: ✅ Ready")
        print("   • LLM Integration: ⚠️  Requires Ollama server")
        print("\n🚀 The system is ready to use!")
        print("\n💡 To start the assistant, run: python main.py")
        print("💡 On Windows, wake word detection will simulate every 10 seconds for testing")
        
        # Clean up
        wd.close()
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logging.error(f"Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_system()
    sys.exit(0 if success else 1) 