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
import os

from feedback_search import query as query_file
from feedback_search import feedback
from feedback_search import enhance_query
from feedback_search import index
from feedback_search import scrape
from feedback_search import preprocess
from feedback_search import constants

from tests import mock_feedback, mock_query_and_scraping

logger = logging.getLogger('feedback_search')
logger.propagate = False # do not log in console
os.makedirs('logs', exist_ok=True) # create directory for logs if it's not there already
handler = logging.FileHandler('logs/feedback_search.log')
formatter = logging.Formatter(
    fmt='[%(asctime)s %(levelname)s]\t%(message)s',
    datefmt='%d-%m-%Y %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def main(is_test=False):
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

    logger.info('\n\n ========================================================================\n\n')
    logger.info('[MAIN]\t\t Started with args: QUERY = %s, PRECISION = %s', query, target_precision)

    achieved_precision = 0

    # Build one index for each zone of the documents (see enhance_query):
    indexers = {zone: index.UnigramIndexer(zone) for zone in ['title', 'summary', 'content']}
    bigram_indexers = {zone: index.BigramIndexer(zone) for zone in ['title', 'summary', 'content']}

    query_optimizer = enhance_query.RocchioQueryOptimizer()

    while (achieved_precision < target_precision):
        logger.info('[MAIN]\t\t achieved precision = %s vs target precision = %s, optimizing...', achieved_precision, target_precision)
        print('Parameters:')
        print('Query = {}'.format(query))
        print('Precision = {}'.format(target_precision))
        print('')
        
        if not is_test:
            results = query_file.query_google(query)

            # Fetch the whole documents by scraping the urls in results, as a background task
            scraping_thread = threading.Thread(target=scrape.add_url_content, args=(query, results))
            scraping_thread.start()

            if len(results) < 10:
                print('Too few results, aborting...')
                break

            # Ask feedback to user, store feedback in results dict directly
            feedback.ask_feedback(results)
            scraping_thread.join() # make sure all the documents have been scraped

        elif is_test:
            results = mock_query_and_scraping.load_query_results(query)
            mock_feedback.mock_feedback(results, query=query)

        relevant = [doc['id'] for doc in results if doc['relevant']]
        non_relevant = [doc['id'] for doc in results if not doc['relevant']]
        achieved_precision = len(relevant)/len(results) if results else 0

        if achieved_precision == 0:
            print('Precision@10 is 0, aborting...')
            break

        logger.info('[MAIN]\t\t orginal query: %s', query)
        query = preprocess.split_remove_punctuation(query)
        if constants.USE_STEMMING:
            query = preprocess.stem(query)
        logger.info('[MAIN]\t\t preprocessed query: %s', query)

        indexing_threads = []
        for zone in indexers:
            indexers[zone].reset()
            t = threading.Thread(target=indexers[zone].index, args=(results, query))
            t.start()
            indexing_threads.append(t)
        
        for zone in bigram_indexers:
            bigram_indexers[zone].reset()
            t = threading.Thread(target=bigram_indexers[zone].index, args=(results, query))
            t.start()
            indexing_threads.append(t)

        for t in indexing_threads:
            t.join()

        print('Achieved precision: ', achieved_precision)

        query = query_optimizer.enhance(query, indexers, relevant, non_relevant, bigram_indexers=bigram_indexers)

        if is_test:
            # in tests we do unly one run of the query optimizer with mock feedback and analyze it
            return query

if __name__ == '__main__':
    main()