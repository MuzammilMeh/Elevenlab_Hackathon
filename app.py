import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, db,firestore
import base64
from pydub import AudioSegment
import io
from utils import get_voice_sample,all_samples,upload_voice_semantics
from voice_model import instant_voice_clone

from PIL import Image
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationEntityMemory
from langchain.chains.conversation.prompt import ENTITY_MEMORY_CONVERSATION_TEMPLATE
from langchain.llms import OpenAI
from langchain.callbacks import get_openai_callback

# if not firebase_admin._apps:
#     # Initialize the default Firebase app (call this only once)
#     cred = credentials.Certificate('firebase.json')
#     firebase_admin.initialize_app(cred,{'storageBucket': 'elevenlabshackathon.appspot.com'})

# fire_db = firestore.client()

# Set Streamlit page configuration
st.set_page_config(page_title="Chat with your Loved One", layout="wide")

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


# Function to get the duration of the audio file
def get_audio_duration(audio_data):
    # Convert the base64 encoded audio data to bytes
    audio_bytes = base64.b64decode(audio_data)

    # Load the audio data using pydub
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))

    # Get the duration of the audio file in seconds
    duration = len(audio) / 1000.0
    return duration


def save_user_response(name,personality_trait, accent, voice_type):
    user_data = {
        "name":name,
        "personality_trait": personality_trait,
        "accent": accent,
        "voice_type": voice_type,
        "voice_samples":all_samples
        
        # Add more data fields as needed
    }
    if upload_voice_semantics(user_data):
        instant_voice_clone(name)
    else:
        st.warning("User Data not found make sure you are entering the correct information.")
        
   


def create_professional_clone(personality_trait, accent, voice_type, voice_samples):
    # Check if at least 30 minutes of voice samples are uploaded
    total_duration = 0
    for audio_data in voice_samples:
        # Get the duration of the audio file
        duration = get_audio_duration(audio_data)
        total_duration += duration

    if (
        total_duration < 30 * 60
    ):  # Check if the total duration is less than 30 minutes (in seconds)
        st.warning(
            "Creating a professional clone requires at least 30 minutes of voice samples."
        )
        return

    # Implement your voice cloning logic for professional clone here based on the selected options and voice samples
    # For example, you can call a deep learning model to create the professional voice clone

    # Save the user's responses to the Firebase Realtime Database
    save_user_response(personality_trait, accent, voice_type)
    st.success("Professional clone created successfully!")


def create_instant_clone(personality_trait, accent, voice_type, voice_samples):
    # Check if there are at least some voice samples uploaded
    print(personality_trait,accent,"fsdf")
    if not voice_samples:
        st.warning("Creating an instant clone requires at least one voice sample.")
        return

    # Implement your voice cloning logic for instant clone here based on the selected options and voice samples
    # For example, you can use a simpler model for instant voice cloning

    # Save the user's responses to the Firebase Realtime Database
    save_user_response(personality_trait, accent, voice_type)
    st.success("Instant clone created successfully!")


# Define function to get user input
def get_text():
    input_text = st.text_input(
        "You: ",
        st.session_state["input"],
        key="input",
        placeholder="Talk to Me",
        on_change=clear_text,
        label_visibility="hidden",
    )
    input_text = st.session_state["temp"]
    return input_text


# Function to create a new voice based on user-selected options
def create_new_voice(personality_trait, accent, voice_type):
    # Implement your voice creation logic here based on the selected options
    # For example, you can call a function to create the new voice
    # Replace the print statements with the actual logic to create the voice
    print(f"Creating new voice with Personality Trait: {personality_trait}")
    print(f"Selected Accent: {accent}")
    print(f"Selected Voice Type: {voice_type}")

    # Save the user's responses to the Firebase Realtime Database

    save_user_response(personality_trait, accent, voice_type)



voice_samples = []
new_voice_inputs={}


def new_chat():
    """
    Clears session state and starts a new chat.
    """
    save = []
    for i in range(len(st.session_state["generated"]) - 1, -1, -1):
        save.append("User:" + st.session_state["past"][i])
        save.append("Bot:" + st.session_state["generated"][i])
    st.session_state["stored_session"].append(save)
    st.session_state["generated"] = []
    st.session_state["past"] = []
    st.session_state["input"] = ""
    st.session_state["entity_memory"].store = {}
    st.session_state["entity_memory"].buffer.clear()


MODEL = "gpt-3.5"
K = 100

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


# Read the API key from the secret.json file
def get_openai_api_key():
    with open("secret.json", "r") as f:
        secret_data = json.load(f)
        return secret_data.get("api_key", "")


API_O = get_openai_api_key()

# Session state storage would be ideal
if API_O:
    # Create an OpenAI instance
    llm = OpenAI(temperature=0, openai_api_key=API_O, model_name=MODEL, verbose=False)

    # Create a ConversationEntityMemory object if not already created
    if "entity_memory" not in st.session_state:
        st.session_state["entity_memory"] = ConversationEntityMemory(llm=llm, k=K)

    # Create the ConversationChain object with the specified configuration
    Conversation = ConversationChain(
        llm=llm,
        prompt=ENTITY_MEMORY_CONVERSATION_TEMPLATE,
        memory=st.session_state["entity_memory"],
    )
else:
    st.sidebar.warning(
        "API key required to try this app. The API key is not stored in any form."
    )
if selected_page == "Upload Voice Samples":
    st.subheader("Upload Voice Samples")
    st.write(
        "You can upload audio files (mp3 or wav) here to be stored in the database."
    )

    # Initialize variables to store user-selected options
    personality_trait = ""
    accent = ""
    voice_type = ""
    name = ""

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
            ["Professional Clone", "Instant Clone"],
            index=0,  # Default selected option
        )

        # Display the "Create New Voice" or "Save Response" button
        if st.form_submit_button("Create New Voice"):
            if voice_clone_option == "Professional Clone":
                create_professional_clone(
                    personality_trait, accent, voice_type, voice_samples
                )
                # Show the warning for instant clone requirement

            else:
                # Call the create_instant_clone function with the selected options and voice samples
                create_instant_clone(
                    personality_trait, accent, voice_type, voice_samples
                )
                # Show the warning for instant clone requirement

            # Save the user's response to the database
            save_user_response(name,personality_trait, accent, voice_type)

            # Log the user's responses
            st.write("User Personality Trait:", personality_trait)
            st.write("User Accent:", accent)
            st.write("User Voice Type:", voice_type)
            st.write("User name:", name)

            st.success("User response saved successfully!")

    uploaded_audio = get_voice_sample()
    if uploaded_audio is not None:
        voice_samples.append(uploaded_audio)

    # Display the number of collected voice samples
    if voice_samples:
        st.subheader("Collected Voice Samples:")
        st.write(f"Number of Audio Files Uploaded: {len(all_samples)}")




















elif selected_page == "Chat":
    # Get the user input
    user_input = get_text()

    # Generate the output using the ConversationChain object and the user input, and add the input/output to the session
    if user_input:
        if "balance" not in st.session_state:
            st.session_state["balance"] = 0.0

        if st.session_state["balance"] > -0.03:
            with get_openai_callback() as cb:
                output = Conversation.run(input=user_input)
                st.session_state["past"].append(user_input)
                st.session_state["generated"].append(output)
                st.session_state["balance"] -= cb.total_cost * 4
        else:
            st.session_state["past"].append(user_input)

    # Display the conversation history using an expander, and allow the user to download it
    with st.expander("Conversation", expanded=True):
        for i in range(len(st.session_state["generated"]) - 1, -1, -1):
            st.info(st.session_state["past"][i], icon="🧐")
            st.success(st.session_state["generated"][i], icon="🤖")

            # Allow to download as well
            download_str = []
            download_str.append(st.session_state["past"][i])
            download_str.append(st.session_state["generated"][i])
            download_str = "\n".join(download_str)

            if download_str:
                st.download_button(f"Download (Session {i+1})", download_str)

# Display stored conversation sessions in the sidebar
for i, sublist in enumerate(st.session_state["stored_session"]):
    with st.sidebar.expander(label=f"Conversation-Session:{i}"):
        st.write(sublist)

# Allow the user to clear all stored conversation sessions
if st.session_state["stored_session"]:
    if st.sidebar.checkbox("Clear-all"):
        del st.session_state["stored_session"]
