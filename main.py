#!/usr/bin/env python3
"""
Main entry point for the Voice Assistant.
Run this script to start the voice assistant.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.assistant import VoiceAssistant

def main():
    """
    Main function to run the voice assistant.
    """
    try:
        assistant = VoiceAssistant()
        assistant.run()
    except KeyboardInterrupt:
        print("\nShutting down voice assistant...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 