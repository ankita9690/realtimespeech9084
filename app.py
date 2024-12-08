import streamlit as st
from main import speech_to_text, translate_text, real_time_text_to_speech, LANGUAGES_REVERSED, COUNTRY_LANGUAGES, \
    get_vocabulary_suggestions, transcribe_audio_or_video
import time
import tempfile
import os


def main():
    # Customizing the app's header and title
    st.set_page_config(page_title="Real-Time Speech-to-Text Translation App", page_icon="🎤", layout="wide")
    st.markdown("<h1 style='text-align: center;'>Real-Time Speech-to-Text Translation App</h1>", unsafe_allow_html=True)

    st.markdown("""
        <style>
            .css-18e3th9 {
                background-color: #F0F8FF;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            }
            .css-1v0mbdj {
                padding-top: 0px;
                padding-bottom: 0px;
            }
            .stButton > button {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                padding: 10px;
                border-radius: 5px;
                border: none;
                width: 100%;
                cursor: pointer;
            }
            .stButton > button:hover {
                background-color: #45a049;
            }
            .css-14xtw13 {
                padding-left: 10px;
                padding-right: 10px;
            }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar menu for feature selection
    st.sidebar.title("Navigation")
    feature = st.sidebar.radio(
        "Choose a Feature",
        ["Real-Time Speech-to-Text", "Audio/Video File Transcription"]
    )

    if feature == "Real-Time Speech-to-Text":
        real_time_speech_to_text_section()
    elif feature == "Audio/Video File Transcription":
        audio_video_transcription_section()


def real_time_speech_to_text_section():
    """Handles the Real-Time Speech-to-Text functionality."""
    # Initialize session state variables
    if "running" not in st.session_state:
        st.session_state.running = False
    if "transcription" not in st.session_state:
        st.session_state.transcription = []

    # Add a country selection dropdown with styling
    country = st.selectbox("Select Country", list(COUNTRY_LANGUAGES.keys()), key="country", index=0,
                           label_visibility="collapsed")

    # Dynamically filter languages based on the selected country
    available_languages = COUNTRY_LANGUAGES[country]
    target_language = st.selectbox("Select Target Language", available_languages, key="target_language")

    # Get the language code for translation
    target_language_code = LANGUAGES_REVERSED.get(target_language.lower())

    # Transcription mode toggle
    transcription_mode = st.checkbox("Enable Transcription Mode")
    vocabulary_mode = st.checkbox("Enable Contextual Vocabulary Suggestions")

    # Create buttons for starting and stopping the session
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start", key="start_button"):
            st.session_state.running = True
            st.session_state.transcription = []  # Reset transcription log
            st.success("Session started! Listening for speech...")
    with col2:
        if st.button("Stop", key="stop_button"):
            st.session_state.running = False
            st.warning("Session stopped. Click 'Start' to begin again.")

    # Main app logic for continuous translation
    if st.session_state.running:
        run_translation_session(target_language_code, transcription_mode, vocabulary_mode)
    else:
        st.info("Ready to start. Click 'Start' to begin listening...")

    # Display transcription and allow download
    if st.session_state.transcription:
        st.subheader("Transcription Log")
        transcription_text = "\n".join(st.session_state.transcription)
        st.text_area("Transcript", transcription_text, height=200, key="transcription_area")
        st.download_button("Download Transcript", transcription_text, file_name="transcript.txt")


def run_translation_session(target_language_code, transcription_mode, vocabulary_mode):
    """Handles the real-time speech-to-text, translation, and text-to-speech."""
    if not target_language_code:
        st.error("Selected language is not supported.")
        return

    # Continuous listening and processing
    while st.session_state.running:
        st.write("Listening... Please speak now.")
        text = speech_to_text()

        if text:
            st.write(f"Original Text: {text}")

            # Translate text
            translated_text = translate_text(text, target_language_code)
            st.write(f"Translated Text: {translated_text}")

            # Add transcription to the session log
            st.session_state.transcription.append(f"Original: {text} → Translated: {translated_text}")

            # Show contextual vocabulary suggestions
            if vocabulary_mode:
                suggestions = get_vocabulary_suggestions(text, target_language_code)
                for original, suggestion in suggestions.items():
                    st.write(f"**{original}** → {', '.join(suggestion)}")

            # Text-to-speech for translated text
            real_time_text_to_speech(translated_text, target_language_code)

        # Sleep for a while before continuing the next round of listening
        time.sleep(2)


def audio_video_transcription_section():
    """Handles the Audio/Video File Transcription functionality."""
    st.header("Audio/Video File Transcription")
    st.markdown(
        "Upload an audio or video file to generate a transcription. "
        "Supported formats: MP3, WAV, MP4, AVI, MOV, MKV."
    )

    uploaded_file = st.file_uploader("Upload a file", type=['mp3', 'wav', 'mp4', 'avi', 'mov', 'mkv'])

    if uploaded_file is not None:
        # Save the uploaded file temporarily
        temp_file_path = tempfile.mktemp(suffix=os.path.splitext(uploaded_file.name)[1])
        with open(temp_file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())

        st.write(f"Processing file: {uploaded_file.name}")

        # Call the transcribe function
        transcription = transcribe_audio_or_video(temp_file_path)

        if transcription:
            st.subheader("Transcription")
            st.write(transcription)
        else:
            st.write("Error in transcription. Please try again.")

        # Optional: Add a download button for the transcription
        st.download_button("Download Transcription", transcription, file_name="transcription.txt")


if __name__ == "__main__":
    main()



