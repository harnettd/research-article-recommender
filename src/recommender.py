"""
A recommender class to make journal article recommendations for authors.

This class provides a method that returns a list of recommended articles.

Attributes:
    author_dois: A dictionary of authors and articles (DOIs) each has cited
    authors: The set of authors in the data
    dois: The set of articles (DOIs) in the data
    knn: A k-Nearest Neighbours model that has been fitted to the data
    mf: A matrix factorization model that has been fitted to the data
"""
import pandas as pd


class Recommender:
    def __init__(self, author_dois: dict, knn, mf) -> None:
        """
        Initilize the recommender

        :param author_dois: Authors and articles (DOIs) each has cited
        :type author_dois: dict

        :param knn: A fitted k-Nearest Neighbours model

        :param mf: A fitted matrix factorization model
        """
        # authors and their citations
        self.author_dois = author_dois
        
        # the set of authors
        self.authors = set(self.author_dois.keys())
        
        # the set of DOIs
        self.dois = set()
        for doi_list in self.author_dois.values():
            self.dois = self.dois.union(set(doi_list))

        self.knn = knn
        self.mf = mf

    def _model_recommend(
        self, author: str, model, num_recs: int
    ) -> set:
        """
        Return article recommendations for an author.

        :param author: An author's name
        :type: str

        :param: A fitted model, either self.knn or self.mf

        :param num_recs: The number of recommendations to return
        :type num_recs: int

        :return: Article recommendations
        :rtype: set
        """
        if author not in self.authors:
            raise ValueError(
                f'Expected author in self.authors, got {author}'
            )
        
        # the set of articles this author has not cited
        uncited_dois = self.dois - set(self.author_dois[author])

        # Generate a predicted rating for each uncited article.
        estimates = {}
        for doi in uncited_dois:
            est = model.predict(author, doi).est
            estimates[doi] = est

        # Get the articles with the top ratings.
        estimates_ser = pd.Series(estimates)
        recommendations = estimates_ser\
            .sort_values(ascending=False)\
            .head(num_recs)\
            .index\
            .to_list()
        
        return set(recommendations)

    def knn_recommend(
        self, author: str, num_recs: int = 5
    ) -> set:
        """
        Return article recommendations for an author using kNN.

        :param author: An author's name
        :type: str

        :param num_recs: The number of recommendations to return
        :type num_recs: int

        :return: Article recommendations
        :rtype: set
        """
        return self._model_recommend(author, self.knn, num_recs)
    
    def mf_recommend(
        self, author: str, num_recs: int = 5
    ) -> set:
        """
        Return article recommendations for an author using MF.

        :param author: An author's name
        :type: str

        :param num_recs: The number of recommendations to return
        :type num_recs: int

        :return: Article recommendations
        :rtype: set
        """
        return self._model_recommend(author, self.mf, num_recs)
    
    def recommend(
        self, author: str, num_recs: int = 10
    ) -> set:
        """
        Return (unioned) article recommendations for an author.

        :param author: An author's name
        :type: str

        :param num_recs: The number of recommendations
        :type num_recs: int

        :return: Article recommendations
        :rtype: set
        """
        knn_recs = self.knn_recommend(author, num_recs // 2)
        mf_recs = self.mf_recommend(author, num_recs // 2)
        return knn_recs.union(mf_recs)


if __name__ == '__main__':
    print(__doc__)
