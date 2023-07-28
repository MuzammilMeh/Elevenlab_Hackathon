import streamlit as st
from PIL import Image
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationEntityMemory
from langchain.chains.conversation.prompt import ENTITY_MEMORY_CONVERSATION_TEMPLATE
from langchain.llms import OpenAI
from langchain.callbacks import get_openai_callback
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import base64

# Initialize Firebase Admin SDK with your Firebase project credentials
if not firebase_admin._apps:
    cred = credentials.Certificate("credential.json")
    firebase_admin.initialize_app(
        cred, {"databaseURL": "https://hackthon-f919c-default-rtdb.firebaseio.com"}
    )


# Set Streamlit page configur

st.set_page_config(page_title=" Chat with your Loved One", layout="wide")
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


def clear_text():
    st.session_state["temp"] = st.session_state["input"]
    st.session_state["input"] = ""


# Initialize a list to store voice data (text samples)
voice_samples = []


# Function to get voice samples from the user
def get_voice_sample():
    """
    Get voice samples from the user as audio file uploads.

    Returns:
        (bytes) or None: The uploaded audio file as bytes, or None if no file is uploaded.
    """
    voice_sample = st.file_uploader(
        "Upload Voice Sample:",
        type=["mp3", "wav"],  # Specify accepted file types (you can add more if needed)
        key="voice_sample",
    )
    return voice_sample


# Function to save the audio file in the Firebase Realtime Database
def save_audio_to_firebase(audio_data):
    encoded_audio_data = base64.b64encode(audio_data).decode("utf-8")
    ref = db.reference("voice_samples")
    ref.push(encoded_audio_data)


# Define function to get user input
def get_text():
    """
    Get the user input text.

    Returns:
        (str): The text entered by the user
    """
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


# Set up the Streamlit app layout
st.title("Talk with Loved One - Voice Cloning")
hide_default_format = """
       <style>
       #MainMenu {visibility: hidden; }
       footer {visibility: hidden;}
       </style>
       """
st.markdown(hide_default_format, unsafe_allow_html=True)


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
    # st.stop()

st.subheader("Upload Voice Samples")
st.write("You can upload audio files (mp3 or wav) here to be stored in the database.")
uploaded_audio = get_voice_sample()
if uploaded_audio is not None:
    voice_samples.append(uploaded_audio)

# Display the number of collected voice samples
if voice_samples:
    st.subheader("Collected Voice Samples:")
    st.write(f"Number of Audio Files Uploaded: {len(voice_samples)}")


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

# Allow to download as well
download_str = []
# Display the conversation history using an expander, and allow the user to download it
with st.expander("Conversation", expanded=True):
    for i in range(len(st.session_state["generated"]) - 1, -1, -1):
        st.info(st.session_state["past"][i], icon="🧐")
        st.success(st.session_state["generated"][i], icon="🤖")
        download_str.append(st.session_state["past"][i])
        download_str.append(st.session_state["generated"][i])

    # Can throw error - requires fix
    download_str = "\n".join(download_str)

    if download_str:
        st.download_button("Download", download_str)

# ... (rest of the code)

# Display stored conversation sessions in the sidebar
for i, sublist in enumerate(st.session_state["stored_session"]):
    with st.sidebar.expander(label=f"Conversation-Session:{i}"):
        st.write(sublist)

# Allow the user to clear all stored conversation sessions
if st.session_state["stored_session"]:
    if st.sidebar.checkbox("Clear-all"):
        del st.session_state["stored_session"]

# st.image(img, caption=None, width=200)
