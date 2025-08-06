import logging
import pyaudio
import struct
import subprocess
import threading
import os
import numpy as np
from typing import Optional
import time

try:
    import openwakeword
    OPENWAKEWORD_AVAILABLE = True
except ImportError:
    OPENWAKEWORD_AVAILABLE = False
    logging.warning("openWakeWord not available, using fallback keyword detection")

class SimpleWakeWordDetector:
    """
    Simple wake word detector using keyword matching as fallback.
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
        
        # Try to open audio stream with error handling
        try:
            self.stream = self.audio.open(
                rate=self.rate,
                channels=self.channels,
                format=pyaudio.paInt16,
                input=True,
                input_device_index=input_device_index,
                frames_per_buffer=self.chunk_size
            )
        except Exception as e:
            logging.error(f"Failed to open audio stream with device {input_device_index}: {e}")
            # Try with default device and no specific device
            logging.info("Trying with default audio device...")
            try:
                self.stream = self.audio.open(
                    rate=self.rate,
                    channels=self.channels,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=self.chunk_size
                )
            except Exception as e2:
                logging.error(f"Failed to open default audio device: {e2}")
                # Try with 44.1kHz as fallback
                if self.rate != 44100:
                    logging.info("Trying with 44.1kHz sample rate...")
                    self.rate = 44100
                    self.stream = self.audio.open(
                        rate=self.rate,
                        channels=self.channels,
                        format=pyaudio.paInt16,
                        input=True,
                        frames_per_buffer=self.chunk_size
                    )
                else:
                    raise
        
        # Simple keyword detection (for testing)
        self.last_detection_time = 0
        self.detection_cooldown = 2.0  # seconds
        
        logging.info("SimpleWakeWordDetector initialized (fallback mode)")

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

    def listen(self):
        """
        Generator that yields when the wake word is detected.
        For fallback mode, this simulates detection every 10 seconds for testing.
        """
        logging.info(f"Listening for wake word: {self.wake_word} (fallback mode)")
        
        try:
            while True:
                # Simulate wake word detection every 10 seconds for testing
                current_time = time.time()
                if current_time - self.last_detection_time > 10:
                    logging.info(f"Simulated wake word '{self.wake_word}' detection (fallback mode)")
                    self._play_activation_sound()
                    self.last_detection_time = current_time
                    yield
                
                time.sleep(0.1)  # Small delay to prevent high CPU usage
                        
        except Exception as e:
            logging.error(f"Error in wake word detection: {e}")
            raise

    def close(self):
        """
        Clean up audio resources.
        """
        try:
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()
            logging.info("SimpleWakeWordDetector resources released.")
        except Exception as e:
            logging.error(f"Error closing SimpleWakeWordDetector: {e}")

class WakeWordDetector:
    """
    Wake word detector using openWakeWord and PyAudio.
    Falls back to simple keyword detection if openWakeWord is not available.
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

        # Check if openWakeWord is available and working
        if not OPENWAKEWORD_AVAILABLE:
            logging.warning("openWakeWord not available, using fallback detector")
            self.detector = SimpleWakeWordDetector(
                wake_word=self.wake_word,
                sensitivity=self.sensitivity,
                rate=self.rate,
                channels=self.channels,
                chunk_size=self.chunk_size,
                activation_sound=self.activation_sound,
                input_device=self.input_device
            )
            return

        # Initialize openWakeWord
        try:
            # Download models if they don't exist
            try:
                logging.info("Downloading openWakeWord models...")
                openwakeword.utils.download_models()
                logging.info("Models downloaded successfully")
            except Exception as download_error:
                logging.warning(f"Model download failed: {download_error}")
                # Continue anyway, the Model class might handle missing models gracefully
            
            # Try TFLite first (for Linux/Raspberry Pi)
            try:
                self.oww = openwakeword.Model(
                    wakeword_models=[self.wake_word],
                    inference_framework="tflite"
                )
                logging.info(f"openWakeWord initialized with TFLite framework and wake word: {self.wake_word}")
            except Exception as tflite_error:
                logging.warning(f"TFLite framework failed: {tflite_error}")
                # Try ONNX framework as fallback
                try:
                    self.oww = openwakeword.Model(
                        wakeword_models=[self.wake_word],
                        inference_framework="onnx"
                    )
                    logging.info(f"openWakeWord initialized with ONNX framework and wake word: {self.wake_word}")
                except Exception as onnx_error:
                    logging.warning(f"ONNX framework failed: {onnx_error}")
                    # Try with available models
                    available_models = openwakeword.get_pretrained_model_paths()
                    logging.info(f"Available models: {available_models}")
                    
                    # Try to find a compatible model
                    if "hey_jarvis" in str(available_models):
                        self.oww = openwakeword.Model(
                            wakeword_models=["hey_jarvis"],
                            inference_framework="tflite"
                        )
                        self.wake_word = "hey_jarvis"
                        logging.info("Using 'hey_jarvis' wake word model")
                    elif "alexa" in str(available_models):
                        self.oww = openwakeword.Model(
                            wakeword_models=["alexa"],
                            inference_framework="tflite"
                        )
                        self.wake_word = "alexa"
                        logging.info("Using 'alexa' wake word model")
                    else:
                        raise Exception("No compatible wake word models found")
                        
        except Exception as e:
            logging.error(f"Failed to initialize openWakeWord: {e}")
            logging.info("Falling back to simple keyword detection")
            self.detector = SimpleWakeWordDetector(
                wake_word=self.wake_word,
                sensitivity=self.sensitivity,
                rate=self.rate,
                channels=self.channels,
                chunk_size=self.chunk_size,
                activation_sound=self.activation_sound,
                input_device=self.input_device
            )
            return

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
        
        # Try to open audio stream with error handling
        try:
            self.stream = self.audio.open(
                rate=self.rate,
                channels=self.channels,
                format=pyaudio.paInt16,
                input=True,
                input_device_index=input_device_index,
                frames_per_buffer=self.chunk_size
            )
        except Exception as e:
            logging.error(f"Failed to open audio stream with device {input_device_index}: {e}")
            # Try with default device and no specific device
            logging.info("Trying with default audio device...")
            try:
                self.stream = self.audio.open(
                    rate=self.rate,
                    channels=self.channels,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=self.chunk_size
                )
            except Exception as e2:
                logging.error(f"Failed to open default audio device: {e2}")
                # Try with 44.1kHz as fallback
                if self.rate != 44100:
                    logging.info("Trying with 44.1kHz sample rate...")
                    self.rate = 44100
                    self.stream = self.audio.open(
                        rate=self.rate,
                        channels=self.channels,
                        format=pyaudio.paInt16,
                        input=True,
                        frames_per_buffer=self.chunk_size
                    )
                else:
                    raise
        
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
        # If using fallback detector, delegate to it
        if hasattr(self, 'detector'):
            for _ in self.detector.listen():
                yield
            return
            
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
            if hasattr(self, 'detector'):
                self.detector.close()
            else:
                self.stream.stop_stream()
                self.stream.close()
                self.audio.terminate()
            logging.info("WakeWordDetector resources released.")
        except Exception as e:
            logging.error(f"Error closing WakeWordDetector: {e}")