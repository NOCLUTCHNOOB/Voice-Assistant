import json
from datetime import datetime
def open_memory():
    try:
        with open("memory.json","r") as memory_file:
            history = json.load(memory_file)
    except Exception:
        history = {"conversations": []}
    return history
def update_memory(user_input,assistant_response,user_input_time,luna_response_time):
    history = open_memory()
    new_conversation = {
        "serial_number": len(history["conversations"]) + 1,
        "start_time": datetime.now().isoformat(),
        "messages": [
            {"sender": "user", "text": user_input,"timestamp": user_input_time.isoformat()},
            {"sender": "assistant", "text": assistant_response,"timestamp": luna_response_time.isoformat(),
             "metadata": {"model":"Meta-Llama-3-8B-Instruct-Q4_K_M", "response_time_sec": (luna_response_time - user_input_time).total_seconds()}}
        ]
    }
    history["conversations"].append(new_conversation)
    with open("memory.json","w") as memory_file:
        json.dump(history, memory_file, indent=4)

def get_memory():
    history = open_memory()
    return history["conversations"][-1:]