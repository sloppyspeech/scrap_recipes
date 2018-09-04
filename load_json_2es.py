import requests, json, os
from elasticsearch import Elasticsearch

es = Elasticsearch([{'host': 'localhost', 'port': '9200'}])
data=json.loads(open('all_recipes.json').read())
for d in data:
    es.index(index='allrecipes_py', doc_type='Indian',  body=d)

