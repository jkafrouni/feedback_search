import re

from pprint import pprint


def ask_feedback(query_results):
    """Given a list of query_results, asks feedback to the user and adds it to each JSON in the list"""

    print('Google Search Results:')
    print('======================')

    for i, result in enumerate(query_results):
        print('Result ', i+1)
        print('[')
        print('URL: ', result['url'])
        print('Title: ', result['title'])
        print('Summary: ', result['summary'])
        print('] \n')

        relevant = input("Relevant (Y/N)?")
        if not re.match("^[Y,y,N,n]{1,1}$", relevant):
            print('Please type in Y or N (or y or n)')
            relevant = input("Relevant (Y/N)?")

        result.update({'relevant': True if relevant.upper() == "Y" else False})

    return query_results
