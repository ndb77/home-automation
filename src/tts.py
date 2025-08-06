import logging
import threading
import subprocess
from typing import Optional

import pyttsx3

class TextToSpeech:
    """Wrapper around *pyttsx3* with CLI fallback (e.g. *espeak*).

    Raspberry Pi audio can be finicky – if the TTS engine raises an
    exception we fall back to the `espeak` command-line program which is
    usually pre-installed or available via `apt install espeak`.
    """

    def __init__(self, voice: Optional[str] = None, rate: int = 150, fallback_cmd: str = "espeak", output_device: str = None):
        self.engine = pyttsx3.init()
        self.voice = voice
        self.rate = rate
        self.fallback_cmd = fallback_cmd
        self.output_device = output_device

        self.engine.setProperty("rate", self.rate)
        if self.voice:
            # Try to find the specified voice
            voice_found = False
            for v in self.engine.getProperty("voices"):
                if self.voice.lower() in v.name.lower():
                    self.engine.setProperty("voice", v.id)
                    voice_found = True
                    logging.info(f"Using voice: {v.name}")
                    break
            
            if not voice_found:
                logging.warning(f"Voice '{self.voice}' not found, using default voice")
        else:
            logging.info("No voice specified, using default system voice")

        self._is_speaking = False
        logging.info("TextToSpeech initialised (pyttsx3, fallback=%s)", self.fallback_cmd)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def speak(self, text: str, interruptible: bool = True):
        if not text.strip():
            return

        def _speak_with_engine():
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as exc:
                logging.error("pyttsx3 error: %s – falling back to '%s'", exc, self.fallback_cmd)
                self._speak_fallback(text)
            finally:
                self._is_speaking = False

        if interruptible:
            self._is_speaking = True
            thread = threading.Thread(target=_speak_with_engine, daemon=True)
            thread.start()
        else:
            _speak_with_engine()

    def _speak_fallback(self, text: str):
        try:
            # Use specified output device if configured
            if self.output_device:
                # Generate audio with espeak and pipe to aplay with specified device
                espeak_process = subprocess.Popen(['espeak', '-s', '150', '-w', '-'], 
                                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                audio_data, _ = espeak_process.communicate(input=text.encode())
                subprocess.run(['aplay', '-D', self.output_device, '-f', 'S16_LE', '-r', '22050', '-c', '1', '-'], 
                             input=audio_data, check=True)
            else:
                # Use default espeak
                subprocess.run([self.fallback_cmd, text], check=True)
        except Exception as exc:
            logging.error("Fallback TTS failed: %s", exc)

    def stop(self):
        if self._is_speaking:
            try:
                self.engine.stop()
            except Exception:
                pass
            self._is_speaking = False
            logging.info("Speech stopped")

    def is_speaking_now(self) -> bool:
        return self._is_speaking
