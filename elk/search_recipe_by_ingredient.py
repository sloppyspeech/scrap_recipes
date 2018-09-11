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
    'size': 10,
    '_source': ['Recipe.Name', 'Recipe.Url'],
    'query': {
        'match': {
            'Recipe.Ingredients.Name': value_to_search
        }
    }
}
recipes = [
    key['_source'] for key in es.search(
        'allrecipes', body=json.dumps(search_object))['hits']['hits']
]
print(json.dumps(recipes))
recipes = [
    key['_source'] for key in es.search(
        'allrecipes_py', body=json.dumps(search_object))['hits']['hits']
]
print(json.dumps(recipes))

# for i in recipes:
#     print(i)
