import speech_recognition as sr
from googletrans import Translator, LANGUAGES as GOOGLE_LANGUAGES
from gtts.lang import tts_langs
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import nltk
from nltk.corpus import wordnet
import ffmpeg
import tempfile

# Make sure you have the required NLTK data
nltk.download('wordnet')

# Initialize translator
translator = Translator()

# Supported languages for Google Translate and gTTS
GOOGLE_TRANSLATE_LANGUAGES = GOOGLE_LANGUAGES
GTTS_LANGUAGES = tts_langs()
LANGUAGES = {code: name for code, name in GOOGLE_TRANSLATE_LANGUAGES.items() if code in GTTS_LANGUAGES}
LANGUAGES_REVERSED = {v: k for k, v in LANGUAGES.items()}

# Country-wise language mapping
COUNTRY_LANGUAGES = {
    "India": ["Hindi", "Bengali", "Tamil", "Telugu", "Kannada", "Malayalam", "Punjabi", "Gujarati", "Marathi", "Odia",
              "Urdu"],
    "United States": ["English", "Spanish"],
    "France": ["French"],
    "Germany": ["German"],
    "China": ["Chinese (Simplified)", "Chinese (Traditional)"],
    "Japan": ["Japanese"],
    "All": list(LANGUAGES.values())
}


def speech_to_text():
    """
    Converts speech input from microphone to text.
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = recognizer.listen(source)
            text = recognizer.recognize_google(audio)
            print(f"Original Text: {text}")
            return text
        except sr.UnknownValueError:
            print("Sorry, I could not understand that.")
            return None
        except sr.RequestError as e:
            print(f"Error with speech recognition: {e}")
            return None


def detect_language(text):
    """
    Auto-detects the language of the given text.
    """
    try:
        detected = translator.detect(text)
        return detected.lang
    except Exception as e:
        print(f"Error detecting language: {e}")
        return 'en'  # Default to English if detection fails


def translate_text(text, target_language):
    """
    Translates text to the specified target language.
    """
    try:
        detected_lang = detect_language(text)
        print(f"Detected Language: {detected_lang}")
        print(f"Translating to {target_language}...")
        translated = translator.translate(text, src=detected_lang, dest=target_language)
        print(f"Translated Text: {translated.text}")
        return translated.text
    except Exception as e:
        print(f"Error during translation to '{target_language}': {e}")
        return "Translation failed."


def real_time_text_to_speech(text, language="en"):
    """
    Converts text to speech in real-time.
    """
    try:
        if language not in GTTS_LANGUAGES:
            print(f"Language '{language}' is not supported for text-to-speech.")
            return

        # Map Google Translate's `zh-cn` to gTTS's `zh` for Chinese
        if language == "zh-cn":
            language = "zh"

        tts = gTTS(text, lang=language)
        tts.save("translated_speech.mp3")
        audio = AudioSegment.from_file("translated_speech.mp3", format="mp3")
        play(audio)
    except Exception as e:
        print(f"Error during text-to-speech: {e}")


def get_vocabulary_suggestions(text, target_language):
    """
    Fetch contextual vocabulary suggestions for words in the given text.
    """
    try:
        words = text.split()
        suggestions = {}
        for word in words:
            try:
                # Translate each word to the target language with explicit source language
                translated_word = translator.translate(word, src='en', dest=target_language).text
                # Mock suggestions (expand with a thesaurus API for more accurate results)
                synonyms = get_synonyms(word, target_language)
                # Ensure synonyms are flattened into a single list of strings
                flattened_synonyms = [syn for sublist in synonyms for syn in
                                      (sublist if isinstance(sublist, list) else [sublist])]
                suggestions[word] = [translated_word] + flattened_synonyms
            except Exception as e:
                print(f"Error fetching vocabulary for word '{word}': {e}")
                suggestions[word] = [word]  # Fallback to the word itself
        return suggestions
    except Exception as e:
        print(f"Error fetching vocabulary suggestions: {e}")
        return {}


def get_synonyms(word, target_language):
    """
    Fetch synonyms for a word (real synonyms for English words, fallback for others).
    Skips function words (e.g., "is", "a", "the") and provides better fallback handling.
    """
    function_words = {'is', 'am', 'are', 'the', 'a', 'an', 'in', 'on', 'of', 'to', 'for', 'and', 'but', 'or', 'by',
                      'with'}

    try:
        # If the word is a function word, skip synonym fetching
        if word.lower() in function_words:
            return [word]  # No synonyms for function words, just return the word itself

        # Check if the word is in English (for using WordNet)
        if target_language == 'en':
            synonyms = wordnet.synsets(word)
            if not synonyms:
                return [word]  # If no synonyms are found, return the word itself

            # Get the lemma names (synonyms) for each synset
            synonym_list = set()
            for syn in synonyms:
                for lemma in syn.lemmas():
                    synonym_list.add(lemma.name())
            return list(synonym_list)
        else:
            # For non-English words, use translation-based fallback
            translated_word = translator.translate(word, src='en', dest=target_language).text
            return [translated_word]  # Just return the translated word

    except Exception as e:
        print(f"Error fetching synonyms for word '{word}': {e}")
        return [word]  # Fallback to the word itself if error occurs


def transcribe_audio_or_video(file_path):
    """
    Transcribe the audio from an audio or video file.
    Uses ffmpeg to extract audio from video files if necessary.
    """
    try:
        # If the file is a video, extract the audio using ffmpeg
        if file_path.endswith(('.mp4', '.avi', '.mov', '.mkv')):
            audio_path = tempfile.mktemp(suffix='.wav')  # Create a temporary file to save the audio
            ffmpeg.input(file_path).output(audio_path).run()
            file_path = audio_path  # Use the extracted audio file

        # Convert the audio to WAV if it's not in the correct format
        if not file_path.endswith('.wav'):
            audio = AudioSegment.from_file(file_path)
            audio = audio.set_channels(1).set_frame_rate(16000)  # Set mono channel and 16kHz frame rate
            temp_wav_path = tempfile.mktemp(suffix='.wav')
            audio.export(temp_wav_path, format='wav')
            file_path = temp_wav_path  # Use the newly created WAV file

        # Now transcribe audio using speech recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(file_path) as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data)
        print(f"Transcription: {text}")
        return text
    except Exception as e:
        print(f"Error transcribing file {file_path}: {e}")
        return "Error in transcription. Please try again."


