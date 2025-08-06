import logging
import os
import subprocess
import threading
import time
from typing import List, Optional

class MusicPlayer:
    """
    Music player for local music files using mpg123.
    """
    def __init__(self, music_directory: str, player_command: str = "mpg123", output_device: str = None):
        self.music_directory = music_directory
        self.player_command = player_command
        self.output_device = output_device
        self.current_process: Optional[subprocess.Popen] = None
        self.is_playing = False
        self.current_track = None
        
        # Validate music directory
        if not os.path.exists(self.music_directory):
            logging.warning(f"Music directory {self.music_directory} does not exist.")
        
        logging.info(f"MusicPlayer initialized with directory: {self.music_directory}")

    def get_available_songs(self) -> List[str]:
        """
        Get list of available music files.
        """
        if not os.path.exists(self.music_directory):
            return []
        
        supported_formats = ['.mp3', '.wav', '.ogg', '.flac']
        songs = []
        
        for file in os.listdir(self.music_directory):
            if any(file.lower().endswith(fmt) for fmt in supported_formats):
                songs.append(file)
        
        return sorted(songs)

    def play_song(self, song_name: str) -> bool:
        """
        Play a specific song by name.
        """
        if not os.path.exists(self.music_directory):
            logging.error("Music directory does not exist.")
            return False
        
        song_path = os.path.join(self.music_directory, song_name)
        if not os.path.exists(song_path):
            logging.error(f"Song not found: {song_path}")
            return False
        
        # Stop current playback
        self.stop()
        
        try:
            logging.info(f"Playing song: {song_name}")
            
            # Build command with output device if specified
            cmd = [self.player_command]
            if self.output_device:
                # For plughw: devices, we'll use the device as-is with mpg123
                # The plug layer should handle format conversion automatically
                cmd.extend(['-a', self.output_device])  # mpg123 audio device option
            cmd.append(song_path)
            
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.is_playing = True
            self.current_track = song_name
            
            # Monitor playback in background
            def monitor_playback():
                self.current_process.wait()
                self.is_playing = False
                self.current_track = None
                logging.info(f"Finished playing: {song_name}")
            
            thread = threading.Thread(target=monitor_playback)
            thread.daemon = True
            thread.start()
            
            return True
            
        except Exception as e:
            logging.error(f"Error playing song {song_name}: {e}")
            return False

    def stop(self):
        """
        Stop current playback.
        """
        if self.current_process and self.is_playing:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.current_process.kill()
            except Exception as e:
                logging.error(f"Error stopping playback: {e}")
            
            self.is_playing = False
            self.current_track = None
            logging.info("Playback stopped.")

    def is_playing_now(self) -> bool:
        """
        Check if currently playing music.
        """
        return self.is_playing

    def get_current_track(self) -> Optional[str]:
        """
        Get name of currently playing track.
        """
        return self.current_track

    def search_songs(self, query: str) -> List[str]:
        """
        Search for songs by name.
        """
        all_songs = self.get_available_songs()
        query_lower = query.lower()
        return [song for song in all_songs if query_lower in song.lower()] 