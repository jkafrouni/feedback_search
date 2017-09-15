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


def main():
    """
    Main routine, 
    Takes initial_query and target_precision provided as input,
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

    while achieved_precision < target_precision:
        print('Parameters:')
        print('Query = {}'.format(query))
        print('Precision = {}'.format(target_precision))
        print('')
        
        results = query_file.query_google(query)
        feedback.ask_feedback(results)

        achieved_precision = len([result['relevant'] for result in results if result['relevant'] == 1])/len(results)

        print('Achieved precision: ', achieved_precision)

        new_query = enhance_query.enhance_query(query, results)

if __name__ == '__main__':
    main()