import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from openpyxl import load_workbook


def get_event_links(page_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(page_url, headers=headers)
    event_links = []
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        event_name_divs = soup.find_all('div', string="Event name")
        for div in event_name_divs:
            strong_tag = div.find_next('strong')
            if strong_tag:
                a_tag = strong_tag.find('a')
                if a_tag and 'href' in a_tag.attrs:
                    link = a_tag['href']
                    event_links.append(link)
    else:
        print(f"Failed to retrieve event links from {page_url}, status code: {response.status_code}")
    return event_links


def get_event_title(link):
    base_url = "https://www.ted.com"
    full_url = base_url + link
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session = requests.Session()
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        print(f"Fetching event page: {full_url}")
        event_response = session.get(full_url, headers=headers, timeout=10)
        print(f"Status code: {event_response.status_code}")
        if event_response.status_code == 200:
            event_soup = BeautifulSoup(event_response.content, 'html.parser')
            h1_tag = event_soup.find('h1', class_='h2 m1')
            if h1_tag:
                title = h1_tag.get_text(strip=True)
                if title.startswith('Theme:'):
                    title = title.replace('Theme:', '').strip()
                return title
        else:
            print(f"Failed to retrieve the webpage for {full_url}, status code: {event_response.status_code}")
            if event_response.status_code == 429:
                time.sleep(10)  
                return get_event_title(link) 
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving {full_url}: {e}")

    return None


def main():
    
    base_url_template = "https://www.ted.com/tedx/events?page={}&when=past"
    total_pages = 10  

    event_titles = []

    for page in range(1, total_pages + 1):
        page_url = base_url_template.format(page)
        event_links = get_event_links(page_url)

        for link in event_links:
            title = get_event_title(link)
            if title:
                event_titles.append(title)
                
                df = pd.DataFrame([title], columns=["Event Title"])
                try:
                    try:
                        df_existing = pd.read_excel("eventtitles.xlsx")
                    except FileNotFoundError:
                        df_existing = pd.DataFrame(columns=["Event Title"])

                    df_combined = pd.concat([df_existing, df], ignore_index=True)

                    df_combined.to_excel("eventtitles.xlsx", index=False)
                except Exception as e:
                    print(f"Failed to append title to Excel: {e}")

    print("Event titles appended to eventtitles.xlsx")

if __name__ == "__main__":
    main()
