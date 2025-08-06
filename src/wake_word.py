import logging
import pyaudio
import struct
import subprocess
import threading
import os
import numpy as np
from typing import Optional

import openwakeword

class WakeWordDetector:
    """
    Wake word detector using openWakeWord and PyAudio.
    """
    def __init__(self, wake_word: str = "jarvis", sensitivity: float = 0.5,
                 rate: int = 16000, channels: int = 1, chunk_size: int = 512,
                 activation_sound: str = None, input_device: str = None):
        self.wake_word = wake_word.lower()
        self.sensitivity = sensitivity
        self.rate = rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.activation_sound = activation_sound
        self.input_device = input_device

        # Initialize openWakeWord
        try:
            # Load the openWakeWord model
            self.oww = openwakeword.Model(
                wakeword_models=[self.wake_word],
                inference_framework="onnx"
            )
            logging.info(f"openWakeWord initialized with wake word: {self.wake_word}")
        except Exception as e:
            logging.error(f"Failed to initialize openWakeWord: {e}")
            # Try to use a default model if the specified one doesn't exist
            try:
                self.oww = openwakeword.Model(
                    wakeword_models=["jarvis"],
                    inference_framework="onnx"
                )
                self.wake_word = "jarvis"
                logging.info("Using default 'jarvis' wake word model")
            except Exception as e2:
                logging.error(f"Failed to initialize default model: {e2}")
                raise

        # Initialize audio stream
        self.audio = pyaudio.PyAudio()
        
        # Get device index if specified
        input_device_index = None
        if hasattr(self, 'input_device') and self.input_device:
            # Find device index by name
            for i in range(self.audio.get_device_count()):
                device_info = self.audio.get_device_info_by_index(i)
                if self.input_device in device_info['name']:
                    input_device_index = i
                    logging.info(f"Using input device: {device_info['name']}")
                    break
        
        self.stream = self.audio.open(
            rate=self.rate,
            channels=self.channels,
            format=pyaudio.paInt16,
            input=True,
            input_device_index=input_device_index,
            frames_per_buffer=self.chunk_size
        )
        logging.info("WakeWordDetector initialized.")

    def _play_activation_sound(self):
        """
        Play activation sound to indicate wake word detection.
        """
        if not self.activation_sound:
            return
            
        def play_sound():
            try:
                if self.activation_sound.endswith('.wav'):
                    # Play WAV file
                    subprocess.run(['aplay', '-q', self.activation_sound], 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif self.activation_sound.endswith('.mp3'):
                    # Play MP3 file
                    subprocess.run(['mpg123', '-q', self.activation_sound], 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    # Generate a simple beep tone using sox or speaker-test
                    try:
                        subprocess.run(['speaker-test', '-t', 'sine', '-f', '800', '-l', '1'], 
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1)
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        # Fallback: try sox if available
                        try:
                            subprocess.run(['sox', '-n', '-r', '44100', '-c', '1', '-t', 'wav', '-', 
                                          'trim', '0.0', '0.2', 'sine', '800'], 
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        except FileNotFoundError:
                            logging.warning("No audio playback tools available for activation sound")
            except Exception as e:
                logging.error(f"Error playing activation sound: {e}")
        
        # Play sound in background thread to avoid blocking wake word detection
        thread = threading.Thread(target=play_sound, daemon=True)
        thread.start()

    def _audio_to_numpy(self, audio_data: bytes) -> np.ndarray:
        """
        Convert PyAudio audio data to numpy array.
        """
        # Convert bytes to 16-bit integers
        audio_int16 = struct.unpack(f"{len(audio_data)//2}h", audio_data)
        # Convert to float32 and normalize
        audio_float32 = np.array(audio_int16, dtype=np.float32) / 32768.0
        return audio_float32

    def listen(self):
        """
        Generator that yields when the wake word is detected.
        """
        logging.info(f"Listening for wake word: {self.wake_word}")
        
        # Buffer for accumulating audio data
        audio_buffer = np.array([], dtype=np.float32)
        buffer_size = int(self.rate * 0.5)  # 500ms buffer
        
        try:
            while True:
                # Read raw audio
                pcm = self.stream.read(self.chunk_size, exception_on_overflow=False)
                
                # Convert to numpy array
                audio_chunk = self._audio_to_numpy(pcm)
                
                # Add to buffer
                audio_buffer = np.concatenate([audio_buffer, audio_chunk])
                
                # Keep only the last buffer_size samples
                if len(audio_buffer) > buffer_size:
                    audio_buffer = audio_buffer[-buffer_size:]
                
                # Process with openWakeWord when we have enough data
                if len(audio_buffer) >= buffer_size:
                    try:
                        # Predict wake word
                        prediction = self.oww.predict(audio_buffer)
                        
                        # Check if wake word was detected
                        if prediction[self.wake_word] > self.sensitivity:
                            logging.info(f"Wake word '{self.wake_word}' detected! Confidence: {prediction[self.wake_word]:.3f}")
                            # Play activation sound
                            self._play_activation_sound()
                            # Clear buffer to avoid multiple detections
                            audio_buffer = np.array([], dtype=np.float32)
                            yield
                            
                    except Exception as e:
                        logging.error(f"Error in wake word prediction: {e}")
                        continue
                        
        except Exception as e:
            logging.error(f"Error in wake word detection: {e}")
            raise

    def close(self):
        """
        Clean up audio and openWakeWord resources.
        """
        try:
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()
            logging.info("WakeWordDetector resources released.")
        except Exception as e:
            logging.error(f"Error closing WakeWordDetector: {e}")