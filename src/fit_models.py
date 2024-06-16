"""
Load the author-reference-count CSV file into a Dataset. 
Fit a k-NN model and apply matrix factorization.
"""
import pandas as pd
import pickle

from math import floor, ceil
from pathlib import Path
from surprise import Dataset, Reader, KNNWithMeans, SVD
from surprise.model_selection import GridSearchCV


def load_data(data_path):
    """
    Return a Dataset corresponding to the author-reference-count data.

    Each line of the CSV file should be of the form:
        author, doi, count

    :param data_path: The path of the CSV data file
    :type data_path: Path

    :return: A Dataset of the author-doi-count data
    :rtype: Dataset
    """
    # Load data into a DataFrame.
    names = ['author', 'doi', 'count']
    df = pd.read_csv(data_path, sep=',', names=names, header=0)
    
    # Define a Reader.
    rating_max = ceil(df['count'].max())
    rating_min = floor(df['count'].min())
    rating_scale = (rating_min, rating_max)
    reader = Reader(rating_scale=rating_scale)

    return Dataset.load_from_df(df, reader)


def fit_knn(data):
    """
    Return a fitted and tuned k-Nearest Neighbours model.
    """
    param_grid = {
        'k': [20, 40, 60],
        'min_k': [1, 2, 3],
        'verbose': [False],
        'sim_options': {
            'name': ['msd', 'cosine', 'pearson'],
            'user_based': [True]
        }
    }
    gs = GridSearchCV(
        KNNWithMeans, 
        param_grid, 
        measures=['mae'], 
        cv=3
    )
    gs.fit(data)

    knn = gs.best_estimator['mae']
    knn.fit(data.build_full_trainset())
    return knn


def fit_svd(data):
    """
    Return a fitted and tuned SVD matrix-factorization model.
    """
    param_grid = {
        'n_factors': [50, 100, 150],
        'n_epochs': [25, 50, 100],
        'lr_all': [0.001, 0.01, 0.1],
        'reg_all': [0.01, 0.1]
    }
    gs = GridSearchCV(
        SVD,
        param_grid=param_grid,
        measures=['mae'],
        cv=3
    )
    gs.fit(data)

    svd = gs.best_estimator['mae']
    svd.fit(data.build_full_trainset())
    return svd


def main():
    # Load the author-doi-count data into a Dataset.
    file_path = Path(__file__)  # the path of this script
    data_dir = file_path.parent.parent.joinpath('data')
    data_path = data_dir.joinpath('author_doi_count.csv')
    data = load_data(data_path)

    # Fit a k-Nearest Neighbours model.
    knn = fit_knn(data)

    # Fit a matrix-factorization model.
    mf = fit_svd(data)

    # Pickle both models.
    file_path = Path(__file__)  # the path of this script
    models_dir = file_path.parent.parent.joinpath('models')
    knn_path = models_dir.joinpath('knn.pkl')
    mf_path = models_dir.joinpath('mf.pkl')
    
    with open(knn_path, 'wb') as f:
        pickle.dump(knn, f)

    with open(mf_path, 'wb') as f:
        pickle.dump(mf, f)


if __name__ == '__main__':
    main()
