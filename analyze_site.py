"""Find total page count"""
import cloudscraper
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})

# Binary search for last page
low, high = 200, 500
# First check if 500 has recipes
r = scraper.get(f'https://www.tarladalal.com/recipes-for-indian-veg-recipes-2?page=500')
s = BeautifulSoup(r.text, 'html.parser')
recs = s.find_all('div', attrs={'class': 'recipe-title'})
print(f"Page 500: {len(recs)} recipes")

if len(recs) > 0:
    # Try higher
    for p in [1000, 1500, 2000]:
        r = scraper.get(f'https://www.tarladalal.com/recipes-for-indian-veg-recipes-2?page={p}')
        s = BeautifulSoup(r.text, 'html.parser')
        recs = s.find_all('div', attrs={'class': 'recipe-title'})
        print(f"Page {p}: {len(recs)} recipes")
        if len(recs) == 0:
            high = p
            low = p - 500
            break
else:
    high = 500

# Binary search
while low < high - 1:
    mid = (low + high) // 2
    r = scraper.get(f'https://www.tarladalal.com/recipes-for-indian-veg-recipes-2?page={mid}')
    s = BeautifulSoup(r.text, 'html.parser')
    recs = s.find_all('div', attrs={'class': 'recipe-title'})
    print(f"Page {mid}: {len(recs)} recipes")
    if len(recs) > 0:
        low = mid
    else:
        high = mid

print(f"\nApproximate last page with recipes: {low}")
print(f"Approximate total recipes: {low * 20}")
