import json


def load_query_results(query):
    with open('tests/query_history.json', 'r') as outfile:
        try:
            saved_queries = json.load(outfile)
            return saved_queries[query]
        except Exception as e:
            log.error('[TEST]\t Error while loading saved query results:')
            log.error('[TEST]\t ', e)
            return

def save_query_and_scraping_results(query, documents):
    """
    Saves the results from google query + scraping in a file to run tests without querying google / scraping
    """
    try:
        with open('tests/query_history.json', 'r') as outfile:
            try:
                saved_queries = json.load(outfile)
            except Exception:
                saved_queries = {}
        with open('tests/query_history.json', 'w') as outfile:
            saved_queries[query] = documents
            json.dump(saved_queries, outfile, sort_keys=True, indent=4, separators=(',', ': '))
    except Exception:
        # make sure this doesn't make the main process crash, this is only a side feature
        return