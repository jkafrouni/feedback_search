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

from googleapiclient.discovery import build
from config import DEVELOPER_KEY, SEARCH_ENGINE_ID

def main():
    """Main routine, queries Google Search API"""
    args = sys.argv[1:]

    if len(sys.argv) != 3:
        print('Use: python -m feedback_search <query> <precision>')
        return

    query = sys.argv[1]
    precision = sys.argv[2]

    print('Parameters:')
    print('Query = {}'.format(query))
    print('Precision = {}'.format(precision))
    
    print('Google Search Results:')
    print('======================')

    # Build a service object for interacting with the API.
    service = build("customsearch", "v1", developerKey=DEVELOPER_KEY)

    res = service.cse().list(
        q=query,
        cx=SEARCH_ENGINE_ID,
    ).execute()

    items = res['items']

    short_items = [{'url': item['link'], 'title': item['title'], 'summary': item['snippet']} for item in items]

    for i, short_item in enumerate(short_items):
        print('Result ', i+1)
        print('[')
        print('URL: ', short_item['url'])
        print('Title: ', short_item['title'])
        print('Summary: ', short_item['summary'])
        print('] \n')

if __name__ == '__main__':
    main()