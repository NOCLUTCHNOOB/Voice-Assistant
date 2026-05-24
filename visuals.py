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
    return freq.most_common(3),topic.most_common(3)


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
        most_common_topic,most_common_word = outputs
    else:
        print("No Data Available! ")
        return

    fig, axes = plt.subplots(1,2,figsize=(16,2))
    plt.show() 
        
run()        