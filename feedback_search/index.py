import re


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

    def reset(self):
        self.__init__()

    def index(self, document):

        # quick preprocessing of the text:
        terms = re.split('\W+', document['summary']) # split into words, without punctuation
        terms.remove('') # quick fix, regex adds empty string
        terms = [term.lower() for term in terms] # lower everything

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
