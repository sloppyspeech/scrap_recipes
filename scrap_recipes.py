from bs4 import BeautifulSoup as soup
import time
import requests as req
import json
import pandas as pd
import sys
from tqdm import tqdm

def get_ingredient_by_recipe(recipe_name,recipe_url,output_file):
    requrl=req.get(recipe_url)
    requrl.raise_for_status()
    souped=soup(requrl.content,'html.parser')
    for rec_ing in souped.findAll('span',attrs={'itemprop':'recipeIngredient'}):
        ingrd_text=rec_ing.get_text().replace(',','')
        if  ingrd_text[0].isdigit():
            ingrd_text=','.join(ingrd_text.split(' ',2)).strip(' ')
        else:
            ingrd_text=',,{0}'.format(ingrd_text).strip(' ')
        output_file.write('{0},{1},{2}\n'.format(recipe_name,ingrd_text,recipe_url))

def get_recipes_list(base_url,output_file):
    mainUrl=base_url+'recipes-for-indian-veg-recipes-2?pageindex='
    with open(output_file,'w') as out_file:
        out_file.write('recipe_name,quantity,measurement_unit,ingredient,recipe_url\n')
        for recipe_pageindex in tqdm(range(307)):
            raw_url=mainUrl+str(recipe_pageindex+1)
            # print(raw_url)
            opened_url=req.get(raw_url)
            souped_up=soup(opened_url.content,'html.parser')
            for recipe_span in souped_up.find_all('span',attrs={'class':'rcc_recipename'}):
                span_children=recipe_span.findChildren('a',recursive=False)[0]
                indiv_recipe_url=base_url+span_children.get('href')
                indiv_recipe_name=span_children.get_text().replace(',','')
                get_ingredient_by_recipe(indiv_recipe_name,indiv_recipe_url,out_file)

def create_recipes_json(input_file,output_file):
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
        out_file.write(json.dumps(dict(Recipes=records),indent=4))

if __name__=='__main__':
    csv_filename='recipe_ingredients.csv'
    json_filename='recipe_ingredients.json'
    get_recipes_list('https://www.tarladalal.com/',csv_filename)
    create_recipes_json(csv_filename,json_filename)
