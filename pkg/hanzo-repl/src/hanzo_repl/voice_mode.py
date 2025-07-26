"""Voice mode for bidirectional communication."""

import asyncio
import threading
import queue
import time
from typing import Optional, Callable

try:
    import speech_recognition as sr
    import pyttsx3
    import sounddevice as sd
    import numpy as np
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False


class VoiceMode:
    """Handles voice input/output for the REPL."""
    
    def __init__(self):
        if not VOICE_AVAILABLE:
            raise ImportError("Voice dependencies not installed. Run: pip install speechrecognition pyttsx3 pyaudio")
            
        # Speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Text to speech
        self.tts_engine = pyttsx3.init()
        self._setup_tts()
        
        # State
        self.is_active = False
        self.is_listening = False
        self.speech_queue = queue.Queue()
        self.stop_event = threading.Event()
        
        # Callbacks
        self.on_speech_recognized = None
        self.on_listening_started = None
        self.on_listening_stopped = None
        
    def _setup_tts(self):
        """Configure TTS engine."""
        # Set properties
        voices = self.tts_engine.getProperty('voices')
        
        # Try to find a nice voice (prefer female voices)
        for voice in voices:
            if 'female' in voice.name.lower() or 'samantha' in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break
        
        # Set rate and volume
        self.tts_engine.setProperty('rate', 180)  # Speed
        self.tts_engine.setProperty('volume', 0.9)  # Volume
    
    def start(self, on_speech: Optional[Callable[[str], None]] = None):
        """Start voice mode."""
        self.is_active = True
        self.on_speech_recognized = on_speech
        
        # Start listening thread
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        
        # Play activation sound
        self._play_sound("activated")
        self.speak("Voice mode activated. I'm listening.")
    
    def stop(self):
        """Stop voice mode."""
        self.is_active = False
        self.stop_event.set()
        
        # Play deactivation sound
        self._play_sound("deactivated")
        self.speak("Voice mode deactivated.")
        
        # Wait for thread to stop
        if hasattr(self, 'listen_thread'):
            self.listen_thread.join(timeout=2)
    
    def _listen_loop(self):
        """Main listening loop."""
        with self.microphone as source:
            # Adjust for ambient noise
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            while self.is_active and not self.stop_event.is_set():
                try:
                    # Signal listening started
                    self.is_listening = True
                    if self.on_listening_started:
                        self.on_listening_started()
                    
                    # Listen with timeout
                    audio = self.recognizer.listen(
                        source,
                        timeout=1,
                        phrase_time_limit=10
                    )
                    
                    # Signal listening stopped
                    self.is_listening = False
                    if self.on_listening_stopped:
                        self.on_listening_stopped()
                    
                    # Recognize speech
                    try:
                        text = self.recognizer.recognize_google(audio)
                        if text and self.on_speech_recognized:
                            self.on_speech_recognized(text)
                    except sr.UnknownValueError:
                        # Could not understand audio
                        pass
                    except sr.RequestError as e:
                        # API error
                        if self.on_speech_recognized:
                            self.on_speech_recognized(f"[Voice Error: {e}]")
                            
                except sr.WaitTimeoutError:
                    # No speech detected
                    self.is_listening = False
                    continue
                except Exception as e:
                    # Other error
                    self.is_listening = False
                    if self.on_speech_recognized:
                        self.on_speech_recognized(f"[Voice Error: {e}]")
                    time.sleep(0.5)
    
    def speak(self, text: str, wait: bool = False):
        """Convert text to speech."""
        def _speak():
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        
        if wait:
            _speak()
        else:
            # Run in thread to avoid blocking
            threading.Thread(target=_speak, daemon=True).start()
    
    def _play_sound(self, sound_type: str):
        """Play UI sounds."""
        # Generate simple beeps using sounddevice
        try:
            duration = 0.1
            sample_rate = 44100
            
            if sound_type == "activated":
                # Rising tone
                frequency = [440, 880]
            elif sound_type == "deactivated":
                # Falling tone
                frequency = [880, 440]
            else:
                frequency = [440]
            
            # Generate and play tones
            for freq in frequency:
                t = np.linspace(0, duration, int(sample_rate * duration))
                wave = 0.3 * np.sin(2 * np.pi * freq * t)
                sd.play(wave, sample_rate)
                sd.wait()
                
        except Exception:
            # Fallback to TTS beep
            pass


class VoiceCommands:
    """Voice command processor."""
    
    WAKE_WORDS = ["hey hanzo", "hanzo", "computer", "assistant"]
    STOP_WORDS = ["stop", "cancel", "never mind", "exit voice"]
    
    @staticmethod
    def process_voice_input(text: str) -> tuple[str, bool]:
        """Process voice input and extract commands."""
        text_lower = text.lower()
        
        # Check for stop commands
        for stop_word in VoiceCommands.STOP_WORDS:
            if stop_word in text_lower:
                return "", True
        
        # Remove wake words
        for wake_word in VoiceCommands.WAKE_WORDS:
            if text_lower.startswith(wake_word):
                text = text[len(wake_word):].strip()
                break
        
        # Voice shortcuts
        voice_shortcuts = {
            "run command": "!",
            "bash": "!",
            "search for": "/search",
            "find file": "@",
            "memorize this": "#",
            "show commands": "cmd+k",
            "clear screen": "ctrl+l",
            "what can you do": "?",
        }
        
        for voice_cmd, shortcut in voice_shortcuts.items():
            if text_lower.startswith(voice_cmd):
                remainder = text[len(voice_cmd):].strip()
                return f"{shortcut} {remainder}", False
        
        return text, False