from bs4 import BeautifulSoup as soup, NavigableString, Comment
import time
import cloudscraper
import json
import pandas as pd
import sys
from tqdm import tqdm
import logging
import re
import argparse


def create_scraper():
    '''Create a cloudscraper session to bypass Cloudflare'''
    return cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )


def extract_time_fields(souped):
    '''
    Extract all time-related fields and Makes from the recipe page.
    Returns a dict with keys: soaking_time, preparation_time, cooking_time,
    baking_time, baking_temperature, sprouting_time, total_time, makes
    '''
    time_data = {
        'soaking_time': '',
        'preparation_time': '',
        'cooking_time': '',
        'baking_time': '',
        'baking_temperature': '',
        'sprouting_time': '',
        'total_time': '',
        'makes': ''
    }

    # Map h6 label text to dict keys
    label_map = {
        'soaking time': 'soaking_time',
        'preparation time': 'preparation_time',
        'cooking time': 'cooking_time',
        'baking time': 'baking_time',
        'baking temperature': 'baking_temperature',
        'sprouting time': 'sprouting_time',
        'total time': 'total_time',
        'makes': 'makes'
    }

    # Find all div.content sections that contain h6 headers
    content_divs = souped.find_all('div', attrs={'class': 'content'})
    for cd in content_divs:
        h6 = cd.find('h6')
        if h6:
            label = h6.get_text().strip().lower()
            if label in label_map:
                # Value is in full text minus the label
                full_text = cd.get_text().strip()
                value = full_text.replace(h6.get_text().strip(), '').strip()
                time_data[label_map[label]] = value

    return time_data


def extract_tags(souped):
    '''Extract recipe tags from the page'''
    tags_list = souped.find('ul', attrs={'class': 'tags-list'})
    if tags_list:
        tags = [li.get_text().strip() for li in tags_list.find_all('li') if li.get_text().strip()]
        return '|'.join(tags)
    return ''


def extract_nutrients(souped):
    '''
    Extract nutrient values from the recipe page.
    Strategy: 1) JSON-LD schema, 2) commented-out HTML nutrient section.
    Returns a dict with calories and nutrient_values (JSON string).
    '''
    nutrient_data = {
        'calories': '',
        'nutrient_values': ''
    }

    # Strategy 1: Parse JSON-LD for nutrition info
    scripts = souped.find_all('script', type='application/ld+json')
    for sc in scripts:
        if not sc.string:
            continue
        try:
            # Sanitize control characters that break json.loads
            # (user review text often contains raw newlines/tabs)
            clean_json = re.sub(r'[\x00-\x1f\x7f]', ' ', sc.string)
            data = json.loads(clean_json)
            if isinstance(data, dict) and data.get('@type') == 'Recipe':
                nutrition = data.get('nutrition', {})
                if nutrition:
                    nutrient_data['calories'] = nutrition.get('calories', '')
                    # Collect all nutrient fields except @type
                    nutrient_items = {k: v for k, v in nutrition.items() if k != '@type'}
                    nutrient_data['nutrient_values'] = json.dumps(nutrient_items) if nutrient_items else ''
                break
        except (json.JSONDecodeError, TypeError):
            pass

    # Strategy 2: Fallback — parse commented-out HTML nutrient section
    if not nutrient_data['calories']:
        comments = souped.find_all(string=lambda t: isinstance(t, Comment))
        for comment in comments:
            if 'nutrient' in comment.lower() or 'calori' in comment.lower() or 'energy' in comment.lower():
                comment_soup = soup(comment, 'html.parser')
                nutrient_list = comment_soup.find('ul', class_='list-of-recipe')
                if nutrient_list:
                    nutrient_items = {}
                    # Mapping of HTML label -> JSON key
                    label_map = {
                        'energy': 'calories',
                        'protien': 'proteinContent',  # sic - site typo
                        'protein': 'proteinContent',
                        'carbohydrates': 'carbohydrateContent',
                        'fiber': 'fiberContent',
                        'fat': 'fatContent',
                        'cholesterol': 'cholesterolContent',
                        'sodium': 'sodiumContent'
                    }
                    for li in nutrient_list.find_all('li'):
                        spans = li.find_all('span')
                        if len(spans) >= 2:
                            label = spans[0].get_text(strip=True).lower()
                            value = spans[1].get_text(strip=True)
                            key = label_map.get(label, label)
                            nutrient_items[key] = value
                    if nutrient_items:
                        nutrient_data['calories'] = nutrient_items.get('calories', '')
                        nutrient_data['nutrient_values'] = json.dumps(nutrient_items)
                break

    return nutrient_data


def get_recipe_details(recipe_name, recipe_url, scraper):
    '''
    Get all details from an individual recipe page:
    - Ingredients (list of dicts with quantity, unit, name, prep notes)
    - Time fields
    - Tags
    - Nutrient values
    '''
    logger.debug(f'get_recipe_details for: {recipe_name}')
    logger.debug(f'recipe_url: {recipe_url}')

    try:
        requrl = scraper.get(recipe_url)
        souped = soup(requrl.content, 'html.parser')
    except Exception as e:
        logger.error(f'Error fetching {recipe_url}: {e}')
        return []

    # Extract time fields, tags, and nutrients
    time_data = extract_time_fields(souped)
    tags = extract_tags(souped)
    nutrient_data = extract_nutrients(souped)

    # Extract ingredients from div.ingredients
    ingredients = []
    ing_div = souped.find('div', attrs={'class': 'ingredients'})
    if ing_div:
        for li in ing_div.find_all('li'):
            link = li.find('a')
            if not link:
                # No link - use full text as ingredient
                full_text = li.get_text(separator=' ', strip=True).replace(',', '').replace('"', '')
                ingredient_name = full_text
                quantity = ''
                measurement_unit = ''
                prep_notes = ''
            else:
                # Get ingredient name from the link/span
                ingredient_name = link.get_text(strip=True).replace(',', '').replace('"', '')

                # Get quantity text: everything before the link
                qty_parts = []
                for child in li.children:
                    if child == link:
                        break
                    if isinstance(child, NavigableString):
                        t = child.strip()
                        if t:
                            qty_parts.append(t)
                    else:
                        t = child.get_text(strip=True)
                        if t:
                            qty_parts.append(t)
                qty_text = ' '.join(qty_parts).replace(',', '').replace('"', '').strip()

                # Get trailing text (preparation notes like "to taste", "soaked overnight")
                trailing_parts = []
                found_link = False
                for child in li.children:
                    if child == link:
                        found_link = True
                        continue
                    if found_link:
                        if isinstance(child, NavigableString):
                            t = child.strip()
                            if t:
                                trailing_parts.append(t)
                        else:
                            t = child.get_text(strip=True)
                            if t:
                                trailing_parts.append(t)
                prep_notes = ' '.join(trailing_parts).replace(',', '').replace('"', '').strip()

                # Parse quantity and measurement unit from qty_text
                # e.g. "1 cup", "2 tbsp", "1/2 tsp finely", "1 1/2 cups", "a pinch of"
                quantity = ''
                measurement_unit = ''
                if qty_text:
                    parts = qty_text.split()
                    if parts and (parts[0][0].isdigit() or parts[0] in ('a', 'A')):
                        quantity = parts[0]
                        rest_idx = 1
                        # Handle compound fractions like "1 1/2" or "2 1/4"
                        if len(parts) > 1 and '/' in parts[1] and parts[1][0].isdigit():
                            quantity = f"{parts[0]} {parts[1]}"
                            rest_idx = 2
                        if len(parts) > rest_idx:
                            measurement_unit = ' '.join(parts[rest_idx:])
                    else:
                        # No numeric quantity, treat all as measurement descriptor
                        measurement_unit = qty_text

            # If prep_notes exist, append to ingredient for context
            if prep_notes:
                ingredient_name = f"{ingredient_name} ({prep_notes})"

            ingredients.append({
                'recipe_name': recipe_name,
                'quantity': quantity,
                'measurement_unit': measurement_unit,
                'ingredient': ingredient_name,
                'recipe_url': recipe_url,
                'soaking_time': time_data['soaking_time'],
                'preparation_time': time_data['preparation_time'],
                'cooking_time': time_data['cooking_time'],
                'baking_time': time_data['baking_time'],
                'baking_temperature': time_data['baking_temperature'],
                'sprouting_time': time_data['sprouting_time'],
                'total_time': time_data['total_time'],
                'makes': time_data['makes'],
                'tags': tags,
                'calories': nutrient_data['calories'],
                'nutrient_values': nutrient_data['nutrient_values']
            })

    # If no ingredients found via li parsing, add at least one record
    if not ingredients:
        ingredients.append({
            'recipe_name': recipe_name,
            'quantity': '',
            'measurement_unit': '',
            'ingredient': '',
            'recipe_url': recipe_url,
            'soaking_time': time_data['soaking_time'],
            'preparation_time': time_data['preparation_time'],
            'cooking_time': time_data['cooking_time'],
            'baking_time': time_data['baking_time'],
            'baking_temperature': time_data['baking_temperature'],
            'sprouting_time': time_data['sprouting_time'],
            'total_time': time_data['total_time'],
            'makes': time_data['makes'],
            'tags': tags,
            'calories': nutrient_data['calories'],
            'nutrient_values': nutrient_data['nutrient_values']
        })

    return ingredients


def get_recipes_list(base_url, output_file, url2skip, start_page=1, end_page=2, scrape_all=False):
    '''
    Get the list of recipes from listing pages with recursive pagination.

    Args:
        base_url: Base URL of tarladalal.com
        output_file: Path to output CSV file
        url2skip: Tuple of recipe URL slugs to skip
        start_page: Starting page number (default: 1)
        end_page: Ending page number (default: 2)
        scrape_all: If True, scrape all pages until no new recipes found
    '''
    listing_url = base_url + 'recipes-for-indian-veg-recipes-2?page='
    scraper = create_scraper()

    # CSV columns
    columns = [
        'recipe_name', 'quantity', 'measurement_unit', 'ingredient', 'recipe_url',
        'soaking_time', 'preparation_time', 'cooking_time', 'baking_time',
        'baking_temperature', 'sprouting_time', 'total_time', 'makes', 'tags',
        'calories', 'nutrient_values'
    ]

    all_records = []
    seen_urls = set()
    page = start_page
    consecutive_empty = 0

    if scrape_all:
        logger.info('Scraping ALL pages (will stop when no new recipes found)')
        pbar = tqdm(desc='Scraping pages', unit='page')
    else:
        logger.info(f'Scraping pages {start_page} to {end_page}')
        pbar = tqdm(total=(end_page - start_page + 1), desc='Scraping pages', unit='page')

    while True:
        # Check stop condition
        if not scrape_all and page > end_page:
            break
        if scrape_all and consecutive_empty >= 3:
            logger.info(f'Stopped at page {page}: 3 consecutive pages with no new recipes')
            break

        raw_url = listing_url + str(page)
        logger.debug(f'Fetching listing page: {raw_url}')

        try:
            opened_url = scraper.get(raw_url)
            souped_up = soup(opened_url.content, 'html.parser')
        except Exception as e:
            logger.error(f'Error fetching listing page {page}: {e}')
            page += 1
            pbar.update(1)
            continue

        # Get recipe links from this page
        recipe_titles = souped_up.find_all('div', attrs={'class': 'recipe-title'})
        new_recipes_on_page = 0

        for recipe_span in recipe_titles:
            span_children = recipe_span.findChildren('a', recursive=False)
            if not span_children:
                continue

            recipe_slug = span_children[0].get('href')
            indiv_recipe_url = base_url + recipe_slug.lstrip('/')
            indiv_recipe_name = span_children[0].get_text().replace(',', '').strip()

            # Skip if URL already processed or in skip list
            if indiv_recipe_url in seen_urls:
                continue
            if recipe_slug in url2skip:
                logger.debug(f'Skipping {indiv_recipe_url}')
                continue

            seen_urls.add(indiv_recipe_url)
            new_recipes_on_page += 1

            # Get full recipe details
            recipe_records = get_recipe_details(indiv_recipe_name, indiv_recipe_url, scraper)
            all_records.extend(recipe_records)

            # Rate limiting - be polite to the server
            time.sleep(0.5)

        if new_recipes_on_page == 0:
            consecutive_empty += 1
            logger.debug(f'Page {page}: no new recipes (consecutive empty: {consecutive_empty})')
        else:
            consecutive_empty = 0
            logger.debug(f'Page {page}: {new_recipes_on_page} new recipes')

        page += 1
        pbar.update(1)

        # Small delay between listing pages
        time.sleep(0.3)

    pbar.close()

    # Write to CSV
    logger.info(f'Writing {len(all_records)} ingredient records to {output_file}')
    df = pd.DataFrame(all_records, columns=columns)
    df.to_csv(output_file, index=False)

    print(f'\nTotal recipes scraped: {len(seen_urls)}')
    print(f'Total ingredient records: {len(all_records)}')
    print(f'Output: {output_file}')


def create_recipes_json(input_file, output_file):
    '''
    Create recipe/ingredient list JSON from CSV created earlier.
    Includes all new fields (nutrients, times, tags).
    '''
    logger.debug(f'create_recipes_json: {input_file} -> {output_file}')

    df = pd.read_csv(input_file)
    records = []

    for key, grp in df.groupby('recipe_name'):
        first_row = grp.iloc[0]
        recipe = {
            "Recipe": {
                "Name": key,
                "Url": first_row.recipe_url,
                "Ingredients": [
                    {
                        'Name': row.ingredient,
                        'Quantity': f"{row.quantity} {row.measurement_unit}".strip()
                    }
                    for row in grp.itertuples()
                ],
                "Times": {
                    "SoakingTime": str(first_row.soaking_time) if pd.notna(first_row.soaking_time) else '',
                    "PreparationTime": str(first_row.preparation_time) if pd.notna(first_row.preparation_time) else '',
                    "CookingTime": str(first_row.cooking_time) if pd.notna(first_row.cooking_time) else '',
                    "BakingTime": str(first_row.baking_time) if pd.notna(first_row.baking_time) else '',
                    "BakingTemperature": str(first_row.baking_temperature) if pd.notna(first_row.baking_temperature) else '',
                    "SproutingTime": str(first_row.sprouting_time) if pd.notna(first_row.sprouting_time) else '',
                    "TotalTime": str(first_row.total_time) if pd.notna(first_row.total_time) else ''
                },
                "Makes": str(first_row.makes) if pd.notna(first_row.makes) else '',
                "Tags": str(first_row.tags).split('|') if pd.notna(first_row.tags) and first_row.tags else [],
                "Calories": str(first_row.calories) if pd.notna(first_row.calories) else '',
                "NutrientValues": json.loads(first_row.nutrient_values) if pd.notna(first_row.nutrient_values) and first_row.nutrient_values else {}
            }
        }
        records.append(recipe)

    with open(output_file, 'w', encoding='utf-8') as out_file:
        out_file.write(json.dumps(records, indent=2))

    print(f'JSON output: {output_file} ({len(records)} recipes)')


if __name__ == '__main__':
    try:
        from datetime import datetime

        # Parse arguments
        parser = argparse.ArgumentParser(description='Scrape recipes from tarladalal.com')
        parser.add_argument('scrape', nargs='?', default='n',
                            help='y = scrape + create JSON, n = just create JSON from existing CSV')
        parser.add_argument('start_page', nargs='?', type=int, default=1,
                            help='Start page number (default: 1)')
        parser.add_argument('end_page', nargs='?', type=int, default=2,
                            help='End page number (default: 2)')
        parser.add_argument('--all', action='store_true',
                            help='Scrape ALL pages (overrides start/end page)')
        parser.add_argument('--csv', type=str, default=None,
                            help='Path to existing CSV file (for JSON-only mode with scrape=n)')
        args = parser.parse_args()

        url2skip = ()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')

        # Build descriptive filenames based on scrape mode
        if args.scrape == 'y':
            if args.all:
                scope = f'all_from_p{args.start_page}'
            else:
                scope = f'p{args.start_page}_to_{args.end_page}'
            csv_filename = f'recipes_{scope}_{timestamp}.csv'
            json_filename = f'recipes_{scope}_{timestamp}.json'
        else:
            # JSON-only mode: use provided CSV or fall back to most recent
            if args.csv:
                csv_filename = args.csv
            else:
                # Find the most recent recipes_*.csv in current directory
                import glob
                csv_files = sorted(glob.glob('recipes_*.csv'), reverse=True)
                if csv_files:
                    csv_filename = csv_files[0]
                else:
                    csv_filename = 'recipe_all.csv'  # legacy fallback
            json_filename = csv_filename.replace('.csv', '.json')

        # Logger settings
        logging.basicConfig(
            filename=r".\scrap_recipes.log",
            format="%(asctime)s [%(levelname)s] %(message)s",
            filemode="w",
            level=logging.DEBUG
        )
        logger = logging.getLogger('scrappy')

        logger.debug(f'Scrapping Started - scrape={args.scrape}, '
                      f'start_page={args.start_page}, end_page={args.end_page}, all={args.all}')

        if args.scrape == 'y':
            print(f'Scraping recipes from tarladalal.com...')
            if args.all:
                print(f'Mode: ALL pages (starting from page {args.start_page})')
            else:
                print(f'Mode: Pages {args.start_page} to {args.end_page}')

            get_recipes_list(
                'https://www.tarladalal.com/',
                csv_filename,
                url2skip,
                start_page=args.start_page,
                end_page=args.end_page,
                scrape_all=args.all
            )

        print(f'\nCreating JSON from {csv_filename}...')
        create_recipes_json(csv_filename, json_filename)

    except Exception as e:
        logging.error("An error occurred: %s", str(e), exc_info=True)
        print(f'Error: {e}')
        sys.exit(1)

