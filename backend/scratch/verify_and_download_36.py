import json
import requests
from pathlib import Path
from PIL import Image
import io

selected_36 = [
    # 1. Women's Clothing (6)
    {'id': 39716, 'category': 'womens-clothing', 'desc_override': 'Elevated navy blue tailored dress with architectural seam lines, crafted from structured stretch crepe.'},
    {'id': 49653, 'category': 'womens-clothing', 'desc_override': 'Contemporary green draped silhouette top with a fluid hemline, cut from lightweight breathable viscose.'},
    {'id': 26960, 'category': 'womens-clothing', 'desc_override': 'Crisp collared woven shirt in a rich amethyst hue, finished with mother-of-pearl buttons and tailored cuffs.'},
    {'id': 20099, 'category': 'womens-clothing', 'desc_override': 'Artisanal bottle-green embroidered tunic kurta featuring handcrafted threadwork and a relaxed luxury fit.'},
    {'id': 26994, 'category': 'womens-clothing', 'desc_override': 'Mid-rise classic slim jeans in deep obsidian black, woven with authentic denim twill and subtle stretch comfort.'},
    {'id': 2288,  'category': 'womens-clothing', 'desc_override': 'Signature minimal black knit performance tee with breathable cotton-jersey finish and clean tonal seams.'},

    # 2. Men's Clothing (6)
    {'id': 15970, 'category': 'mens-clothing', 'desc_override': 'Tailored navy blue check button-down shirt woven from 100% long-staple Egyptian cotton.'},
    {'id': 39386, 'category': 'mens-clothing', 'desc_override': 'Authentic blue wash selvedge-inspired five-pocket denim jeans with precision-stitched bar tacks.'},
    {'id': 13089, 'category': 'mens-clothing', 'desc_override': 'Athletic heather-grey hooded sweatshirt with soft brushed-fleece interior and double-needle ribbed trims.'},
    {'id': 53759, 'category': 'mens-clothing', 'desc_override': 'Premium athletic crewneck tee in heather grey, engineered with moisture-wicking and ultra-soft cotton hand-feel.'},
    {'id': 30805, 'category': 'mens-clothing', 'desc_override': 'Handwoven textured forest green striped shirt crafted from pure organic breathable cotton.'},
    {'id': 7990,  'category': 'mens-clothing', 'desc_override': 'Sport heritage crewneck t-shirt in deep navy blue, finished with a reinforced rib collar and classic fit.'},

    # 3. Shoes (6)
    {'id': 9036,  'category': 'shoes', 'desc_override': 'Handcrafted derby formal shoes in rich full-grain black calfskin leather with Goodyear-welted soles.'},
    {'id': 9204,  'category': 'shoes', 'desc_override': 'Low-profile motorsports-inspired casual leather sneakers with contoured aerodynamic silhouette and rubber cupsole.'},
    {'id': 3168,  'category': 'shoes', 'desc_override': 'Lightweight road performance athletic sneakers featuring responsive foam cushioning and breathable engineered mesh upper.'},
    {'id': 59051, 'category': 'shoes', 'desc_override': 'Pointed-toe slingback flats in polished jet-black leather accented with delicate brushed champagne-gold trims.'},
    {'id': 2886,  'category': 'shoes', 'desc_override': 'Artisanal cognac-brown handcrafted leather slide flats with cushioned leather footbed and flexible sole.'},
    {'id': 39988, 'category': 'shoes', 'desc_override': 'Clean minimalist court sneakers in crisp chalk-white leather with tonal stitch detailing and vulcanized outsoles.'},

    # 4. Bags (6)
    {'id': 47957, 'category': 'bags', 'desc_override': 'Architectural structured top-handle handbag in cobalt blue textured leather with brushed metallic hardware.'},
    {'id': 47359, 'category': 'bags', 'desc_override': 'Timeless saddle-brown structured leather shoulder tote featuring dual handles and a spacious compartmentalized interior.'},
    {'id': 58183, 'category': 'bags', 'desc_override': 'Modern ivory top-handle satchel with clean minimalist silhouette, removable crossbody strap, and magnetic flap closure.'},
    {'id': 20851, 'category': 'bags', 'desc_override': 'Artisanal structured occasion clutch in scarlet red featuring delicate botanical ribbon embroidery and satin lining.'},
    {'id': 39524, 'category': 'bags', 'desc_override': 'Padded urban tech folio sleeve in high-visibility heritage orange with waterproof zippers and fleece-lined laptop sleeve.'},
    {'id': 12732, 'category': 'bags', 'desc_override': 'Everyday multi-compartment commuter backpack in dense matte black canvas with ergonomic padded shoulder straps.'},

    # 5. Jewellery (6)
    {'id': 48781, 'category': 'jewellery', 'desc_override': 'Solid 925 sterling silver sculpted pendant suspended from a delicate diamond-cut cable chain.'},
    {'id': 49005, 'category': 'jewellery', 'desc_override': 'Minimalist comfort-fit band ring cast in fine sterling silver with a softly burnished satin finish.'},
    {'id': 35322, 'category': 'jewellery', 'desc_override': 'Filigree drop earrings hand-cast in pure oxidised sterling silver with traditional lotus motif detailing.'},
    {'id': 56214, 'category': 'jewellery', 'desc_override': 'Polished 18K yellow gold plated sculptural huggie hoop earrings designed for effortless daily elegance.'},
    {'id': 48311, 'category': 'jewellery', 'desc_override': 'Multi-strand artisanal beaded cuff bracelet combining faceted bronze beads and hand-tied metallic cord.'},
    {'id': 52224, 'category': 'jewellery', 'desc_override': 'Graduated silver pearl strand necklace featuring lustrous Swarovski simulated pearls and sterling silver filigree clasp.'},

    # 6. Accessories (6)
    {'id': 25947, 'category': 'accessories', 'desc_override': 'Ultra-soft woven autumn scarf in rich espresso brown, designed with delicately fringed hems and generous drape.'},
    {'id': 16957, 'category': 'accessories', 'desc_override': 'Polarised classic square sunglasses with handcrafted matte black acetate frames and 100% UV400 protective lenses.'},
    {'id': 59263, 'category': 'accessories', 'desc_override': 'Sculptural stainless-steel timepiece featuring a sunray silver dial, faceted bezel, and solid link bracelet.'},
    {'id': 17429, 'category': 'accessories', 'desc_override': 'Shock-resistant tactical digital watch in stealth matte black with world time, stopwatch, and 200m water resistance.'},
    {'id': 48123, 'category': 'accessories', 'desc_override': 'Hand-braided huarache leather waist belt in midnight black, finished with an antique brass roller buckle.'},
    {'id': 18839, 'category': 'accessories', 'desc_override': 'Sleek dress belt crafted from smooth full-grain black bridle leather with a polished nickel prong buckle.'},
]

def verify_all():
    print(f"Total products to verify: {len(selected_36)}")
    id_map = {item['id']: item for item in selected_36}
    
    # We will search the dataset rows for these 36 IDs
    found = {}
    url_base = 'https://datasets-server.huggingface.co/rows?dataset=benitomartin%2Ffashion-product-images-small-384x512&config=default&split=train'

    for offset in [0, 100, 200, 300, 400, 500]:
        if len(found) == len(selected_36):
            break
        print(f"Searching offset {offset}...")
        r = requests.get(f"{url_base}&offset={offset}&limit=100", timeout=20)
        if r.status_code != 200:
            continue
        for row_item in r.json().get('rows', []):
            row = row_item['row']
            pid = row['id']
            if pid in id_map:
                found[pid] = {
                    'dataset_id': pid,
                    'name': row.get('productDisplayName'),
                    'masterCategory': row.get('masterCategory'),
                    'subCategory': row.get('subCategory'),
                    'articleType': row.get('articleType'),
                    'gender': row.get('gender'),
                    'baseColour': row.get('baseColour'),
                    'season': row.get('season'),
                    'usage': row.get('usage'),
                    'image_src': row.get('image', {}).get('src'),
                    'category': id_map[pid]['category'],
                    'desc_override': id_map[pid]['desc_override']
                }

    print(f"Found in dataset: {len(found)} / {len(selected_36)}")
    missing = set(id_map.keys()) - set(found.keys())
    if missing:
        print(f"Missing IDs: {missing}")
        return

    # Check images
    media_dir = Path("media/products")
    media_dir.mkdir(parents=True, exist_ok=True)

    verified_data = []

    for item in selected_36:
        info = found[item['id']]
        img_url = info['image_src']
        print(f"Downloading [{info['dataset_id']}] {info['name']}...")
        r_img = requests.get(img_url, timeout=15)
        if r_img.status_code != 200 or len(r_img.content) == 0:
            raise RuntimeError(f"Failed to download image for {info['dataset_id']}")
        
        # Verify valid image
        im = Image.open(io.BytesIO(r_img.content))
        im.verify()
        
        local_path = media_dir / f"{info['dataset_id']}.jpg"
        with open(local_path, "wb") as f:
            f.write(r_img.content)

        info['local_image'] = f"products/{info['dataset_id']}.jpg"
        info['image_size'] = len(r_img.content)
        info['dimensions'] = f"{im.size[0]}x{im.size[1]}" if hasattr(im, 'size') else "384x512"
        verified_data.append(info)

    with open("verified_36_catalog.json", "w", encoding="utf-8") as f:
        json.dump(verified_data, f, indent=2)

    print("Successfully verified and downloaded all 36 product images!")

if __name__ == '__main__':
    verify_all()
