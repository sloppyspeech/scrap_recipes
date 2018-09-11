from elasticsearch import Elasticsearch
import json
import sys
import argparse

parser = argparse.ArgumentParser(
    prog        = 'search_recipe_by_ingredient.py',
    description = 'Search Recipes by Ingredient')
parser.add_argument('ingredient', help='Name of the ingredient to be searched in recipes')
args = parser.parse_args()
# print(args.ingredient)

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
value_to_search = args.ingredient
search_object = {
    'size': 1000,
    '_source': ['Recipe.Name', 'Recipe.Url'],
    'query': {
        'match': {
            'Recipe.Ingredients.Name': value_to_search
        }
    }
}
recipes =sorted( [
    key['_source']['Recipe']['Name'] for key in es.search(
        'allrecipes', body=json.dumps(search_object))['hits']['hits']
])
for idx,recipe in enumerate(recipes):
    print("{0}) {1}".format(str(idx),recipe))

