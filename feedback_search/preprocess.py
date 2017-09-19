import re

STOPWORDS = open('resources/stopwords.txt').read().split('\n')

def split_remove_punctuation(text):
    word_list = re.split('\W+', text) # split into words, without punctuation
    if '' in word_list: # quick fix, regex adds empty string
        word_list.remove('') 
    word_list = [word.lower() for word in word_list] # lower everything

    return word_list

def remove_stopwords(word_list):
    for w in STOPWORDS:
        if w in word_list:
            word_list.remove(w)

    return word_list