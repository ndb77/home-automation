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

    def __init__(self, voice: Optional[str] = None, rate: int = 150, fallback_cmd: str = "espeak"):
        self.engine = pyttsx3.init()
        self.voice = voice
        self.rate = rate
        self.fallback_cmd = fallback_cmd

        self.engine.setProperty("rate", self.rate)
        if self.voice:
            for v in self.engine.getProperty("voices"):
                if self.voice.lower() in v.name.lower():
                    self.engine.setProperty("voice", v.id)
                    break

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
