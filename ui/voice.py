"""TTS/STT wrappers (pyttsx3 + SpeechRecognition) with safe fallbacks.

If `pyttsx3` or `speech_recognition` are not installed, this module
provides lightweight no-op fallbacks so imports don't fail during tests.
"""
import threading
try:
    import pyttsx3
except Exception:
    pyttsx3 = None

try:
    import speech_recognition as sr
except Exception:
    sr = None

_engine = None

def init_tts(rate=170, volume=1.0):
    global _engine
    if _engine or pyttsx3 is None:
        return
    _engine = pyttsx3.init()
    _engine.setProperty('rate', rate); _engine.setProperty('volume', volume)
    v = _engine.getProperty('voices')
    if v:
        _engine.setProperty('voice', v[0].id)

def speak(text, block=False):
    # No-op when TTS is unavailable
    if pyttsx3 is None:
        return None
    init_tts()
    def _say():
        _engine.say(text); _engine.runAndWait()
    if block:
        _say()
    else:
        t = threading.Thread(target=_say, daemon=True); t.start()

def listen_once(timeout=5, phrase_time_limit=8):
    if sr is None:
        return None
    r = sr.Recognizer()
    try:
        with sr.Microphone() as src:
            print('[voice] listening...')
            audio = r.listen(src, timeout=timeout, phrase_time_limit=phrase_time_limit)
        txt = r.recognize_google(audio)
        return txt
    except Exception as e:
        print('[voice] stt error:', e)
        return None

def input_with_voice_fallback():
    txt = listen_once()
    if txt:
        return txt
    return input('You: ')
