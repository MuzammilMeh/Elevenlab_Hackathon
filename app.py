import streamlit as st
import json
from utils import get_voice_sample, all_samples, upload_voice_semantics, global_name
from voice_model import instant_voice_clone

from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
import os
from elevenlabs import generate, set_api_key, voices

from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
import time


# Set Streamlit page configuration
st.set_page_config(page_title="Chat with your Loved One", layout="wide")
name_global = ""


# Initialize session states
if "generated" not in st.session_state:
    st.session_state["generated"] = []
if "past" not in st.session_state:
    st.session_state["past"] = []
if "input" not in st.session_state:
    st.session_state["input"] = ""
if "stored_session" not in st.session_state:
    st.session_state["stored_session"] = []
if "just_sent" not in st.session_state:
    st.session_state["just_sent"] = False
if "temp" not in st.session_state:
    st.session_state["temp"] = ""
if "show_warning" not in st.session_state:
    st.session_state["show_warning"] = False


def clear_text():
    st.session_state["temp"] = st.session_state["input"]
    st.session_state["input"] = ""


def save_user_response(name, personality_trait, accent, voice_type):
    user_data = {
        "name": name,
        "personality_trait": personality_trait,
        "accent": accent,
        "voice_type": voice_type,
        "voice_samples": all_samples
        # Add more data fields as needed
    }

    if upload_voice_semantics(user_data):
        instant_voice_clone(name)
    else:
        st.warning(
            "User Data not found make sure you are entering the correct information."
        )


def create_instant_clone(personality_trait, accent, voice_type, voice_samples):
    # Check if there are at least some voice samples uploaded
    print(personality_trait, accent, "fsdf")
    if not voice_samples:
        st.warning("Creating an instant clone requires at least one voice sample.")
        return

    # Save the user's responses to the Firebase Realtime Database
    save_user_response(personality_trait, accent, voice_type)
    st.success("Instant clone created successfully!")


# Function to create a new voice based on user-selected options
def create_new_voice(personality_trait, accent, voice_type):
    print(f"Creating new voice with Personality Trait: {personality_trait}")
    print(f"Selected Accent: {accent}")
    print(f"Selected Voice Type: {voice_type}")

    # Save the user's responses to the Firebase Realtime Database

    save_user_response(personality_trait, accent, voice_type)


voice_samples = []
new_voice_inputs = {}


MODEL = "gpt-3.5-turbo"
K = 100


# Read the API key from the secret.json file
def get_openai_api_key():
    with open("secret.json", "r") as f:
        secret_data = json.load(f)
        return secret_data.get("api_key", "")


def generate_response(user_input, personality_trait, accent, voice_type, name):
    # Here we are setting up the OpenAI API key.
    API_O = get_openai_api_key()

    # Here we are creating a prompt template for the conversation.
    # The prompt template is a list of messages that will be used to generate the conversation.
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(
                "The following is a friendly conversation between a human and an AI. The AI is talkative and provides lots of specific details from its context. If the AI does not know the answer to a question, it truthfully says it does not know."
            ),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{input}", name="input"),
        ]
    )

    # Here we are creating a LLM (OpenAI in our case).
    llm = ChatOpenAI(temperature=0, openai_api_key=API_O)
    memory = ConversationBufferMemory(return_messages=True)
    conversation = ConversationChain(memory=memory, prompt=prompt, llm=llm)

    # Combine the instruction text and user input to form the modified prompt
    instruction_text = f"Context : Act as my loved one that i lost, your NAME:{name} always refer to yourself with this name: {name} ,with Personality Trait: {personality_trait}, make sure you must reply with compassion and  use 3 dashes ---- in your response always in text to express pauses and use proper punctuation to change the tone, take breaks in between sentences and show emotions, to address me as my loved one, DO NOT refer to me as [User] instead just address me as your loved one, DO NOT act as an AI and never bring up that i am talking to an AI, DO's: Generate upto 120 characters in you response,\n and answer this question"
    prompt_with_role = instruction_text + user_input
    print(user_input, "user_input")

    # Get the AI response using LangChain
    response = conversation.predict(input=prompt_with_role)
    print("Response from Server:")
    print(response)

    return response


st.title("Talk with Loved One - Voice Cloning")
hide_default_format = """
       <style>
       #MainMenu {visibility: hidden; }
       footer {visibility: hidden;}
       </style>
       """
st.markdown(hide_default_format, unsafe_allow_html=True)

# Display the navigation bar
st.sidebar.title("Navigation")
selected_page = st.sidebar.radio("Select a Page", ["Upload Voice Samples", "Chat"])

personality_trait = ""
accent = ""
voice_type = ""
name = ""


if selected_page == "Upload Voice Samples":
    st.subheader("Upload Voice Samples")
    st.write(
        "You can upload audio files (mp3 or wav) here to be stored in the database."
    )

    # Initialize variables to store user-selected options

    with st.form(key="create_voice_form"):
        # Prompt a window for voice creation options
        st.subheader("Create New Voice")
        # Ask for personality Name
        name = st.text_input("Name", "")
        st.write(f"Selected Name: {name}")

        # Ask for personality trait
        personality_trait = st.text_input("Personality Trait", "Friendly")
        st.write(f"Selected Personality Trait: {personality_trait}")

        # Ask for accent
        accents = ["American", "British", "Australian", "Indian", "Others"]
        accent = st.selectbox("Select Accent", accents)
        st.write(f"Selected Accent: {accent}")

        # Ask for voice type
        voice_type = st.selectbox("Select Voice Type", ["Male", "Female"])
        st.write(f"Selected Voice Type: {voice_type}")

        # Use st.radio to allow the user to select only one option
        voice_clone_option = st.radio(
            "Select Voice Clone Option",
            ["Instant Clone"],
            index=0,  # Default selected option
        )

        # Display the "Create New Voice" or "Save Response" button
        if st.form_submit_button("Create New Voice"):
            # Call the create_instant_clone function with the selected options and voice samples
            create_instant_clone(personality_trait, accent, voice_type, voice_samples)
            # Show the warning for instant clone requirement

            # Save the user's response to the database
            save_user_response(name, personality_trait, accent, voice_type)

            # Log the user's responses

            st.success("User response saved successfully!")

    uploaded_audio = get_voice_sample()
    if uploaded_audio is not None:
        voice_samples.append(uploaded_audio)

    # Display the number of collected voice samples
    if voice_samples:
        st.subheader("Collected Voice Samples:")
        st.write(f"Number of Audio Files Uploaded: {len(all_samples)}")

elif selected_page == "Chat":
    folder_path = "./audio"
    subfolder_names = []

    for root, dirs, files in os.walk(folder_path):
        for dir_name in dirs:
            subfolder_names.append(dir_name)

    name = ""
    name = st.selectbox("Select the name of voice you just cloned", subfolder_names)
    st.write(f"Name: {name}")
    st.warning("make sure you select the correct name !")

    try:
        file_path = f"audio/{name}/audio_info.json"
        folder_path = os.path.join("audio", name)
        mp3_files = [
            f"./audio/{name}/{file}"
            for file in os.listdir(folder_path)
            if file.endswith(".mp3")
        ]

        with open(file_path, "r") as json_file:
            json_data = json.load(json_file)
            json_name = json_data["name"]
            json_personality_trait = json_data["personality_trait"]
            json_accent = json_data["accent"]
            json_voice_type = json_data["voice_type"]
        print(mp3_files)
    except FileNotFoundError as e:
        st.error("Please generate clone first")
        print(f"Error: {e}")

    with st.form(key="text_input_form"):
        user_input = st.text_input(
            "You: ",
            st.session_state["input"],
            placeholder="Talk to Me",
            label_visibility="hidden",
        )
        submit_button = st.form_submit_button("Submit")

    # Generate the AI response using LangChain
    ai_response = generate_response(
        user_input, json_personality_trait, json_accent, json_voice_type, json_name
    )

    voice_to_clone = None
    if submit_button:
        # Process the user input here (e.g., generate the AI response)
        # If you want to clear the input field after submission, update the session state variable
        progress_bar = st.progress(0)
        for i in range(100):
            # Simulate progress
            progress_bar.progress(i + 1)
            time.sleep(1)  # Add a small delay to simulate processing time
        # Process the user input here (e.g., generate the AI response)
        # If you want to clear the input field after submission, update the session state variable
        st.session_state["input"] = ""
        # Clear the progress bar after response is generated
        progress_bar.empty()

    # Add the user input and AI response to the conversation history
    # if "generated" not in st.session_state:
    #     st.session_state["generated"] = []
    # if "past" not in st.session_state:
    #     st.session_state["past"] = []

    if st.session_state["past"] is None:
        st.session_state["past"] = []
    else:
        st.session_state["past"].append(user_input)

    if st.session_state["generated"] is None:
        st.session_state["generated"] = []
    else:
        st.session_state["generated"].append(ai_response)

    # Display the conversation history using containers
    with st.expander("Conversation", expanded=True):
        num_messages = min(
            len(st.session_state["generated"]), len(st.session_state["past"])
        )
        for i in range(num_messages):
            past_message = (
                st.session_state["past"][i]
                if i < len(st.session_state["past"])
                else None
            )
            ai_response = (
                st.session_state["generated"][i]
                if i < len(st.session_state["generated"])
                else None
            )

            if past_message is not None:
                st.info(past_message, icon="🧐")

            if ai_response is not None:
                with st.container():
                    st.success(ai_response, icon="😃")
                    set_api_key("f6c901a9e1db35ac8b7df9dc70932d0d")

                    print(voice_to_clone)
                    if voice_to_clone:
                        print("passed")
                        audio_stream = generate(text=ai_response, voice=voice_to_clone)

                    else:
                        available_voices = voices()
                        for index, voice in enumerate(available_voices):
                            if voice.name == json_name:
                                voice_to_clone = voice
                                print("voice selected")
                        audio_stream = generate(text=ai_response, voice=voice_to_clone)

                    st.audio(audio_stream, format="audio/mpeg", start_time=0)
