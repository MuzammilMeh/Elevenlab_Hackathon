import streamlit as st
import base64
import os
import json

all_samples=[]
global_name=""

# Function to get voice samples from the user
def get_voice_sample():
    voice_sample = st.file_uploader(
        "Upload Voice Sample:",
        type=["mp3", "wav"],  # Specify accepted file types (you can add more if needed)
        key="voice_sample",
    )
    if voice_sample is not None:
        all_samples.append(voice_sample)
    return voice_sample


def upload_voice_semantics(user_data):
    flag=False
    global_name=user_data['name']
    os.makedirs('audio', exist_ok=True)
    audio_info = {
        'name': user_data['name'],
        'personality_trait': user_data['personality_trait'],
        'accent': user_data['accent'],
        'voice_type': user_data['voice_type'],
    }

    # Create a subfolder using the 'name' field from the audio object
    subfolder_path = os.path.join('audio', user_data['name'])
    os.makedirs(subfolder_path, exist_ok=True)

    # Save each audio file to the subfolder
    for audio_file in user_data['voice_samples']:
        file_path = os.path.join(subfolder_path, audio_file.name)
        with open(file_path, 'wb') as local_file:
            local_file.write(audio_file.getbuffer())
            flag=True


      # Save the audio info as a JSON file in the 'audio' folder
    info_file_path = os.path.join(subfolder_path, 'audio_info.json')
    with open(info_file_path, 'w') as info_file:
        json.dump(audio_info, info_file)
        flag=True

    return True if flag==True else False

   


