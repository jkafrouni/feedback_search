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
import logging
import threading

from feedback_search import query as query_file
from feedback_search import feedback
from feedback_search import enhance_query
from feedback_search import index
from feedback_search import scrape
from feedback_search import preprocess
from config import ALPHA, BETA, GAMMA

logger = logging.getLogger('feedback_search')
logger.propagate = False # do not log in console
handler = logging.FileHandler('logs/feedback_search.log')
formatter = logging.Formatter(
    fmt='[%(asctime)s %(levelname)s]\t%(message)s',
    datefmt='%d-%m-%Y %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def main():
    """
    Main routine, 
    Takes initial query and target_precision provided as input,
    Until target_precision is achieved:
        Runs enhanced query, asks user's feedback, computes new precision.
    """

    if len(sys.argv) < 3:
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

    logger.info('[MAIN]\t Started with args: QUERY = %s, PRECISION = %s', query, target_precision)

    achieved_precision = 0

    # Build one index for each zone of the documents (see enhance_query):
    indexers = {zone: index.Indexer(zone) for zone in ['title', 'summary', 'content']}
    query_optimizer = enhance_query.RocchioQueryOptimizer(ALPHA, BETA, GAMMA)

    while (achieved_precision < target_precision):
        logger.info('[MAIN]\t achieved precision = %s vs target precision = %s, optimizing...', achieved_precision, target_precision)
        print('Parameters:')
        print('Query = {}'.format(query))
        print('Precision = {}'.format(target_precision))
        print('')
        
        results = query_file.query_google(query)

        # Fetch the whole documents by scraping the urls in results, as a background task
        scraping_thread = threading.Thread(target=scrape.add_url_content, args=(results,))
        scraping_thread.start()

        if len(results) < 10:
            print('Too few results, aborting...')
            break

        # Ask feedback to user, store feedback in results dict directly
        feedback.ask_feedback(results)

        scraping_thread.join() # make sure all the documents have been scraped

        relevant = [doc['id'] for doc in results if doc['relevant']]
        non_relevant = [doc['id'] for doc in results if not doc['relevant']]
        achieved_precision = len(relevant)/len(results) if results else 0

        if achieved_precision == 0:
            print('Precision@10 is 0, aborting...')
            break

        logger.info('[MAIN]\t orginal query: %s', query)
        query = preprocess.split_remove_punctuation(query)
        query = preprocess.stem(query)
        logger.info('[MAIN]\t preprocessed query: %s', query)

        for zone in indexers:
            indexers[zone].reset()
            indexers[zone].index(results, query)

        print('Achieved precision: ', achieved_precision)

        query = query_optimizer.enhance(query, indexers, relevant, non_relevant)

if __name__ == '__main__':
    main()