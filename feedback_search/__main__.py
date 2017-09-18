#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Columbia University
COMS 6111 - Advanced Database Systems (Fall 2017)
Project 1
Author: Jerome Kafrouni

Implementation of an information retrieval system that exploits user-provided 
relevance feedback to improve the search results returned by Google.
"""
import sys

from feedback_search import query as query_file
from feedback_search import feedback
from feedback_search import enhance_query
from feedback_search import index


def main():
    """
    Main routine, 
    Takes initial query and target_precision provided as input,
    Until target_precision is achieved:
        Runs enhanced query, asks user's feedback, computes new precision.
    """

    if len(sys.argv) != 3:
        print('Use: python -m feedback_search <query> <precision>')
        return

    query = sys.argv[1]

    try:
        target_precision = float(sys.argv[2])
    except ValueError:
        print('<precision> must be a float between 0 and 1 !')
        return

    if target_precision > 1 or target_precision <0:
        print('<precision> must be a float between 0 and 1 !')
        return

    achieved_precision = 0

    indexer = index.Indexer()
    query_optimizer = enhance_query.RocchioQueryOptimizer(1, 1, 1)

    while (achieved_precision < target_precision):
        print('Parameters:')
        print('Query = {}'.format(query))
        print('Precision = {}'.format(target_precision))
        print('')
        
        results = query_file.query_google(query)

        if len(results) < 10:
            print('Too few results, aborting...')
            break

        # Ask feedback to user, store feedback in results dict directly
        feedback.ask_feedback(results)

        relevant = [result for result in results if result['relevant']]
        non_relevant = [result for result in results if not result['relevant']]
        achieved_precision = len(relevant)/len(results)

        if achieved_precision == 0:
            print('Precision@10 is 0, aborting...')
            break

        indexer.reset()
        for document in results:
            indexer.index(document)

        print('Achieved precision: ', achieved_precision)

        query = query_optimizer.enhance(query, indexer.inverted_database, relevant, non_relevant)

if __name__ == '__main__':
    main()