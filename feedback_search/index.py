from feedback_search import preprocess

import re
import time
import logging
import math

logger = logging.getLogger('feedback_search')


class Indexer:
    """
    Given documents, 
    - stores them in an inverted index, 
    - computes terms frequencies,
    - computes vector of term frequencies for each document
    # TODO : add threads to index in parallel when possible
    """
    def __init__(self):
        self.inverted_database = dict()

    def __iter__(self):
        return iter(self.inverted_database)

    def __len__(self):
        return len(self.inverted_database)

    def reset(self):
        self.__init__()

    def idf(self, word):
        return math.log(len(self)/len(self.inverted_database[word]))

    def index(self, document, query):
        """
        Given documents and the query,
        Preprocesses the terms,
        Builds an inverted database of the documents with words as keys,
        And builds the term frequency representation of each document

        The query is passed so that stop words that are in the query are not removed from documents
        """
        initial_time = time.time()

        terms = document['content'] if 'content' in document else document['summary'] # work with summary if content not available
        terms = preprocess.split_remove_punctuation(terms)
        terms = preprocess.remove_stopwords(terms, words_to_keep=query)

        document['tf_vector'] = dict()

        for term in terms:
            if term in self.inverted_database:
                self.inverted_database[term][document['id']] = document
            else:
                self.inverted_database[term] = {document['id']: document}

            if term in document['tf_vector']:
                document['tf_vector'][term] += 1
            else:
                document['tf_vector'][term] = 1

        logger.info('[INDEXER]\t Indexed document in %s', time.time() - initial_time)