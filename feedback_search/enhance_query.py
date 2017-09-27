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

    def compute_docs_weights(self, index):
        self.docs_weights_vectors = [[0] * len(index.vocabulary_index)] * index.num_of_docs
        for doc_id in range(index.num_of_docs):
            for term_idx in range(len(index.vocabulary_index)):
                self.docs_weights_vectors[doc_id][term_idx] = index.log_tf(term_idx, doc_id) * index.idf(term_idx)

            # a remplacer par numpy:
            norm = math.sqrt(sum([x**2 for x in self.docs_weights_vectors[doc_id]]))
            self.docs_weights_vectors[doc_id] = [x/norm for x in self.docs_weights_vectors[doc_id]]

    def compute_query_weights(self, index, query):
        """
        Args:
            query: list of strings, already preprocessed
        """
        self.query_weights_vector = [0] * len(index.vocabulary_index)
        for term in query:
            term_idx = index.get_term_idx(term)
            self.query_weights_vector[term_idx] = math.log(1 + query.count(term), 10) * index.idf(term_idx)
            # TODO: revoir poids, normaliser
            norm = math.sqrt(sum([x**2 for x in self.query_weights_vector]))
            self.query_weights_vector = [x/norm for x in self.query_weights_vector]

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
        self.new_query_weights = [0] * len(self.query_weights_vector)

        for term_idx in range(len(index.vocabulary_index)):
            # TODO: make calculus look nicer
            rocchio_first_part = self.ALPHA * self.query_weights_vector[term_idx]
            
            rocchio_second_part = 0
            for doc_id in relevant:
                rocchio_second_part += self.docs_weights_vectors[doc_id][term_idx]
            rocchio_second_part *= (self.BETA/len(relevant))

            rocchio_third_part = 0
            for document in non_relevant:
                rocchio_third_part += self.docs_weights_vectors[doc_id][term_idx]
            rocchio_third_part *= (self.GAMMA/len(non_relevant))

            self.new_query_weights[term_idx] =  max(0, rocchio_first_part + rocchio_second_part - rocchio_third_part)

        # rank words by order:
        ranked_new_terms_ids = list(np.argsort(self.new_query_weights))
        # logger.info('[ROCCHIO]\t 10 best new query words: %s', ranked_new_query_words[-10:])

        for term in query:
            term_idx = index.get_term_idx(term)
            if term_idx in ranked_new_terms_ids:
                ranked_new_terms_ids.remove(term_idx)

        # add two best words to query:
        query += [index.get_term(term_idx) for term_idx in ranked_new_terms_ids[-2:]]

        logger.info('[ROCCHIO]\t 2 new query words: %s', query[-2:])

        # return query as a string an not a list:
        return ' '.join(query)
