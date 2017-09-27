"""
Rules:

- Automatical enhancement, no further human input after feedback has been given
- Introduce at most 2 new words
- Cannot delete any words of the input query (neither initial nor current query)
- Queries should only contain words, no additional operators
- Words can (and should) be reordered
"""
import math
import logging
import numpy as np

from feedback_search import preprocess

logger = logging.getLogger('feedback_search')


class RocchioQueryOptimizer:

    def __init__(self, ALPHA, BETA, GAMMA):
        self.ALPHA = ALPHA
        self.BETA = BETA
        self.GAMMA = GAMMA

        self.docs_weights_vectors = None
        self.query_weights_vector = None
        self.new_query_weights = None

    def compute_docs_weights(self, index):
        self.docs_weights_vectors = np.zeros((index.num_of_docs, index.vocabulary_size))

        for doc_id in range(index.num_of_docs):
            for term_idx in range(index.vocabulary_size):
                self.docs_weights_vectors[doc_id, term_idx] = index.log_tf(term_idx, doc_id) * index.idf(term_idx)

            if np.linalg.norm(self.docs_weights_vectors[doc_id]) != 0:
                self.docs_weights_vectors[doc_id] /= np.linalg.norm(self.docs_weights_vectors[doc_id])

    def compute_query_weights(self, index, query):
        """
        Args:
            index: Index object
            query: list of strings, already preprocessed
        """
        self.query_weights_vector = np.zeros(index.vocabulary_size)
        
        for term in query:
            term_idx = index.get_term_idx(term)
            self.query_weights_vector[term_idx] = math.log(1 + query.count(term), 10) * index.idf(term_idx)

            if np.linalg.norm(self.query_weights_vector) != 0:
                self.query_weights_vector /= np.linalg.norm(self.query_weights_vector)

    def enhance(self, query, index, relevant, non_relevant):
        """
        Given the raw query and the index of documents with inverted file computed,
        Runs Rocchio's algorithms and returns the augmented query
        Args:
            query: list of strings (preprocessed)
            index: Indexer object (already built)
            relevant: list of ints (doc_ids)
            non_relevant: list of ints (doc_ids)
        """
        self.compute_docs_weights(index)
        self.compute_query_weights(index, query)
        # self.new_query_weights = [0] * len(self.query_weights_vector)
        self.new_query_weights = np.zeros(index.vocabulary_size)

        self.new_query_weights = self.ALPHA * self.query_weights_vector

        for doc_id in relevant:
            self.new_query_weights += (self.BETA/len(relevant)) * self.docs_weights_vectors[doc_id]

        for doc_id in non_relevant:
            self.new_query_weights -= (self.GAMMA/len(non_relevant)) * self.docs_weights_vectors[doc_id]

        self.new_query_weights = self.new_query_weights.clip(min=0) # set negative weights to 0

        # rank words by order:
        ranked_new_terms_ids = list(np.argsort(self.new_query_weights))
        
        logger.info('[ROCCHIO]\t 10 best new query words: %s', [index.get_term(term_idx) for term_idx in ranked_new_terms_ids[-10:]])

        for term in query:
            term_idx = index.get_term_idx(term)
            if term_idx in ranked_new_terms_ids:
                ranked_new_terms_ids.remove(term_idx)

        # add two best words to query:
        query += [index.get_term(term_idx) for term_idx in ranked_new_terms_ids[-2:]]

        logger.info('[ROCCHIO]\t 2 new query words: %s', query[-2:])

        # return query as a string an not a list:
        return ' '.join(query)
