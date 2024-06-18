"""
Set the query parameters used to search the CORE API.
"""
# Search the CORE API for these terms (there's an implied OR) 
# in the title, abstract, and full text of the article (if available).
SEARCH_TERMS = ['diquark', 'tetraquark', 'pentaquark']

# Search for articles published on or after this year.
YEAR = 2000

# The maximum number of articles to be found. Note that 10,000 is
# the upper limit here without a special ID needed for larger
# queries.
LIMIT = 1000


if __name__ == '__main__':
    print(__doc__)
