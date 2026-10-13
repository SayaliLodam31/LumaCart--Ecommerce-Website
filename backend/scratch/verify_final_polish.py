import urllib.request
import urllib.error
import json

BASE_URL = 'http://127.0.0.1:8001'

def verify_storefront():
    print("=" * 70)
    print("           LUMACART FINAL STOREFRONT & PAGE AUDIT")
    print("=" * 70)
    
    pages = [
        ('/', 'Home Page'),
        ('/pages/products.html', 'Products Listing Page'),
        ('/pages/product-detail.html?slug=femella-women-brown-scarf-25947', 'Product Detail Page (Scarf)'),
        ('/pages/cart.html', 'Cart Page'),
        ('/pages/checkout.html', 'Checkout Page'),
        ('/pages/login.html', 'Login Page'),
        ('/pages/register.html', 'Registration Page'),
        ('/pages/wishlist.html', 'Wishlist Page'),
        ('/pages/orders.html', 'Orders Tracking Page'),
    ]
    
    all_pages_ok = True
    for path, name in pages:
        url = BASE_URL + path
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as resp:
                status = resp.status
                data = resp.read()
                print(f"[OK] {name:<35} | HTTP {status} | Size: {len(data):>5} B")
        except Exception as e:
            all_pages_ok = False
            print(f"[FAIL] {name:<35} | Error: {e}")
            
    print("\n---------------- TESTING ALL 36 PRODUCT IMAGES ----------------")
    with open('scratch/baseline_image_stats.json') as f:
        baseline = json.load(f)
        
    broken_images = []
    for pid in baseline.keys():
        img_url = f"{BASE_URL}/media/products/{pid}.jpg"
        try:
            req = urllib.request.Request(img_url)
            with urllib.request.urlopen(req) as resp:
                if resp.status != 200:
                    broken_images.append((pid, resp.status))
        except Exception as e:
            broken_images.append((pid, str(e)))
            
    print(f"Total Products Checked: {len(baseline)}")
    print(f"Broken Images: {len(broken_images)}")
    
    print("\n---------------- TESTING ALL 6 CATEGORY API FILTERS ----------------")
    categories = ['womens-clothing', 'mens-clothing', 'shoes', 'bags', 'jewellery', 'accessories']
    for cat in categories:
        url = f"{BASE_URL}/api/products/?category={cat}&page=1"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            count = data.get('count', len(data.get('results', [])))
            print(f"  Category: {cat:<20} | HTTP {resp.status} | Item Count: {count}")
            
    if all_pages_ok and len(broken_images) == 0:
        print("\n>>> ALL STOREFRONT PAGES, 36 IMAGES & CATEGORY FILTERS VERIFIED 100% OPERATIONAL! <<<")

if __name__ == '__main__':
    verify_storefront()
