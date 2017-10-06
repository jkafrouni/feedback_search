import re
import nltk

STOPWORDS = open('resources/stopwords.txt').read().split('\n')

def split_remove_punctuation(text):
    word_list = re.split('\W+', text) # split into words, without punctuation
    while '' in word_list: # quick fix, regex adds empty string
        word_list.remove('') 
    word_list = [word.lower() for word in word_list] # lower everything

    return word_list

def remove_stopwords(word_list, words_to_keep=[]):
    """Doesn't remove the words in words_to_keep if they are present and they are indeed stopwords"""
    if words_to_keep and isinstance(words_to_keep, str):
        words_to_keep = split_remove_punctuation(words_to_keep)

    for w in STOPWORDS:
        if w not in words_to_keep:
            while w in word_list:
                # list.remove only removes an element one time
                word_list.remove(w)

    return word_list

def stem(word_list):
    p = nltk.stem.PorterStemmer()
    return [p.stem(word) for word in word_list]

def get_bigrams(word_list):
    return list(nltk.bigrams(word_list))