import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import requests
import json
import os
from datetime import datetime

PHONE_EMAIL_PATTERN = re.compile(r"^(tel:|mailto:|\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9})|@")

def scrape_page(url, depth=0, visited=set()):
    if depth < 0 or url in visited:
        return {}

    visited.add(url)
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')

        # Extract title of the page
        title = soup.title.string if soup.title else "No Title"

        # Get structured content for sections and divs with 'ct-' classes
        sections_content = scrape_sections_content(soup)

        data = {
            "url": url,
            "title": title,
            "scraped_at": datetime.utcnow().isoformat() + "Z",
            "sections_content": sections_content
        }

        # Recursive scraping if depth > 0
        if depth > 0:
            for link in soup.find_all('a', href=True):
                full_url = urljoin(url, link['href'])

                # Skip links that match phone numbers or emails
                if PHONE_EMAIL_PATTERN.match(full_url):
                    print(f"Skipping phone or email link: {full_url}")
                    continue
                
                if is_internal_link(url, full_url):
                    data.update(scrape_page(full_url, depth - 1, visited))

        return data

    except requests.exceptions.RequestException as e:
        print(f"Error scraping {url}: {e}")
        return {"url": url, "sections_content": "No content available", "error": str(e)}


def scrape_sections_content(soup):
    """Extract structured content from each <section> or <div> with classes prefixed by 'ct-'."""
    sections_content = []

    # Loop through each section or div with classes starting with 'ct-'
    for section in soup.find_all(['section', 'div'], class_=lambda classes: classes and any(re.match(r'^ct-', cls) for cls in (classes if isinstance(classes, list) else [classes]))):
        section_data = {
            "headings": [],
            "content": [],  # Combined paragraphs and text blocks
            "links": []
        }

        # Capture main headings
        for heading in section.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], class_=lambda x: x and 'ct-headline' in x):
            section_data["headings"].append(heading.get_text(strip=True))

        # Capture text from <div> tags with 'ct-text-block' and paragraphs
        for text_block in section.find_all('div', class_=lambda x: x and 'ct-text-block' in x):
            section_data["content"].append(text_block.get_text(strip=True))
        for paragraph in section.find_all('p'):
            section_data["content"].append(paragraph.get_text(strip=True))
        
        # Capture links with anchor text and URL
        for link in section.find_all('a', href=True):
            link_text = link.get_text(strip=True)
            link_url = urljoin(section.base_url, link['href'])
            section_data["links"].append({"text": link_text, "url": link_url})
        
        # Add section data only if it contains meaningful content
        if any(section_data.values()):
            sections_content.append(section_data)

    return sections_content

def is_internal_link(base_url, link_url):
    """Check if a link is within the same site structure."""
    parsed_base = urlparse(base_url)
    parsed_link = urlparse(link_url)
    return parsed_link.netloc == "" or parsed_link.netloc == parsed_base.netloc

def save_to_json(data, url):
    """Save the scraped data to a JSON file with a filename based on the URL."""
    filename = url.replace("https://", "").replace("http://", "").replace("/", "_") + ".json"
    filepath = os.path.join("output", filename)

    # Ensure the output directory exists
    os.makedirs("output", exist_ok=True)

    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

    print(f"Saved data to {filepath}")

def scrape_website(url, depth=0):
    """Scrape the website, optionally following links up to a given depth."""
    scraped_data = scrape_page(url, depth)

    # Save the result to a JSON file
    save_to_json(scraped_data, url)
    
    return scraped_data
