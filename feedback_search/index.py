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
    def __init__(self, zone='content'):
        self.zone = zone
        self.num_of_docs = 0
        self.vocabulary_size = 0
        self.vocabulary_index = dict()
        self.inverted_file = list()
        self.docs_tf_vectors = list()
        self.docs_weights_vectors = list()

    def reset(self):
        self.__init__(self.zone)

    def get_term_idx(self, term):
        return self.vocabulary_index[term]

    def get_term(self, term_idx):
        for term in self.vocabulary_index:
            if self.vocabulary_index[term] == term_idx:
                return term

    def log_tf(self, term_idx, doc_id):
        return math.log(1 + self.docs_tf_vectors[doc_id][term_idx], 10)

    def idf(self, term_idx):
        if self.inverted_file[term_idx]: # A VERIFIER
            return math.log(self.num_of_docs/len(self.inverted_file[term_idx]))
        else:
            return 0

    def preprocess(self, documents, query):
        raise NotImplementedError
    
    def index(self, documents, query):
        """
        Given documents and the query,
        Preprocesses the terms,
        Builds an inverted database of the documents with words as keys,
        And builds the term frequency representation of each document

        The query is passed so that stop words that are in the query are not removed from documents
        """
        initial_time = time.time()
        logger.info('[INDEXER]\t[%s] Started indexing...', self.zone.upper())

        self.num_of_docs = len(documents)

        unique_vocabulary_list, documents_terms = self.preprocess(documents, query)

        self.vocabulary_size = len(unique_vocabulary_list)

        self.docs_tf_vectors = [[0] * len(unique_vocabulary_list) for _ in range(self.num_of_docs)]
        self.vocabulary_index = {term: idx for idx, term in enumerate(unique_vocabulary_list)}
        self.inverted_file = [set() for _ in range(len(unique_vocabulary_list))]

        for doc_id, terms in enumerate(documents_terms):
            for term in terms:
                try:
                    term_idx = self.get_term_idx(term)
                except Exception:
                    logger.error('Pb indexing: %s', terms)
                    break
                self.inverted_file[term_idx].add(doc_id)
                self.docs_tf_vectors[doc_id][term_idx] += 1

        logger.info('[INDEXER]\t[%s] Indexed documents in %s', self.zone.upper(), time.time() - initial_time)


class UnigramIndexer(Indexer):

    def __init__(self, zone='content'):
        super().__init__(zone)

    def find_unigram(self, word):
        """
        Given a single word, return the index of the 
        """
    def preprocess(self, documents, query):

        documents_terms = [] # will be filled with lists of terms of each document
        vocabulary_list = []

        for document in documents:
            # Preprocessing
            zone_terms = document[self.zone]
            all_terms = ' '.join([document[zone] for zone in ['title', 'summary', 'content']])
            # we index only the words from the given zone in doc, but the vocabulary list needs to have all the words
            # so that multiple indexers can be used together in enhance_query
            zone_terms = preprocess.split_remove_punctuation(zone_terms)
            zone_terms = preprocess.remove_stopwords(zone_terms, words_to_keep=query)
            zone_terms = preprocess.stem(zone_terms)

            all_terms = preprocess.split_remove_punctuation(all_terms)
            all_terms = preprocess.remove_stopwords(all_terms, words_to_keep=query)
            all_terms = preprocess.stem(all_terms)

            documents_terms.append(zone_terms)
            vocabulary_list += all_terms

        # Build vocabulary index
        vocabulary_list += query
        unique_vocabulary_list = list(set(vocabulary_list))

        return unique_vocabulary_list, documents_terms


class BigramIndexer(Indexer):

    def __init__(self, zone='content'):
        super().__init__(zone)

    def preprocess(self, documents, query):

        documents_bigrams = [] # will be filled with bigrams of terms of each document
        vocabulary_list = []

        for document in documents:
            # Preprocessing
            zone_terms = document[self.zone]
            all_terms = ' '.join([document[zone] for zone in ['title', 'summary', 'content']])
            # we index only the bigrams from the given zone in doc, but the vocabulary list needs to have all the words
            # so that multiple indexers can be used together in enhance_query
            zone_terms = preprocess.split_remove_punctuation(zone_terms)
            zone_terms = preprocess.remove_stopwords(zone_terms, words_to_keep=query)
            zone_terms = preprocess.stem(zone_terms)
            zone_bigrams = preprocess.get_bigrams(zone_terms)

            all_terms = preprocess.split_remove_punctuation(all_terms)
            all_terms = preprocess.remove_stopwords(all_terms, words_to_keep=query)
            all_terms = preprocess.stem(all_terms)
            all_bigrams = preprocess.get_bigrams(zone_terms)

            documents_bigrams.append(zone_terms)
            vocabulary_list += all_bigrams

        # Build vocabulary index
        vocabulary_list += query
        unique_vocabulary_list = list(set(vocabulary_list))

        return unique_vocabulary_list, documents_bigrams
