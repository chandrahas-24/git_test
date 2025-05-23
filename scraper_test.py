import requests
from bs4 import BeautifulSoup
import os

def download_amazon_search_images(url, folder_name="amazon_search_images"):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    os.makedirs(folder_name, exist_ok=True)
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all product containers (usually 'div' with 's-result-item' and NOT 'AdHolder' or 'Sponsored')
    product_containers = soup.find_all('div', {'data-component-type': 's-search-result'})
    seen = set()
    idx = 1

    for container in product_containers:
        # Skip if the container contains a Sponsored label
        sponsored = container.find(string=lambda text: text and "Sponsored" in text)
        if sponsored:
            continue

        img = container.find('img', class_='s-image')
        if img:
            img_url = img.get('src')
            if not img_url or img_url in seen:
                continue
            seen.add(img_url)
            try:
                img_data = requests.get(img_url, headers=headers).content
                filename = os.path.join(folder_name, f" - {idx}.png")
                with open(filename, 'wb') as f:
                    f.write(img_data)
                print(f"Downloaded: {filename}")
                idx += 1
            except Exception as e:
                print(f"Failed to download {img_url}: {e}")

if __name__ == "__main__":
    url = input("Enter Amazon search results URL: ")
    download_amazon_search_images(url)
