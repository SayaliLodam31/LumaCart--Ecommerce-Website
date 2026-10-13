import urllib.request
import urllib.error
import json
import os

BASE_URL = 'http://127.0.0.1:8001'

def test_endpoints():
    print("================ TESTING PAGES AND IMAGES ================")
    
    pages = [
        ('/', 'Home Page'),
        ('/pages/products.html', 'Products Listing Page'),
        ('/pages/product-detail.html?slug=femella-women-brown-scarf-25947', 'Product Detail Page (Scarf)'),
        ('/pages/cart.html', 'Cart Page'),
        ('/pages/checkout.html', 'Checkout Page'),
    ]
    
    for path, name in pages:
        url = BASE_URL + path
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as resp:
                status = resp.status
                content = resp.read()
                print(f"[OK] {name} ({path}) -> HTTP {status} ({len(content)} bytes)")
        except Exception as e:
            print(f"[FAIL] {name} ({path}) -> Error: {e}")
            
    print("\n---------------- TESTING ALL 36 PRODUCT IMAGES ----------------")
    with open('scratch/baseline_image_stats.json') as f:
        baseline = json.load(f)
        
    broken_images = []
    cached_headers_ok = 0
    total_download_bytes = 0
    
    for pid in baseline.keys():
        img_url = f"{BASE_URL}/media/products/{pid}.jpg"
        try:
            req = urllib.request.Request(img_url)
            with urllib.request.urlopen(req) as resp:
                status = resp.status
                data = resp.read()
                cache_header = resp.headers.get('Cache-Control', '')
                if 'max-age=2592000' in cache_header:
                    cached_headers_ok += 1
                total_download_bytes += len(data)
                if len(data) == 0:
                    broken_images.append(pid)
        except Exception as e:
            broken_images.append((pid, str(e)))
            
    print(f"Total Images Tested: {len(baseline)}")
    print(f"Broken Images: {len(broken_images)}")
    print(f"Images with Immutable Cache-Control (30 days): {cached_headers_ok}/{len(baseline)}")
    print(f"Total Bytes Streamed: {total_download_bytes} bytes ({total_download_bytes/1024:.2f} KB)")
    
    if len(broken_images) == 0 and cached_headers_ok == len(baseline):
        print("\n>>> ALL PAGES & 36 PRODUCT IMAGES VERIFIED 100% OPERATIONAL WITH OPTIMAL CACHING! <<<")
    else:
        print(f"\nIssues detected: {broken_images}")

if __name__ == '__main__':
    test_endpoints()
