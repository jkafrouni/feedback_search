"""
Rules:

- Automatical enhancement, no further human input after feedback has been given
- Introduce at most 2 new words
- Cannot delete any words of the input query
- Queries should only contain words, no additional operators
- Words can (and should) be reordered
"""
import math
import re


class RocchioQueryOptimizer:

    def __init__(self, ALPHA, BETA, GAMMA):
        self.ALPHA = ALPHA
        self.BETA = BETA
        self.GAMMA = GAMMA

    def enhance(self, query, inverted_db, relevant, non_relevant):

        # quick preprocessing of the query:
        query = re.split('\W+', query) # split into words, without punctuation
        if '' in query: # quick fix, regex adds empty string
            query.remove('') 
        query = [term.lower() for term in query] # lower everything

        # initialize tf-idf weights vectors:
        query_weights_vector = dict()
        new_query_weights_vector = dict()
        for document in relevant + non_relevant:
            document['weights_vector'] = dict()

        # the vocabulary is all the index words in inverted_db:
        for term in inverted_db.keys():
            # idf of the term:
            idf = math.log((len(relevant) + len(non_relevant))/len(inverted_db[term]))

            # Vector representation of query, using tf-idf weights:
            query_weights_vector[term] = math.log(1 + query.count(term), 10) * idf

            # Vector representation of docs, using tf-idf weights:
            for document in relevant + non_relevant:
                if term in document['tf_vector']:
                    document['weights_vector'][term] = math.log(1 + document['tf_vector'][term], 10) * idf
                else:
                    document['weights_vector'][term] = 0

            # TODO: make calculus look nicer
            rocchio_first_term = self.ALPHA * query_weights_vector[term]
            
            rocchio_second_term = 0
            for document in relevant:
                rocchio_second_term += document['weights_vector'][term]
            rocchio_second_term *= (self.BETA/len(relevant))

            rocchio_third_term = 0
            for document in non_relevant:
                rocchio_third_term += document['weights_vector'][term]
            rocchio_third_term *= (self.GAMMA/len(non_relevant))

            new_query_weights_vector[term] =  max(0, rocchio_first_term + rocchio_second_term - rocchio_third_term)

        # rank words by order:
        ranked_new_query_words = sorted(new_query_weights_vector, key=new_query_weights_vector.get)
        for term in query:
            if term in ranked_new_query_words:
                ranked_new_query_words.remove(term)

        # add two best words to query:
        return query + ranked_new_query_words[-2:]


