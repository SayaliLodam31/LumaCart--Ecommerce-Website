import urllib.request
import urllib.error
import time
import json
from PIL import Image
import os

BASE_URL = 'http://127.0.0.1:8001'

def measure_request(url, headers=None):
    if headers is None:
        headers = {}
    req = urllib.request.Request(url, headers=headers)
    t0 = time.perf_counter()
    try:
        resp = urllib.request.urlopen(req)
        t_resp = time.perf_counter()
        data = resp.read()
        t_done = time.perf_counter()
        ttfb = (t_resp - t0) * 1000
        total_time = (t_done - t0) * 1000
        return {
            'status': resp.status,
            'ttfb_ms': round(ttfb, 2),
            'total_ms': round(total_time, 2),
            'size_bytes': len(data),
            'headers': dict(resp.headers)
        }
    except urllib.error.HTTPError as e:
        t_resp = time.perf_counter()
        data = e.read()
        t_done = time.perf_counter()
        return {
            'status': e.code,
            'ttfb_ms': round((t_resp - t0) * 1000, 2),
            'total_ms': round((t_done - t0) * 1000, 2),
            'size_bytes': len(data),
            'headers': dict(e.headers)
        }

def run_diagnostics():
    print("=" * 80)
    print("           LUMACART NETWORK & IMAGE LOADING DIAGNOSTIC")
    print("=" * 80)

    # 1. Measure API calls
    print("\n[1] MEASURING PRODUCT API ENDPOINTS (Database query + JSON serialization):")
    api_endpoints = [
        '/api/products/?page=1',
        '/api/products/?category=womens-clothing&page=1',
        '/api/products/femella-women-brown-scarf-25947/',
        '/api/products/featured/',
        '/api/products/new_arrivals/'
    ]
    api_timings = []
    for ep in api_endpoints:
        res = measure_request(BASE_URL + ep)
        api_timings.append((ep, res['status'], res['ttfb_ms'], res['total_ms'], res['size_bytes']))
        print(f"  {ep:<55} | HTTP {res['status']} | TTFB: {res['ttfb_ms']:>6.1f} ms | Total: {res['total_ms']:>6.1f} ms | Size: {res['size_bytes']:>5} B")

    # 2. Measure Image files
    print("\n[2] MEASURING PRODUCT IMAGE HTTP DELIVERY (First Request - Direct from server):")
    # Sample files requested by user plus actual catalog images
    image_paths = [
        '/media/products/2288.jpg',
        '/media/products/2886.jpg',
        '/media/products/3168.jpg',
        '/media/products/7990.jpg',
        '/media/products/1.jpg',
        '/media/products/2.jpg',
        '/media/products/3.jpg'
    ]
    for ip in image_paths:
        res = measure_request(BASE_URL + ip)
        cc = res['headers'].get('cache-control', res['headers'].get('Cache-Control', 'None'))
        
        # Check image dimensions if file exists on disk
        local_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ip.lstrip('/'))
        dims = "N/A"
        if os.path.exists(local_path):
            try:
                with Image.open(local_path) as im:
                    dims = f"{im.width}x{im.height}"
            except Exception:
                pass

        print(f"  {ip:<28} | HTTP {res['status']} | TTFB: {res['ttfb_ms']:>5.1f} ms | Total: {res['total_ms']:>5.1f} ms | Size: {res['size_bytes']:>6} B | Dims: {dims:<7} | Cache-Control: {cc}")

    # 3. Repeated Image Requests (Browser Cache simulation & Conditional GET)
    print("\n[3] MEASURING REPEATED REQUESTS (Simulating browser cache & revalidation):")
    for ip in ['/media/products/2288.jpg', '/media/products/2886.jpg', '/media/products/3168.jpg']:
        # First regular request
        r1 = measure_request(BASE_URL + ip)
        last_mod = r1['headers'].get('last-modified', r1['headers'].get('Last-Modified', ''))
        
        # Second request with If-Modified-Since
        headers = {'If-Modified-Since': last_mod} if last_mod else {}
        r2 = measure_request(BASE_URL + ip, headers=headers)
        
        print(f"  {ip:<28} | Request 1 (Full): HTTP {r1['status']} in {r1['total_ms']:>5.1f} ms ({r1['size_bytes']} B)")
        print(f"  {'':<28} | Request 2 (304) : HTTP {r2['status']} in {r2['total_ms']:>5.1f} ms ({r2['size_bytes']} B)")

    # 4. Measure Page HTML downloads
    print("\n[4] MEASURING PAGE HTML DELIVERIES:")
    pages = [
        ('/', 'Home (/)'),
        ('/pages/products.html', 'Products (/pages/products.html)'),
        ('/pages/product-detail.html?slug=femella-women-brown-scarf-25947', 'Detail (/pages/product-detail.html)'),
    ]
    for p, name in pages:
        res = measure_request(BASE_URL + p)
        print(f"  {name:<40} | HTTP {res['status']} | TTFB: {res['ttfb_ms']:>5.1f} ms | Total: {res['total_ms']:>5.1f} ms | Size: {res['size_bytes']:>6} B")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    run_diagnostics()
