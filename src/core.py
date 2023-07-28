
import re
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup




def parse_html_as_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    return soup

def get_price_history(url: str) -> pd.DataFrame:
    soup = parse_html_as_soup(url)
    price_history = soup.find("div", {"class": "pricing-row-container"}).findAll("div", {"class": "price-row"})

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
    url = "https://items.jellyneo.net/item/2288/price-history/"
    get_price_history(url)
