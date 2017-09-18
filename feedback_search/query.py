from googleapiclient.discovery import build
from config import DEVELOPER_KEY, SEARCH_ENGINE_ID


def query_google(query):
    """
    Given a query, sends it to google, returns a list of the top 10 results' url, link, summary
    Each result is given an id which is his rank in the results
    """

    # Build a service object for interacting with the API.
    service = build("customsearch", "v1", developerKey=DEVELOPER_KEY)

    res = service.cse().list(
        q=query,
        cx=SEARCH_ENGINE_ID,
    ).execute()

    items = res['items']
    short_items = [{'id': idx, 'url': item['link'], 'title': item['title'], 'summary': item['snippet']} for idx, item in enumerate(items)]

    return short_items