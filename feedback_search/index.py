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
        self.num_of_docs = 0
        self.vocabulary_size = 0
        self.vocabulary_index = dict()
        self.inverted_file = list()
        self.docs_tf_vectors = list()
        self.docs_weights_vectors = list()

    def reset(self):
        self.__init__()

    def get_term_idx(self, term):
        return self.vocabulary_index[term]

    def get_term(self, term_idx):
        for term in self.vocabulary_index:
            if self.vocabulary_index[term] == term_idx:
                return term

    def log_tf(self, term_idx, doc_id):
        return math.log(1 + self.docs_tf_vectors[doc_id][term_idx], 10)

    def idf(self, term_idx):
        return math.log(self.num_of_docs/len(self.inverted_file[term_idx]))

    def index(self, documents, query):
        """
        Given documents and the query,
        Preprocesses the terms,
        Builds an inverted database of the documents with words as keys,
        And builds the term frequency representation of each document

        The query is passed so that stop words that are in the query are not removed from documents
        """
        initial_time = time.time()

        self.num_of_docs = len(documents)

        documents_terms = [] # will be filled with lists of terms of each document

        for document in documents:
            # Preprocessing
            terms = document['content'] if 'content' in document else document['summary'] # work with summary if content not available
            terms = preprocess.split_remove_punctuation(terms)
            terms = preprocess.remove_stopwords(terms, words_to_keep=query)
            terms = preprocess.stem(terms)
            documents_terms.append(terms)

        # Build vocabulary index
        vocabulary_list = sum(documents_terms, []) + query
        unique_vocabulary_list = list(set(vocabulary_list))

        self.vocabulary_size = len(unique_vocabulary_list)

        self.docs_tf_vectors = [[0] * len(unique_vocabulary_list) for _ in range(self.num_of_docs)]
        self.vocabulary_index = {term: idx for idx, term in enumerate(unique_vocabulary_list)}
        self.inverted_file = [set() for _ in range(len(unique_vocabulary_list))]

        for doc_id, terms in enumerate(documents_terms):
            for term in terms:
                term_idx = self.get_term_idx(term)
                self.inverted_file[term_idx].add(doc_id)
                self.docs_tf_vectors[doc_id][term_idx] += 1

        logger.info('[INDEXER]\t Indexed documents in %s', time.time() - initial_time)
