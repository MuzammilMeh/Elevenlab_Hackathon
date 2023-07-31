from elevenlabs import clone, generate, play, set_api_key,voices
import streamlit as st
import json
from elevenlabs.api import History
from utils import global_name

import os

json_name=""
json_personality_trait=""
json_accent=""
def instant_voice_clone(name):
    
    try:
        file_path = f'audio/{name}/audio_info.json'
        folder_path = os.path.join('audio', name)
        mp3_files = [f"./audio/{name}/{file}" for file in os.listdir(folder_path) if file.endswith('.mp3')]

        with open(file_path, 'r') as json_file:
            json_data = json.load(json_file)
   
        print(mp3_files)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        

    set_api_key("f6c901a9e1db35ac8b7df9dc70932d0d")

    voice = clone(
        name=name,
        description= f"A {json_data['voice_type']} voice that is {json_data['personality_trait']} and easy to talk, very calm and composed, takes alot of pauses while taking and even whispers when compassionate, show's alot of emotions and very expressive.",
        labels={"accent":json_data['accent'],"voice type":json_data['voice_type'],"personality":json_data['personality_trait']},
      
        files=mp3_files
    )
    print(json_data['voice_type'],json_data['personality_trait'],json_data['accent'])
    st.success("voice cloned successfully")
    print('voice cloned')
    
    return voice
