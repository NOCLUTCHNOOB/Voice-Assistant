import pandas as pd
import matplotlib.pyplot as plt
import re
from collections import Counter
from nltk.stem import PorterStemmer
def show_visuals():
    text = []
    try:
        data = pd.read_json("memory.json")
    except FileNotFoundError as e:
        print(f"Error loading stats: {e}")
        return
    for conv in data["conversations"]:
        for msg in conv["messages"][::2]:
            text.append(msg["text"]) 
    topic = Counter(text)
    text = clean_text(text) 
    freq = Counter(text)
    average_response_time = pd.json_normalize([msg for conv in data["conversations"] for msg in conv["messages"]]).query("sender == 'assistant'")["metadata.response_time_sec"].mean()
    return freq.most_common(3),topic.most_common(3),average_response_time


def clean_text(text):
    words = []
    stemmer = PorterStemmer()
    for each in text:
        each = re.sub(r'[^a-z0-9\s]', '', each)
        words.extend(each.split())
    words = [stemmer.stem(w) for w in words]     
    return words   
    
def run():
    outputs = show_visuals()
    if outputs:
        most_common_word, most_common_topic, average_response_time_sec = outputs
    else:
        print("No Data Available! ")
        return
    
    plt.ion()
    plt.close("all")
    fig, axes = plt.subplots(2,2,figsize=(15,4))
    topics, counts = zip(*most_common_topic)
    axes[0,0].bar(topics, counts, color="red")
    axes[0,0].set_title("Most Common Topics")
    axes[0,0].set_ylabel("Frequency")

    # used gemini for the next three lines
    axes[0,0].tick_params(axis='x', rotation=20) # without rotation the topics get jumbled together
    axes[0,0].set_xticks(range(len(topics)))
    axes[0,0].set_xticklabels(topics, ha='right')

    words, counts = zip(*most_common_word)
    axes[0,1].bar(words, counts, color="green")
    axes[0,1].set_title("Most Common Words")
    axes[0,1].set_ylabel("Frequency")
    axes[1,0].text(0.5, 0.7, f"Average Response Time = {average_response_time_sec} sec",fontsize=14, color="darkred")
    axes[1,0].axis("off")
    axes[1,1].axis("off")
    plt.tight_layout()
    plt.show()
    plt.pause(0.1)
    return

def close():
    plt.close("all")   
    return       