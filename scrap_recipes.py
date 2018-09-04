from bs4 import BeautifulSoup as soup
import time
import requests as req
import json
import pandas as pd
import sys
from tqdm import tqdm
import logging


def get_ingredient_by_recipe(recipe_name,recipe_url,output_file):
    requrl=req.get(recipe_url)
    # requrl.raise_for_status()
    souped=soup(requrl.content,'html.parser')
    logger.debug('get_ingredient_by_recipe for :'+recipe_name)
    logger.debug('recipe_url:'+recipe_url)
    for rec_ing in souped.findAll('span',attrs={'itemprop':'recipeIngredient'}):
        ingrd_text=rec_ing.get_text().replace(',','').replace('"','')
        if  ingrd_text[0].isdigit():
            ingrd_text=','.join(ingrd_text.split(' ',2)).strip(' ')
            if ingrd_text.count(',') == 1:
                ingrd_text=ingrd_text.split(',',1)[0].strip(' ')+',,'+ingrd_text.split(',',1)[1].strip(' ')
        else:
            ingrd_text=',,{0}'.format(ingrd_text).strip(' ')
        output_file.write('{0},{1},{2}\n'.format(recipe_name,ingrd_text,recipe_url))

def get_recipes_list(base_url,output_file,url2skip):
    mainUrl=base_url+'recipes-for-indian-veg-recipes-2?pageindex='
    with open(output_file,'w') as out_file:
        out_file.write('recipe_name,quantity,measurement_unit,ingredient,recipe_url\n')
        for recipe_pageindex in tqdm(range(1)):
            raw_url=mainUrl+str(recipe_pageindex)
            logger.debug('get_recipes_list')
            logger.debug('raw_url:'+raw_url)
            opened_url=req.get(raw_url)
            souped_up=soup(opened_url.content,'html.parser')
            for recipe_span in souped_up.find_all('span',attrs={'class':'rcc_recipename'}):
                span_children=recipe_span.findChildren('a',recursive=False)[0]
                recipe_url=span_children.get('href')
                indiv_recipe_url=base_url+recipe_url
                indiv_recipe_name=span_children.get_text().replace(',','')
                if recipe_url in url2skip:
                    logger.debug('Skipping '+indiv_recipe_url)
                else:
                    get_ingredient_by_recipe(indiv_recipe_name,indiv_recipe_url,out_file)

def create_recipes_json(input_file,output_file):
    logger.debug('create_recipes_json ')
    logger.debug('Input file :'+input_file)
    logger.debug('Output file :'+output_file)
    df=pd.read_csv(input_file)
    records=[]
    for key,grp in df.groupby('recipe_name'):
        records.append({
        "Recipe":
            {   "Name":key,
                "Url": grp.recipe_url.iloc[0],
                "Ingredients": [
                    { 'Name':row.ingredient, 'Quantity': str(row.quantity)+" "+str(row.measurement_unit) } for row in grp.itertuples()
                ]
            }
        })
    with open(output_file,'w') as out_file:
        out_file.write(json.dumps(records))
        # out_file.write(json.dumps(records,indent=4))

if __name__=='__main__':
    # url2skip=('Mutter-Paneer-Delicious-11529r')
    url2skip=()
    csv_filename='recipe_all.csv'
    json_filename='recipe_all.json'

    #Logger settings
    logging.basicConfig(filename="scrap_recipes.log",
                        format='%(asctime)s [%(levelname)s] %(message)s',
                        filemode='w')

    #Creating an object
    logger=logging.getLogger('scrappy')
    
    #Setting the threshold of logger to DEBUG
    logger.setLevel(logging.DEBUG)

    logger.debug('Scrapping Started with argument '+sys.argv[1])
    #scrap the data with option "y", if csv already exists, just create the json
    if sys.argv[1] == 'y':
        get_recipes_list('https://www.tarladalal.com/',csv_filename,url2skip)
    create_recipes_json(csv_filename,json_filename)
