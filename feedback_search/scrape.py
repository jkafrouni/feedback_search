from urllib.request import urlopen
import urllib.error
import http.client
import logging
from multiprocessing.dummy import Pool as ThreadPool

from bs4 import BeautifulSoup

logger = logging.getLogger('feedback_search')


def scrape(url):
    """
    Given a url, returns the document as plain text
    """
    logger.debug('[SCRAPER]\t Loading url: %s', url)
    try:
        html_page = urlopen(url).read()
    except (http.client.IncompleteRead, urllib.error.URLError):
        logger.warning("[SCRAPER]\t Could not read the page for url: %s", url)
        return None
    logger.debug('[SCRAPER]\t Parsing with BS')
    soup = BeautifulSoup(html_page, 'html5lib')
    data = soup.findAll('p')
    data = [p.get_text().replace('\n', '').replace('\t','') for p in data]

    if not data:
        log.info('[SCRAPER]\t No data found')

    return ' '.join(data) if data else None


def add_url_content(documents):
    """
    Given a list of documents as jsons containing a url field,
    Tries to scrape the corresponding url and extract the body
    And if scraping goes well, stores result in a 'content' field in the json
    Returns when all urls have been processed
    """
    def scrape_and_update(doc):
        text = scrape(doc['url'])
        if text is not None:
            logger.debug('[SCRAPER]\t Updating "content" for url %s', doc['url'])
            doc.update({'content': text})

    with ThreadPool(processes=10) as pool:
        for doc in documents:
            pool.apply_async(scrape_and_update, args=(doc,))
        pool.close()
        pool.join()
