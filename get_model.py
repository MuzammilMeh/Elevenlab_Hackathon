from elevenlabs import clone, generate, play, set_api_key,voices,stream
from elevenlabs.api import History
from utils import global_name
import os

set_api_key("4ea3953bf7a5fd8cf5901eeab0e91ac9")
available_voices = voices()[-1]

audio_stream = generate(text="Some very long text to be read by the voice", voice=available_voices)
play(audio_stream)