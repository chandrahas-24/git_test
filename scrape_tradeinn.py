import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import time
from urllib.parse import urljoin, urlparse
import mimetypes
import re

def extract_product_data(file_path):
    try:
        df = pd.read_excel(file_path, usecols="C,D")
        products = df.dropna().values.tolist()
        return products
    except Exception as e:
        print(f"Error reading spreadsheet: {e}")
        return []

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '', name)

def find_product_image_links(soup):
    site_root = "https://www.tradeinn.com"
    product_imgs = []
    gallery = soup.find('div', class_='swiper-wrapper')
    if not gallery:
        return []
    img_tags = gallery.find_all('img')
    for img in img_tags:
        src = img.get('src') or img.get('data-src')
        if src and '/f/' in src and 'thumb' not in src.lower():
            if not src.startswith('http'):
                src = urljoin(site_root, src.lstrip('/'))
            if src not in product_imgs:
                product_imgs.append(src)
    return product_imgs

def download_product_images(url, product_name, output_folder='downloaded_images'):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        safe_name = sanitize_filename(str(product_name))
        product_folder = os.path.join(output_folder, safe_name)
        os.makedirs(product_folder, exist_ok=True)
        product_imgs = find_product_image_links(soup)
        if not product_imgs:
            print(f"  ⚠️  No product images found for {product_name}")
            return 0
        downloaded_count = 0
        for i, img_url in enumerate(product_imgs, 1):
            try:
                img_response = requests.get(img_url, headers=headers)
                img_response.raise_for_status()
                content_type = img_response.headers.get('Content-Type', '').lower()
                if not content_type.startswith('image/'):
                    print(f"  ❌ Skipped non-image: {img_url}")
                    continue
                parsed_url = urlparse(img_url)
                ext = os.path.splitext(parsed_url.path)[1]
                filename = f"{product_name} - {i}{ext}"
                safe_filename = sanitize_filename(filename)
                with open(os.path.join(product_folder, safe_filename), 'wb') as f:
                    f.write(img_response.content)
                downloaded_count += 1
                print(f"  ✅ Saved: {safe_filename}")
            except Exception as img_error:
                print(f"  ❌ Failed to download {img_url}: {img_error}")
        return downloaded_count
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return 0

def run_scraper(spreadsheet_path):
    products = extract_product_data(spreadsheet_path)
    if not products:
        print("No valid product data found in spreadsheet")
        return
    print(f"Found {len(products)} products")
    total_images = 0
    for idx, (url, product_name) in enumerate(products, 1):
        print(f"\nProcessing {idx}/{len(products)}: {product_name}")
        count = download_product_images(url, product_name)
        total_images += count
        print(f"Downloaded {count} images")
        time.sleep(0.5)
    print(f"\n✅ Completed! Downloaded {total_images} total images")

if __name__ == "__main__":
    run_scraper("Buscar_Imagens.xlsx")  # Replace with your file
