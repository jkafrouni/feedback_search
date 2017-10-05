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
from feedback_search.constants import ALPHA, BETA, GAMMA, title_weight, summary_weight, content_weight

from feedback_search import preprocess

logger = logging.getLogger('feedback_search')


class RocchioQueryOptimizer:

    def __init__(self):
        self.ALPHA = ALPHA
        self.BETA = BETA
        self.GAMMA = GAMMA
        self.title_weight = title_weight
        self.summary_weight = summary_weight
        self.content_weight = content_weight

        self.docs_weights_vectors = None
        self.query_weights_vector = None
        self.new_query_weights = None

    def compute_docs_weights(self, indexers):
        """
        Args:
            indexers: list of Indexer objects
        We use one indexer for each zone of docs (title, summary, content)
        And do a weighted sum of the weights given by each indexer
        As scraping might fail, documents may have no content:
        If it's the case we rearrange the weight so that such documents are not penalized # TODO
        """
        vocabulary_size = indexers['title'].vocabulary_size
        num_of_docs = indexers['content'].num_of_docs

        self.docs_weights_vectors = np.zeros((num_of_docs, vocabulary_size))
        zone_weights_vectors = dict()

        for zone in ['title', 'summary', 'content']: 
            zone_weights_vectors[zone] = np.zeros((num_of_docs, vocabulary_size))

            for doc_id in range(num_of_docs):
                for term_idx in range(vocabulary_size):
                    zone_weights_vectors[zone][doc_id, term_idx] += indexers[zone].log_tf(term_idx, doc_id) * indexers[zone].idf(term_idx)

                if np.linalg.norm(zone_weights_vectors[zone][doc_id]) != 0:
                    zone_weights_vectors[zone][doc_id] /= np.linalg.norm(zone_weights_vectors[zone][doc_id])

        self.docs_weights_vectors = self.title_weight * zone_weights_vectors['title'] \
                                  + self.summary_weight * zone_weights_vectors['summary'] \
                                  + self.content_weight * zone_weights_vectors['content']

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

    def enhance(self, query, indexers, relevant, non_relevant):
        """
        Given the raw query and the index of documents with inverted file computed,
        Runs Rocchio's algorithms and returns the augmented query
        Args:
            query: list of strings (preprocessed)
            index: Indexer object (already built)
            relevant: list of ints (doc_ids)
            non_relevant: list of ints (doc_ids)
        """
        self.compute_docs_weights(indexers)
        self.compute_query_weights(indexers['content'], query)

        self.new_query_weights = self.ALPHA * self.query_weights_vector

        for doc_id in relevant:
            self.new_query_weights += (self.BETA/len(relevant)) * self.docs_weights_vectors[doc_id]

        for doc_id in non_relevant:
            self.new_query_weights -= (self.GAMMA/len(non_relevant)) * self.docs_weights_vectors[doc_id]

        self.new_query_weights = self.new_query_weights.clip(min=0) # set negative weights to 0

        # rank words by order:
        ranked_new_terms_ids = list(np.argsort(self.new_query_weights))
        
        logger.info('[ROCCHIO]\t 10 best new query words: %s', [indexers['content'].get_term(term_idx) for term_idx in ranked_new_terms_ids[-10:]])

        for term in query:
            term_idx = indexers['content'].get_term_idx(term)
            if term_idx in ranked_new_terms_ids:
                ranked_new_terms_ids.remove(term_idx)

        # add two best words to query:
        query += [indexers['content'].get_term(term_idx) for term_idx in ranked_new_terms_ids[-2:]]

        logger.info('[ROCCHIO]\t 2 new query words: %s', query[-2:])

        # return query as a string an not a list:
        return ' '.join(query)
