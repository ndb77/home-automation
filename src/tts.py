import logging
import threading
import subprocess
from typing import Optional

class TextToSpeech:
    """Simple TTS wrapper using espeak directly for Raspberry Pi compatibility."""

    def __init__(self, voice: Optional[str] = None, rate: int = 150, fallback_cmd: str = "espeak", output_device: str = None):
        self.voice = voice
        self.rate = rate
        self.fallback_cmd = fallback_cmd
        self.output_device = output_device
        self._is_speaking = False
        
        logging.info("TextToSpeech initialised (espeak, output_device=%s)", self.output_device)

    def speak(self, text: str, interruptible: bool = True):
        """Speak the given text using espeak."""
        if not text.strip():
            return

        def _speak_with_espeak():
            try:
                if self.output_device:
                    # Generate audio with espeak and pipe to aplay with specified device
                    espeak_process = subprocess.Popen(['espeak', '-s', str(self.rate), '-w', '-'], 
                                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                    audio_data, _ = espeak_process.communicate(input=text.encode())
                    subprocess.run(['aplay', '-D', self.output_device, '-f', 'S16_LE', '-r', '22050', '-c', '1', '-'], 
                                 input=audio_data, check=True, stderr=subprocess.DEVNULL)
                else:
                    # Use default espeak
                    subprocess.run([self.fallback_cmd, '-s', str(self.rate), text], 
                                 check=True, stderr=subprocess.DEVNULL)
            except Exception as exc:
                logging.error("TTS failed: %s", exc)
            finally:
                self._is_speaking = False

        if interruptible:
            self._is_speaking = True
            thread = threading.Thread(target=_speak_with_espeak, daemon=True)
            thread.start()
        else:
            _speak_with_espeak()

    def stop(self):
        """Stop any ongoing speech."""
        if self._is_speaking:
            # For espeak, we can't easily stop it, but we can mark it as stopped
            self._is_speaking = False
            logging.info("Speech stopped")

    def is_speaking_now(self) -> bool:
        """Check if currently speaking."""
        return self._is_speaking
