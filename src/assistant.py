import logging
import os
import time
from typing import Optional

import yaml

from .wake_word import WakeWordDetector
from .stt import SpeechToText
from .llm_client import OllamaClient
from .tts import TextToSpeech
from .music_player import MusicPlayer

class VoiceAssistant:
    """Top-level orchestrator gluing all modules together."""

    def __init__(self, config_path: str = "config.yaml"):
        # ------------------------------------------------------------------
        # Load YAML configuration
        # ------------------------------------------------------------------
        with open(config_path, "r", encoding="utf-8") as fh:
            cfg = yaml.safe_load(fh)
        self.config = cfg  # store original for reference

        # ------------------------------------------------------------------
        # Logging as early as possible
        # ------------------------------------------------------------------
        logging.basicConfig(
            level=getattr(logging, cfg["logging"]["level"].upper()),
            format="%(asctime)s | %(levelname)-8s | %(message)s",
        )

        # ------------------------------------------------------------------
        # Initialise components
        # ------------------------------------------------------------------
        self.wake_detector = WakeWordDetector(
            keyword_path=cfg["porcupine"]["keyword_path"],
            sensitivity=cfg["porcupine"]["sensitivity"],
            rate=cfg["recording"]["rate"],
            channels=cfg["recording"]["channels"],
            chunk_size=cfg["recording"]["chunk_size"],
            activation_sound=cfg["porcupine"].get("activation_sound", ""),
        )

        self.stt = SpeechToText(
            model_name=cfg["whisper"]["model"],
            rate=cfg["recording"]["rate"],
            channels=cfg["recording"]["channels"],
        )

        # Allow env-variable override so user doesn’t edit YAML on each Pi
        ollama_host = os.getenv("OLLAMA_HOST", cfg["ollama"]["host"])
        self.llm_client = OllamaClient(
            host=ollama_host,
            port=cfg["ollama"]["port"],
            endpoint=cfg["ollama"]["endpoint"],
        )

        self.tts = TextToSpeech(
            voice=cfg["tts"].get("voice"),
            rate=cfg["tts"].get("rate", 150),
        )

        self.music_player = MusicPlayer(
            music_directory=cfg["music"]["directory"],
            player_command=cfg["music"].get("player", "mpg123"),
        )

        self.running = False
        logging.info("VoiceAssistant initialised – ready for wake word")

    # ------------------------------------------------------------------
    # Command processing helpers
    # ------------------------------------------------------------------
    def process_command(self, text: str) -> Optional[str]:
        tl = text.lower().strip()

        # Music – play
        if "play" in tl and ("music" in tl or "song" in tl):
            return self._handle_music_command(text)

        # Music – stop
        if "stop" in tl and ("music" in tl or "song" in tl):
            self.music_player.stop()
            return "Stopping music playback."

        # Default → LLM
        return self.llm_client.send_message(text)

    def _handle_music_command(self, command: str) -> str:
        lowered = command.lower()
        for w in ["play", "music", "song", "track", "please", "can", "you"]:
            lowered = lowered.replace(w, "")
        query = lowered.strip()

        if not query:
            songs = self.music_player.get_available_songs()
            return (
                f"I found {len(songs)} songs. "
                "Please specify which one you'd like me to play."
                if songs
                else "No music files found."
            )

        matches = self.music_player.search_songs(query)
        if not matches:
            return f"I couldn't find any songs matching '{query}'."
        if len(matches) == 1:
            ok = self.music_player.play_song(matches[0])
            return f"Playing {matches[0]}." if ok else f"Couldn't play {matches[0]}."
        return (
            "I found multiple songs: " + ", ".join(matches[:5])[:150] + ". "
            "Please be more specific."
        )

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self):
        self.running = True
        if not self.llm_client.test_connection():
            logging.warning("Ollama server unreachable – LLM features disabled.")

        try:
            for _ in self.wake_detector.listen():
                if not self.running:
                    break

                # Stop any ongoing output so user can interrupt
                self.tts.stop()
                self.music_player.stop()

                try:
                    user_text = self.stt.listen_and_transcribe()
                except Exception as exc:
                    logging.error("STT failure: %s", exc)
                    self.tts.speak("Sorry, I didn't catch that.")
                    continue

                if not user_text:
                    logging.info("No speech detected after wake word")
                    continue

                logging.info("User said: %s", user_text)
                reply = self.process_command(user_text) or "I'm not sure how to help with that."
                self.tts.speak(reply)

                # Tiny pause before re-arming wake word to avoid false triggers
                time.sleep(0.5)

        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt – shutting down assistant")
        finally:
            self.stop()

    def stop(self):
        self.running = False
        self.tts.stop()
        self.music_player.stop()
        self.wake_detector.close()
        logging.info("Assistant stopped – goodbye")


if __name__ == "__main__":
    VoiceAssistant().run()
