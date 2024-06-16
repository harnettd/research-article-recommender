"""
Set up an API which serves article (DOI) recommendations when 
provided an author's name.
"""
import json
import pickle

from flask import Flask
from flask_restful import Resource, Api, reqparse, abort
from flask_cors import CORS
from pathlib import Path

from src.recommender import Recommender

# Load the authors, dois information.
file_path = Path(__file__)  # the file path of *this* script
project_path = file_path.parent.parent
data_path = project_path.joinpath('data/author_dois.json')
with open(data_path, 'r') as f:
    authors_dois = json.load(f)

# Load the models.
models_path = project_path.joinpath('models')
knn_path = models_path.joinpath('knn.pkl')
mf_path = models_path.joinpath('mf.pkl')
with open(knn_path, 'rb') as f:
    knn = pickle.load(f)
with open(mf_path, 'rb') as f:
    mf = pickle.load(f)

recommender = Recommender(authors_dois, knn, mf)

app = Flask(__name__)
CORS(app)
api = Api(app)

class Authors(Resource):
    def get(self):
        """Return a list of all authors in the data."""
        authors = list(recommender.authors)
        return {'authors': authors}, 200

class DOIs(Resource):
    def get(self):
        """Return a list of all articles (DOIs) in the data."""
        dois = list(recommender.dois)
        return {'dois': dois}, 200
    
parser = reqparse.RequestParser()
parser.add_argument('author', type=str, required=True, help='Missing author')
# TODO: add optional num_recs arg.

class Recommendations(Resource):
    def post(self):
        """Return a list of article recommendations given an author's name."""
        args = parser.parse_args()
        author = args['author']

        if author not in recommender.authors:
            abort(400, message=f'"{author}" not in authors list')

        recommendations = list(recommender.recommend(author))
        response = {
            'recommendations': recommendations,
            'headers': {'Content-Type': 'application/json'}
            }
        return response, 200

api.add_resource(Authors, '/authors')
api.add_resource(DOIs, '/dois')
api.add_resource(Recommendations, '/recommendations')
    

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    # app.run()
