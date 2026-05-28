from datetime import datetime
import pyttsx3
import speech_recognition as sr
import sys
from gpt4all import GPT4All
import os
import chat_history as ch
import visuals
import file_path

full_response = ""

def say(text):
    print(text,end="",flush=True)
    engine = pyttsx3.init()
    engine.setProperty("rate", 180)
    voices = engine.getProperty("voices")
    if len(voices) > 1:
        engine.setProperty("voice", voices[1].id)
    engine.say(text)
    engine.runAndWait()
    engine.stop()

model_name = "Meta-Llama-3-8B-Instruct-Q4_K_M.gguf"
model_path = "D:\\Yash Dev\\VS-code\\jarvis_command_v1"
full_model_path = os.path.join(model_path, model_name)

if not os.path.exists(full_model_path):
    print(f"ERROR: Cannot find {model_name}")
    sys.exit(1)

print("Initializing... (Please wait)")
try:
    model = GPT4All(model_name, model_path=model_path, allow_download=False, device='cpu')
    with model.chat_session():
        say("Welcome back, Boss. How can I help you today?")
except Exception as e:
    print(f"Error loading model: {e}")
    sys.exit(1)

listener = sr.Recognizer()
listener.pause_threshold = 0.8

def getcommand():
    try:
        with sr.Microphone() as source:
            print("Listening...")
            listener.adjust_for_ambient_noise(source, duration=0.5)
            
            audio = listener.listen(source, timeout=5, phrase_time_limit=5)
            
            command = listener.recognize_google(audio)
            print("You said: " + command)
            return command

    except sr.UnknownValueError:
        print("Could not understand audio.")
        return ""
    except sr.RequestError:
        print("Internet error.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred.\nTry again.\nError details: {e}")

def clean_response(text):
    if "User:" in text:
        text = text.split("User:")[0]
    tokens_to_remove = [
        "<|eot_id|>", 
        "<|start_header_id|>", 
        "<|end_header_id|>",
    ]
    for t in tokens_to_remove:
        text = text.replace(t, "")
    return text.strip()

print(f"\nLuna: ",end="",flush=True)

if __name__ == "__main__":

    partial_response = ""
    
    system_template = "You are Luna, a helpful assistant. Keep answers short and human-like."

    while True:
        user_input = getcommand()
        user_input_time = datetime.now()

        if not user_input:
            continue
        
        if "exit" in user_input.lower() or "quit" in user_input.lower():
            say("Goodbye, Boss.")
            os.remove("apps.json")
            break

        if "show response" in user_input.lower():
            visuals.run()
            continue

        if "close response" in user_input.lower():
            visuals.close()
            continue

        if "erase memory" in user_input.lower():
            try:
                os.remove("memory.json")
                say("Memory successfully erased")
                continue
            except Exception as e:
                print("An error occured: {e}")
                continue  

        if user_input.lower().startswith(("open " , "close ")):
            file_path.run(user_input)
            continue
        
        if user_input:
            history_lines = []
            for conv in ch.get_memory():
                for msg in conv["messages"]:
                    sender = msg['sender']
                    text = msg['text']
                    history_lines.append(f"<|start_header_id|>{sender}<|end_header_id|>\n\n{text}<|eot_id|>\n")
            prompt_conversation = "".join(history_lines)
            prompt = (
                f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_template}<|eot_id|>\n"
                f"{prompt_conversation}"
                f"<|start_header_id|>user<|end_header_id|>\n\n{user_input}<|eot_id|>\n"
                f"<|start_header_id|>assistant<|end_header_id|>\n\n"
            )
            if prompt_conversation:
                prompt_conversation += "\n"
            print(f"\nLuna: ",end="",flush=True)
            for response in model.generate(prompt, max_tokens=100, temp=0, top_k=1, streaming=True):
                full_response += response
                partial_response += response
                if "<|eot_id|>" in full_response or "<|start_header_id|>" in full_response or "User:" in full_response:
                    partial_response = partial_response.replace("<|eot_id|>", "").replace("<|start_header_id|>", "").replace("User:", "")
                    break
                if any(punctuation in response for punctuation in [".", "?", "!"]):
                    clean = clean_response(partial_response)
                    partial_response = ""
                    say(clean)
                           
            if partial_response.strip():
                clean = clean_response(partial_response)
                if clean:
                    say(clean)        
            
            cleaned_response = clean_response(full_response)
            luna_response_time = datetime.now()

            if cleaned_response:
                ch.update_memory(user_input, cleaned_response, user_input_time, luna_response_time)
                full_response = ""
                print(f"\nLuna: ",end="",flush=True)
            else:
                say("Luna did not generate a response.")