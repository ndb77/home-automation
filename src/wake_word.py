import logging
import pvporcupine
import pyaudio
import struct
import subprocess
import threading
import os

class WakeWordDetector:
    """
    Wake word detector using Porcupine and PyAudio.
    """
    def __init__(self, keyword_path: str, sensitivity: float,
                 rate: int = 16000, channels: int = 1, chunk_size: int = 512,
                 activation_sound: str = None):
        self.keyword_path = keyword_path
        self.sensitivity = sensitivity
        self.rate = rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.activation_sound = activation_sound

        # Initialize Porcupine
        self.porcupine = pvporcupine.create(
            keyword_paths=[self.keyword_path],
            sensitivities=[self.sensitivity]
        )
        # Initialize audio stream
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            rate=self.rate,
            channels=self.channels,
            format=pyaudio.paInt16,
            input=True,
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

    def listen(self):
        """
        Generator that yields when the wake word is detected.
        """
        logging.info("Listening for wake word...")
        try:
            while True:
                # Read raw audio
                pcm = self.stream.read(self.chunk_size, exception_on_overflow=False)
                # Unpack to signed 16-bit little endian samples
                pcm_unpacked = struct.unpack_from(
                    "h" * self.chunk_size, pcm
                )
                # Process with Porcupine
                result = self.porcupine.process(pcm_unpacked)
                if result >= 0:
                    logging.info("Wake word detected!")
                    # Play activation sound
                    self._play_activation_sound()
                    yield
        except Exception as e:
            logging.error(f"Error in wake word detection: {e}")
            raise

    def close(self):
        """
        Clean up audio and Porcupine resources.
        """
        try:
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()
            self.porcupine.delete()
            logging.info("WakeWordDetector resources released.")
        except Exception as e:
            logging.error(f"Error closing WakeWordDetector: {e}")