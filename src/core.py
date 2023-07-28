
import re
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from tenacity import retry
from tenacity.retry import retry_if_exception_type
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_random


from const import MAX_RETRIES, MAX_WAIT_BETWEEN_REQ, MIN_WAIT_BETWEEN_REQ, IDB_URL_TEMPLATE

@retry(
        wait=wait_random(min=MIN_WAIT_BETWEEN_REQ, max=MAX_WAIT_BETWEEN_REQ),
        stop=stop_after_attempt(MAX_RETRIES),
        retry=retry_if_exception_type(RequestException),        
)

def parse_html_as_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    return soup

def get_item_name(item_soup: BeautifulSoup) -> str:
    return item_soup.find("h1").text

def get_price_history(item_soup: BeautifulSoup) -> pd.DataFrame:
    price_history = item_soup.find("div", {"class": "pricing-row-container"}).findAll("div", {"class": "price-row"})

    price_history_entries = {
        "date": [],
        "price": [],
    }
    for entry in price_history:
        try:
            date = entry.find("span", {"class": "price-date"}).text
            date = re.findall("[A-Za-z]+ \d+, \d+", date)[0]
            date = datetime.strptime(date, "%B %d, %Y")

            price = re.findall("\d{1,3}(?:,\d{3})* (?=NP)", entry.text)[0]
            price = int(re.sub(",", "", price)) / 1000
            
            price_history_entries["date"].append(date)
            price_history_entries["price"].append(price)
        except IndexError:
            continue 
        
    price_history_df = pd.DataFrame().from_dict(price_history_entries)
    print(price_history_df)

if __name__ == "__main__":
    while True:
        item_id = input("Enter Neopets item ID:")
        try:
            item_id = int(item_id)
            break
        except ValueError:
            print("Invalid: ID must be an integer")
    item_url = IDB_URL_TEMPLATE.format(item_id=item_id)
    item_soup = parse_html_as_soup(item_url)

