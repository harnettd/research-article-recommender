"""
Download information on research articles using the CORE API: 

    https://api.core.ac.uk/docs/v3.

For each article, get a list of references from the OpenCitation API:

    https://opencitations.net/index/api/v2.

Save data to an external file.
"""
import json
import os
from pathlib import Path
import requests
from requests.exceptions import HTTPError

from search import SEARCH_TERMS, YEAR, LIMIT


def get_articles(query: str, limit: int) -> list[dict]:
    """
    Get articles using the CORE API.

    :param query: The search query to pass to the CORE API
    :type query: str

    :param limit: The maximum number of articles to get
    :type limit: int

    :return: A list of articles matching the search query
    :rtype: list[dict]
    """
    # the CORE API URL
    api_url = 'https://api.core.ac.uk/v3/search/works'
    
    params = {
        'q': query,
        'limit': limit
    }

    apikey_core = os.getenv('APIKEY_CORE')
    headers = {
        'Authorization': apikey_core,
        'Accept': 'application/json'
    }

    try:
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        raise http_err
    except Exception as err:
        raise err
    else:
        # The get request was successful.
        try:
            results = response.json()['results']
        except KeyError as key_error:
            print(f'Key error occurred, there are no results, {key_error}')
            raise key_error
        except Exception as err:
            raise err
        else:
            return results


def get_references(article: dict) -> list[dict]:
    """
    Get a list of references for a given article.

    :param article: An article (dict) with "doi" as a key
    :type article: dict

    :return: A list of references from the article
    :rtype: list[dict]
    """
    doi = article['doi']
    # the OpenCitations API URL
    api_url = 'https://opencitations.net/index/api/v2/references'
    api_route = f'{api_url}/doi:{doi}'

    apikey_open_citations = os.getenv('APIKEY_OPENCITATIONS')
    headers = {
        'Authorization': apikey_open_citations,
        'Accept': 'application/json'
    }

    try:
        response = requests.get(api_route, headers=headers)
        response.raise_for_status()
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        raise http_err
    except Exception as err:
        raise err
    else:
        # The get request was successful.
        return response.json()
    

def main():
    # Combine search terms with OR.
    search = f'({" OR ".join(SEARCH_TERMS)})'
    
    query = f'{search} AND _exists_:doi AND publishedDate>={YEAR}'
    articles = get_articles(query=query, limit=LIMIT)
    
    for article in articles:
        article['references'] = get_references(article)
    
    # Dump the collected data to a JSON file.
    file_path = Path(__file__)
    data_path = file_path.parent.parent.joinpath('data/articles.json')
    with open(data_path, 'w') as f:
        json.dump(articles, f)


if __name__ == '__main__':
    main()
