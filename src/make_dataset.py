"""
Parse downloaded articles to a form suitable for input into scikit-surprise.
Dump the results to a CSV file.
"""
import json
import numpy as np
import pandas as pd
import re

from collections import defaultdict
from datetime import date
from pathlib import Path


def extract_doi(reference: dict) -> str:
    """Return the DOI from a reference."""
    # Get all of the article's listed IDs.
    ids: str = reference.get('cited')
    if ids is None:
        return None

    # Extract the DOI if it's present.
    match = re.search('doi:(\S*)', ids)    
    if match is None:
        return None
    
    return match.group(1)


def parse_article(article: dict) -> tuple:
    """
    Return the DOI, authors, year, and reference DOIs of an article.
    """
    doi: str = article.get('doi')
    authors: list = article.get('authors')
    year: int = article.get('yearPublished')
    refs: list = article.get('references')
    if refs is None:
        return doi, authors, refs
    
    ref_dois = [extract_doi(ref) for ref in refs]
    return doi, authors, year, ref_dois


def preprocess_name(name: str) -> str:
    """Collapse whitespace sequences to a single space in a name."""
    return re.sub('\s+', ' ', name)


def score_citation(year: int, half_life: float = 25.0) -> float:
    """
    Return the rating of a citation.
    
    In order to promote newer work, citations of newer articles 
    count more than older ones. An exponential scale is used such that
    citations have a half-life.
    
    :param year: The publication date of the cited article
    :type: int

    :param half_life: Time, in years, until a citation's score is halved
    :type half_life: float

    :return: The citation's (scaled) score
    :rtype: float

    Usage examples:
    >>> score_citation(2024, 25.0)
    1.0
    >>> round(score_citation(1999, 25.0), 1)
    0.5
    """
    age = date.today().year - year
    exp_time_constant = half_life / np.log(2)
    return np.exp(- age / exp_time_constant)


def to_nested_list(nested_dict):
    """
    Convert a nested dictionary to a nested list.
    
    Convert
        d = {
            'k1': {'a': 1, 'b': 2}, 
            'k2': {'c', 3}
        }
    to
        [
            ['k1', 'a', 1],
            ['k1', 'b', 2],
            ['k2', 'c', 3]
        ]
    """
    nested_list = []
    for (outer_key, outer_dict) in nested_dict.items():
        for (inner_key, val) in outer_dict.items():
            nested_list.append([outer_key, inner_key, val])
    return nested_list


def trim_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Trim the outliers from df.

    Each line of the DataFrame df is of the form

        author, doi, count.
    
    A handful of authors and DOIs represent major outliers.
    As this data is being used to train a recommender, it would be
    best to remove extremely well-known papers as well as not let
    the preferences of a few authors dominate recommendations.
    Therefore, we'll remove the top 5% of DOIs and the top 5% of
    authors from the data.  
    """
    # We'll trim authors and DOIs whose count totals are above quartile.
    quartile = 0.95
    
    # Identify top authors to trim.
    author_sum = df[['author', 'count']].groupby('author').sum()
    author_class = pd.qcut(
        author_sum['count'], 
        [0, quartile, 1.], 
        ['not top author', 'top author']
    )
    not_top_authors = author_class[author_class == 'not top author']\
        .index.to_list()
    author_filter = df['author'].isin(not_top_authors)

    # Identify top DOIs to trim.
    doi_sum = df[['doi', 'count']].groupby('doi').sum()
    doi_class = pd.qcut(
        doi_sum['count'], 
        [0, quartile, 1.], 
        ['not top doi', 'top doi']
    )
    not_top_dois = doi_class[doi_class == 'not top doi']\
        .index.to_list()
    doi_filter = df['doi'].isin(not_top_dois)

    return df[author_filter & doi_filter]


def main():
    # Read in articles JSON data.
    file_path = Path(__file__)  # the path of this script
    data_path = file_path.parent.parent.joinpath('data/articles.json')
    with open(data_path, 'r') as f:
        articles = json.load(f)

    # Loop through the articles. For each article, extract the DOI, the list 
    # of authors, the publication year, and the list of DOIs of the references. 
    # Track how many times each author has cited each reference.
    # Also, track the year the DOI was published.
    author_doi_counts = defaultdict(dict)
    doi_year = {}
    for article in articles:
        doi, authors, year, refs = parse_article(article)
        if doi and authors and year and refs:
            doi_year[doi] = year
            for author in authors:
                name = author.get('name')
                if name is not None:
                    name = preprocess_name(name)
                    author_doi_counts[name][doi] = 1
                    for ref in refs:
                        if ref in author_doi_counts[name].keys():
                            author_doi_counts[name][ref] += score_citation(year)
                        else:
                            author_doi_counts[name][ref] = score_citation(year)

    # Write raw data (i.e., author_doi_counts) to JSON files.
    data_dir = file_path.parent.parent.joinpath('data')
    data_path = data_dir.joinpath('author_doi_count_raw.json')
    with open(data_path, 'w') as f:
        json.dump(author_doi_counts, f)

    # Write raw data (i.e., author_doi_counts) to a CSV file. 
    # This version is mainly for debugging and EDA. Note that 
    # each line of the CSV is of the form:
    #   author, doi, count
    names = ['author', 'doi', 'count']
    dataset = pd.DataFrame(to_nested_list(author_doi_counts), columns=names)
    data_path = data_dir.joinpath('author_doi_count_raw.csv')
    dataset.to_csv(data_path, sep=',', header=False, index=False)

    # Preprocess the raw dataset and write it to CSV.
    dataset_preprocessed = dataset.pipe(trim_outliers)
    data_path = data_dir.joinpath('author_doi_count.csv')
    dataset_preprocessed.to_csv(data_path, sep=',', header=False, index=False)

    # Write doi_year to a JSON file.
    data_path = data_dir.joinpath('doi_year.json')
    with open(data_path, 'w') as f:
        json.dump(doi_year, f)

    # Create a dictionary of authors and their cited DOIs, and write it
    # to a JSON file.
    dp = dataset_preprocessed  # an alias
    authors = dp['author'].unique().tolist()
    author_dois =\
        {a: dp[dp['author'] == a]['doi'].to_list() for a in authors}
    data_path = data_dir.joinpath('author_dois.json')
    with open(data_path, 'w') as f:
        json.dump(author_dois, f)


if __name__ == '__main__':
    main()
