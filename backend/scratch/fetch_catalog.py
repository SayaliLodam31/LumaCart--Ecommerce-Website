import requests
import json
from pathlib import Path

def fetch_and_select():
    url_base = 'https://datasets-server.huggingface.co/rows?dataset=benitomartin%2Ffashion-product-images-small-384x512&config=default&split=train'

    categories = {
        'womens_clothing': [],
        'mens_clothing': [],
        'shoes': [],
        'bags': [],
        'jewellery': [],
        'accessories': [],
    }

    seen_ids = set()

    for offset in [0, 100, 200, 300, 400]:
        print(f"Fetching offset {offset}...")
        try:
            r = requests.get(f"{url_base}&offset={offset}&limit=100", timeout=20)
            if r.status_code != 200:
                print(f"Failed at offset {offset}: {r.status_code}")
                continue
            rows = r.json().get('rows', [])
            for row_item in rows:
                row = row_item['row']
                pid = row['id']
                if pid in seen_ids:
                    continue

                name = row.get('productDisplayName')
                master = row.get('masterCategory')
                sub = row.get('subCategory')
                atype = row.get('articleType')
                gender = row.get('gender')
                colour = row.get('baseColour')
                season = row.get('season')
                usage = row.get('usage')
                img_src = row.get('image', {}).get('src') if isinstance(row.get('image'), dict) else None

                if not img_src or not name or not name.strip():
                    continue

                item = {
                    'id': pid,
                    'name': name.strip(),
                    'gender': gender,
                    'masterCategory': master,
                    'subCategory': sub,
                    'articleType': atype,
                    'baseColour': colour,
                    'season': season,
                    'usage': usage,
                    'image_url': img_src
                }

                # 1. Women's Clothing
                if master == 'Apparel' and gender == 'Women' and atype in ['Tops', 'Dresses', 'Shirts', 'Tshirts', 'Kurtas', 'Skirts', 'Jeans']:
                    if len(categories['womens_clothing']) < 12:
                        seen_ids.add(pid)
                        categories['womens_clothing'].append(item)
                        continue

                # 2. Men's Clothing
                if master == 'Apparel' and gender == 'Men' and atype in ['Shirts', 'Tshirts', 'Jeans', 'Trousers', 'Sweatshirts', 'Jackets']:
                    if len(categories['mens_clothing']) < 12:
                        seen_ids.add(pid)
                        categories['mens_clothing'].append(item)
                        continue

                # 3. Shoes
                if master == 'Footwear' and sub == 'Shoes' and atype in ['Casual Shoes', 'Sports Shoes', 'Formal Shoes', 'Flats', 'Heels']:
                    if len(categories['shoes']) < 12:
                        seen_ids.add(pid)
                        categories['shoes'].append(item)
                        continue

                # 4. Bags
                if sub == 'Bags' and atype in ['Handbags', 'Backpacks', 'Clutches', 'Wallets', 'Laptop Bag']:
                    if len(categories['bags']) < 12:
                        seen_ids.add(pid)
                        categories['bags'].append(item)
                        continue

                # 5. Jewellery
                if sub == 'Jewellery' and atype in ['Pendant', 'Earrings', 'Necklace and Chains', 'Ring', 'Bangle', 'Bracelet', 'Jewellery Set']:
                    if len(categories['jewellery']) < 12:
                        seen_ids.add(pid)
                        categories['jewellery'].append(item)
                        continue

                # 6. Accessories (Make sure Scarf is prioritized!)
                if master == 'Accessories' and sub not in ['Bags', 'Jewellery', 'Socks'] and atype in ['Scarves', 'Watches', 'Sunglasses', 'Belts', 'Ties', 'Caps']:
                    if len(categories['accessories']) < 12:
                        seen_ids.add(pid)
                        categories['accessories'].append(item)
                        continue
        except Exception as e:
            print(f"Error at offset {offset}: {e}")

    out_file = Path("selected_catalog_candidates.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(categories, f, indent=2)

    print("\nSummary of candidates:")
    for cat, items in categories.items():
        print(f"--- {cat}: {len(items)} items ---")
        for it in items[:6]:
            print(f"  [{it['id']}] {it['name']} ({it['articleType']}, {it['gender']}, {it['baseColour']})")

if __name__ == '__main__':
    fetch_and_select()
