# scrap_recipes
#####Test script to scrap few recipes from https://tarladalal.com. Output is in csv and json formats.

#####Supports Python 3.6
###### Run as follows 
```
python3.6 -m venv <env_name>
source <env_name>/bin/activate
git clone https://github.com/sloppyspeech/scrap_recipes.git
pip install -r requirements.txt
```
###### Run the scrapper with "y" to scrap
```
python3.6 scrap_recipes.py y 
```
This will scrap the website and generate csv and json output

###### Load via Logstash to ES
use the name of the output json file above and update the allrecipes_2es.conf
```
logstash -f ./allrecipes_2es.conf
```

###### Load via Python to ES
update the name of the json file in load_json_2es.py
```
python3.6 load_json_2es.py
````

##### Assumptions
Elasticsearch is hosted on localhost:9200

Logstash and Kibana are installed
