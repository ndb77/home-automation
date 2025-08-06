# Voice Assistant - Raspberry Pi Home Automation

A comprehensive voice-controlled home assistant built for Raspberry Pi that uses wake word detection, speech-to-text, and local LLM processing to provide an intelligent voice interface.

## Features

- **Wake Word Detection**: Uses Porcupine for reliable "Jarvis" wake word detection
- **Speech-to-Text**: Whisper-based transcription for accurate voice recognition
- **Local LLM Integration**: Connects to Ollama server running on Windows desktop
- **Text-to-Speech**: Natural voice responses using pyttsx3
- **Music Playback**: Local music file playback with voice commands
- **Interrupt Support**: Can interrupt responses when wake word is detected
- **Headless Operation**: Designed for SSH-based Raspberry Pi deployment
- **Error Handling**: Robust error handling for network issues and failures

## System Requirements

### Raspberry Pi (Headless)
- Raspberry Pi 3 or 4 (recommended)
- Raspberry Pi OS Lite
- Microphone and speakers/audio output
- Network connection to Windows desktop

### Windows Desktop
- Ollama installed and running
- Network accessible from Raspberry Pi

## Installation

### 1. Clone and Setup Repository

```bash
git clone https://github.com/yourusername/home-automation.git
cd home-automation
```

### 2. Install Dependencies

```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3-pip python3-venv portaudio19-dev mpg123 wget

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Run Porcupine setup script (optional but recommended)
chmod +x scripts/setup_porcupine.sh
./scripts/setup_porcupine.sh
```

### 3. Install Porcupine and Download Wake Word

#### Option A: Using pip (Recommended)
```bash
# Porcupine is already included in requirements.txt
# It will be installed when you run: pip install -r requirements.txt
```

#### Option B: Manual Installation
```bash
# Install Porcupine Python package
pip install pvporcupine

# Or install specific version for Raspberry Pi
pip install pvporcupine==1.9.0
```

#### Get the Wake Word File (.ppn)

1. **Go to Picovoice Console**: https://console.picovoice.ai/
2. **Sign up/Login** (free account)
3. **Create a new wake word**:
   - Click "Create Wake Word"
   - Name it "Jarvis" 
   - Record or upload audio saying "Jarvis" clearly
   - Select "Linux ARM" platform
   - Download the `.ppn` file

4. **Place the file**:
```bash
# Create directory
mkdir -p ~/porcupine/keywords

# Copy your downloaded file (replace with actual path)
cp ~/Downloads/jarvis_linux.ppn ~/porcupine/keywords/

# Verify the file exists
ls -la ~/porcupine/keywords/
```

#### Alternative: Use Built-in Wake Words
If you don't want to create a custom wake word, you can use Picovoice's built-in ones:
```bash
# Download a built-in wake word (e.g., "Picovoice")
wget https://github.com/Picovoice/porcupine/raw/master/resources/keyword_files/linux/arm/picovoice_linux.ppn -O ~/porcupine/keywords/picovoice_linux.ppn

# Then update config.yaml to use "Picovoice" instead of "Jarvis"
```

### 4. Configure the System

Edit `config.yaml` with your settings:

```yaml
# Update the Windows machine IP address
ollama:
  host: "192.168.1.100"  # Your Windows machine IP

# Set your music directory
music:
  directory: "/home/pi/music"

# Adjust wake word sensitivity if needed
porcupine:
  sensitivity: 0.5
  # Optional: Custom activation sound (WAV or MP3 file)
  # Leave empty for default beep tone
  activation_sound: ""
  # Startup sound settings
  startup_sound:
    enabled: true
    frequency: 1000  # Hz (higher pitch than activation sound)
    duration: 1      # seconds
```

### 5. Setup Music Directory

```bash
mkdir -p ~/music
# Copy your music files to ~/music/
```

## Usage

### Starting the Assistant

```bash
# Activate virtual environment
source venv/bin/activate

# Run the assistant
python main.py
```

### Voice Commands

- **Startup**: System plays a high-pitched beep when ready to listen
- **Wake Word**: Say "Jarvis" to activate (you'll hear a lower-pitched beep tone)
- **General Questions**: Ask anything after the wake word
- **Music Commands**: 
  - "Play music [song name]"
  - "Stop music"
- **Conversation**: Natural conversation with the LLM

### Headless Deployment

To run the assistant as a service on boot:

```bash
# Create systemd service file
sudo nano /etc/systemd/system/voice-assistant.service
```

Add the following content:

```ini
[Unit]
Description=Voice Assistant
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/home-automation
Environment=PATH=/home/pi/home-automation/venv/bin
ExecStart=/home/pi/home-automation/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable voice-assistant
sudo systemctl start voice-assistant
sudo systemctl status voice-assistant
```

## Project Structure

```
home-automation/
├── src/                    # Source code
│   ├── wake_word.py       # Wake word detection
│   ├── stt.py             # Speech-to-text
│   ├── llm_client.py      # Ollama LLM communication
│   ├── tts.py             # Text-to-speech
│   ├── music_player.py    # Music playback
│   ├── assistant.py       # Main orchestration
│   └── __init__.py        # Package initialization
├── config.yaml            # Configuration file
├── requirements.txt       # Python dependencies
├── main.py               # Entry point
└── README.md             # This file
```

## Configuration

The `config.yaml` file contains all system parameters:

- **Wake Word**: Porcupine keyword file path and sensitivity
- **Audio**: Recording parameters (rate, channels, chunk size)
- **Whisper**: STT model selection
- **Ollama**: LLM server connection details
- **TTS**: Text-to-speech engine settings
- **Music**: Player and directory configuration

## Troubleshooting

### Common Issues

1. **No Audio Input/Output**
   ```bash
   # Check audio devices
   aplay -l
   arecord -l
   
   # Test microphone
   arecord -D hw:1,0 -f S16_LE -r 16000 -c 1 test.wav
   ```

2. **Porcupine Not Working**
   - Verify wake word file path in config.yaml
   - Check file permissions: `chmod 644 ~/porcupine/keywords/*.ppn`
   - Test with different sensitivity values (0.3-0.8)
   - Ensure activation sound file exists (if specified)
   - Verify you downloaded the correct platform (Linux ARM for Pi)
   - Try a built-in wake word first: `picovoice_linux.ppn`

3. **Ollama Connection Issues**
   - Verify Windows machine IP address
   - Check if Ollama is running: `curl http://192.168.1.100:11434/api/tags`
   - Ensure firewall allows port 11434

4. **Whisper Model Issues**
   - First run will download the model (may take time)
   - Check available disk space
   - Try smaller model (tiny, base) for limited resources

### Logs

Check system logs:
```bash
# If running as service
sudo journalctl -u voice-assistant -f

# If running manually, logs appear in console
```

## Development

### Testing Individual Components

```bash
# Test wake word detection
python -c "from src.wake_word import WakeWordDetector; wd = WakeWordDetector('/home/pi/porcupine/keywords/jarvis_linux.ppn'); print('Wake word detector ready')"

# Test STT
python -c "from src.stt import SpeechToText; stt = SpeechToText(); print('STT ready')"

# Test LLM connection
python -c "from src.llm_client import OllamaClient; client = OllamaClient('192.168.1.100'); print('Connected:', client.test_connection())"
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions, please open an issue on GitHub or contact the maintainers. 