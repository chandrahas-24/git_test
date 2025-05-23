import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import time
from urllib.parse import urljoin, urlparse
import mimetypes
import re


def extract_product_data(file_path):
    """
    Extract product links and names from spreadsheet using Excel columns C (link) and D (name)
    """
    try:
        df = pd.read_excel(file_path, usecols="C,D")
        products = df.dropna().values.tolist()
        return products
    except Exception as e:
        print(f"Error reading spreadsheet: {e}")
        return []


def sanitize_filename(name):
    # Remove forbidden characters, keep spaces and dash
    return re.sub(r'[\\/*?:"<>|]', '', name)


def find_product_image_links(soup):
    """
    Find all product image links while ignoring thumbnails
    Constructs absolute URLs using the site root domain
    """
    site_root = "https://www.fairwaygolfusa.com"
    product_imgs = set()

    # Check img tags (src and data-src)
    for img in soup.find_all('img'):
        for attr in ['src', 'data-src']:
            src = img.get(attr)
            if src and 'resources/upload/products/' in src:
                src_lower = src.lower()
                if 'thumbnail' not in src_lower and 'thumb' not in src_lower:
                    # Construct correct absolute URL
                    if src.startswith('http'):
                        full_url = src
                    else:
                        # Remove leading slash if present to avoid double slashes
                        full_url = urljoin(site_root, src.lstrip('/'))
                    product_imgs.add(full_url)

    # Check a tags (href)
    for a in soup.find_all('a'):
        href = a.get('href')
        if href and 'resources/upload/products/' in href:
            href_lower = href.lower()
            if 'thumbnail' not in href_lower and 'thumb' not in href_lower:
                if href.startswith('http'):
                    full_url = href
                else:
                    full_url = urljoin(site_root, href.lstrip('/'))
                product_imgs.add(full_url)

    return list(product_imgs)


def download_product_images(url, product_name, output_folder='downloaded_images'):
    """
    Download only non-thumbnail product images in their original format
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Create safe folder
        safe_name = sanitize_filename(str(product_name))
        product_folder = os.path.join(output_folder, safe_name)
        os.makedirs(product_folder, exist_ok=True)

        # Find product images
        product_imgs = find_product_image_links(soup)

        if not product_imgs:
            print(f"  ⚠️  No product images found for {product_name}")
            return 0

        downloaded_count = 0
        for i, img_url in enumerate(product_imgs, 1):
            try:
                print(f"  Downloading: {img_url}")
                img_response = requests.get(img_url, headers=headers)
                img_response.raise_for_status()

                # Verify image content
                content_type = img_response.headers.get('Content-Type', '').lower()
                if not content_type.startswith('image/'):
                    print(f"  ❌ Skipped non-image: {img_url}")
                    continue

                # Get correct extension
                parsed_url = urlparse(img_url)
                ext = os.path.splitext(parsed_url.path)[1]
                if not ext:
                    ext = mimetypes.guess_extension(content_type.split(';')[0]) or '.jpg'

                # Create filename
                filename = f"{product_name} - {i}{ext}"
                safe_filename = sanitize_filename(filename)

                # Save file
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
    """
    Main execution function
    """
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
        time.sleep(0.5)  # Delay to avoid rate limiting

    print(f"\n✅ Completed! Downloaded {total_images} total images")


# Usage example:
if __name__ == "__main__":
    run_scraper("Buscar_Imagens.xlsx")  # Replace with actual file path