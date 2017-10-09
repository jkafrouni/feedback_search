from feedback_search import constants
from feedback_search import __main__
import sys
import importlib
import json
import pprint

def test_constants(query, test_constants):
    # change values of constants from constants.py:
    constants.title_weight = test_constants['title_weight']
    constants.summary_weight = test_constants['summary_weight']
    constants.content_weight = test_constants['content_weight']

    print('===============================================')
    print('Testing with ', test_constants)
    importlib.reload(__main__)

    # should be replaced by real mock solution:
    if len(sys.argv) < 3:
        sys.argv += [query, 0.9]
    else:
        sys.argv[1] = query # should be replaced by real mock solution
        sys.argv[2] = 0.9

    augmented_query = __main__.main(is_test=True)

    with open('tests/parameters_tuning.txt', 'a') as outfile:
        outfile.write('\n\n===============================================')
        outfile.write('\nInitial query: ' + query)
        outfile.write('\nConstants: ')
        for constant in test_constants:
            outfile.write('\n\t %s : %s' % (constant, test_constants[constant]))
        outfile.write('\nAugmented query: ' + augmented_query)

    print('Test done, augmented query: ', augmented_query)