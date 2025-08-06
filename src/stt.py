import logging
import audioop
import pyaudio
import wave
import tempfile
import os
from typing import Optional

import whisper

class SpeechToText:
    """Speech-to-text helper that records until the speaker stops and then
    transcribes the captured audio with Whisper. Designed for lightweight
    setup on Raspberry Pi (no extra VAD dependency – energy based silence
    detection only)."""

    def __init__(self, model_name: str = "base", rate: int = 16_000, channels: int = 1):
        self.model_name = model_name
        self.rate = rate
        self.channels = channels

        # Load Whisper model (first call will download weights)
        self.model = whisper.load_model(self.model_name)
        logging.info("Whisper model '%s' loaded", self.model_name)

    # ---------------------------------------------------------------------
    # Recording helpers
    # ---------------------------------------------------------------------
    def _record_until_silence(
        self,
        max_duration: float = 10.0,
        silence_duration: float = 1.0,
        silence_threshold: int = 500,
        chunk: int = 1024,
    ) -> str:
        """Record microphone audio until *silence_duration* seconds of consecutive
        samples fall below *silence_threshold* RMS level or until
        *max_duration* seconds total have elapsed.

        Returns the path to a temporary WAV file containing the recording."""

        audio = pyaudio.PyAudio()
        wav_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        wav_tmp.close()  # we will write later via wave module

        try:
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=chunk,
            )
            logging.info("Listening… (max %.1f s)", max_duration)

            frames = []
            num_silent_chunks_required = int(self.rate / chunk * silence_duration)
            silent_chunks = 0
            total_chunks = 0

            while True:
                data = stream.read(chunk, exception_on_overflow=False)
                frames.append(data)
                total_chunks += 1

                # Calculate RMS energy (0-32767)
                rms = audioop.rms(data, 2)
                if rms < silence_threshold:
                    silent_chunks += 1
                else:
                    silent_chunks = 0  # speech detected – reset counter

                # Stop if enough silence OR max duration exceeded
                if silent_chunks >= num_silent_chunks_required:
                    logging.debug("Silence detected – stopping recording")
                    break
                if total_chunks * chunk / self.rate >= max_duration:
                    logging.debug("Max duration reached – stopping recording")
                    break

            # Close mic stream immediately to free device
            stream.stop_stream()
            stream.close()

            # Write frames to a temporary WAV file
            with wave.open(wav_tmp.name, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.rate)
                wf.writeframes(b"".join(frames))

            logging.info("Recorded %.2f seconds of audio", total_chunks * chunk / self.rate)
            return wav_tmp.name

        except Exception as exc:
            logging.error("Error while recording audio: %s", exc)
            raise
        finally:
            audio.terminate()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def transcribe(self, wav_path: str) -> str:
        """Run Whisper transcription and return plain text (may be empty)."""
        try:
            logging.info("Transcribing audio …")
            result = self.model.transcribe(wav_path)
            text = result.get("text", "").strip()
            logging.info("Transcription: '%s'", text)
            return text
        finally:
            # Always remove temporary file to save SD-card space
            try:
                os.unlink(wav_path)
            except OSError:
                pass

    def listen_and_transcribe(
        self,
        max_duration: float = 10.0,
        silence_duration: float = 1.0,
        silence_threshold: int = 500,
    ) -> str:
        """High-level convenience wrapper used by the assistant."""
        wav_path = self._record_until_silence(
            max_duration=max_duration,
            silence_duration=silence_duration,
            silence_threshold=silence_threshold,
        )
        return self.transcribe(wav_path)
