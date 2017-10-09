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

from feedback_search import constants
from feedback_search import preprocess

logger = logging.getLogger('feedback_search')


class RocchioQueryOptimizer:

    def __init__(self):
        self.ALPHA = constants.ALPHA
        self.BETA = constants.BETA
        self.GAMMA = constants.GAMMA
        self.title_weight = constants.title_weight
        self.summary_weight = constants.summary_weight
        self.content_weight = constants.content_weight

        self.docs_weights_vectors = None
        self.query_weights_vector = None
        self.rocchio_weights = None

    def compute_docs_weights(self, indexers, terms_type='unigram'):
        """
        Args:
            indexers: list of Indexer objects
        We use one indexer for each zone of docs (title, summary, content)
        And do a weighted sum of the weights given by each indexer
        As scraping might fail, documents may have no content:
        If it's the case we rearrange the weight so that such documents are not penalized # TODO
        """
        vocabulary_size = indexers['title'].vocabulary_size
        num_of_docs = indexers['content'].num_of_docs # à clarifier content vs title

        self.docs_weights_vectors = np.zeros((num_of_docs, vocabulary_size))
        zone_weights_vectors = dict()

        for zone in ['title', 'summary', 'content']: 
            zone_weights_vectors[zone] = np.zeros((num_of_docs, vocabulary_size))

            for doc_id in range(num_of_docs):
                for term_idx in range(vocabulary_size):
                    zone_weights_vectors[zone][doc_id, term_idx] += indexers[zone].log_tf(term_idx, doc_id) * indexers[zone].idf(term_idx)

                if np.linalg.norm(zone_weights_vectors[zone][doc_id]) != 0:
                    zone_weights_vectors[zone][doc_id] /= np.linalg.norm(zone_weights_vectors[zone][doc_id])

        if terms_type == 'unigram':
            self.docs_weights_vectors = self.title_weight * zone_weights_vectors['title'] \
                                      + self.summary_weight * zone_weights_vectors['summary'] \
                                      + self.content_weight * zone_weights_vectors['content']
        elif terms_type == 'bigram':
            self.docs_bigrams_weights_vectors = self.title_weight * zone_weights_vectors['title'] \
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

    def choose_best_bigram(self, indexers, bigram_indexers, bigram_weights, query):
        
        ranked_new_terms_ids = list(np.argsort(self.rocchio_weights))
        best_bigram_idx = bigram_weights.argmax()
        best_bigram = bigram_indexers['title'].get_term(best_bigram_idx)

        if best_bigram[0] in query and best_bigram[1] in query:
            # don't insert the bigram at all, re-order query so that the two words of bigram are together
            bigram_weights[best_bigram_idx] = 0
            query.remove(best_bigram[0])
            query.remove(best_bigram[1])
            query += [best_bigram[0], best_bigram[1]]
            return self.choose_best_bigram(indexers, bigram_indexers, bigram_weights, query)

        elif best_bigram[0] in query or best_bigram[1] in query:
            # case only one word of bigram in query:
            # put it at the end, add the other word of the bigram to the query,
            # and add a single best word (from rocchio weights)
            query.remove(best_bigram[0] if best_bigram[0] in query else best_bigram[1])
            query += best_bigram

            best_single_words_indexes = list(np.argsort(self.rocchio_weights))

            for i in range(1, len(best_single_words_indexes) + 1):
                term = indexers['title'].get_term(best_single_words_indexes[-i])
                if term not in query:
                    query.append(term)
                    break
        else:
            # none of the two words of the bigram is in the query, add the whole bigram
            query += [best_bigram[0], best_bigram[1]]

        return query

    def enhance(self, query, indexers, relevant, non_relevant, bigram_indexers=None):
        """
        Given the raw query and the index of documents with inverted file computed,
        Runs Rocchio's algorithms and returns the augmented query
        Args:
            query: list of strings (preprocessed)
            indexers: dict of Indexer objects (already built), one for each zone of documents
            relevant: list of ints (doc_ids)
            non_relevant: list of ints (doc_ids)
            binary_indexers: dict of Indexer objects (already built), one for each zone of documents
        """
        self.compute_docs_weights(indexers)
        self.compute_query_weights(indexers['content'], query)

        self.rocchio_weights = self.ALPHA * self.query_weights_vector

        for doc_id in relevant:
            self.rocchio_weights += (self.BETA/len(relevant)) * self.docs_weights_vectors[doc_id]

        for doc_id in non_relevant:
            self.rocchio_weights -= (self.GAMMA/len(non_relevant)) * self.docs_weights_vectors[doc_id]

        self.rocchio_weights = self.rocchio_weights.clip(min=0) # set negative weights to 0

        if bigram_indexers is None:
            # rank words by order:
            ranked_new_terms_ids = list(np.argsort(self.rocchio_weights))
            
            logger.info('[ROCCHIO]\t 10 best new query words: %s', [indexers['content'].get_term(term_idx) for term_idx in ranked_new_terms_ids[-10:]])

            for term in query:
                term_idx = indexers['content'].get_term_idx(term)
                if term_idx in ranked_new_terms_ids:
                    ranked_new_terms_ids.remove(term_idx)

            # add two best words to query:
            query += [indexers['content'].get_term(term_idx) for term_idx in ranked_new_terms_ids[-2:]]

            logger.info('[ROCCHIO]\t 2 new query words: %s', query[-2:])

        else:
            # select best bigram and not only best words:
            bigram_weights = np.zeros(bigram_indexers['title'].vocabulary_size)
            self.compute_docs_weights(bigram_indexers, terms_type='bigram')

            for doc_id in relevant:
                bigram_weights += (self.BETA/len(relevant)) * self.docs_bigrams_weights_vectors[doc_id]

            for doc_id in non_relevant:
                bigram_weights -= (self.GAMMA/len(non_relevant)) * self.docs_bigrams_weights_vectors[doc_id]

            for bigram_idx in range(bigram_weights.shape[0]):
                bigram = bigram_indexers['content'].get_term(bigram_idx)
                if not isinstance(bigram, tuple):
                    print('found not tuple returned by bigram_indexer')
                try:
                    weight_1 = self.rocchio_weights[indexers['content'].get_term_idx(bigram[0])]
                    weight_2 = self.rocchio_weights[indexers['content'].get_term_idx(bigram[1])]
                except Exception:
                    print('pb with bigram: ', bigram)

                # combine single words rocchio weights and the bigram weight:
                bigram_weights[bigram_idx] *= 1/3
                bigram_weights[bigram_idx] += 2/3 * (weight_1 + weight_2)/2 # give more importance to unigram-rocchio weights

            new_query = self.choose_best_bigram(indexers, bigram_indexers, bigram_weights, query)

        # return query as a string an not a list:
        return ' '.join(query)
