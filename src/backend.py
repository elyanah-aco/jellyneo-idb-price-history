
from __future__ import annotations

import re
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, HTTPError
from tenacity import retry
from tenacity.retry import retry_if_exception_type
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_random

from const import MAX_RETRIES, MAX_WAIT_BETWEEN_REQ, MIN_WAIT_BETWEEN_REQ, IDB_URL_TEMPLATE
from errors import MissingPriceHistoryException

class JellyneoIDBCrawler:
    """
    Implements methods to obtain item data from Jellyneo's Item Database.
    """
    def send_request(self) -> BeautifulSoup:
        while True:
            try:
                item_id = input("Enter Neopets item ID:")
                item_id = int(item_id)
                item_url = IDB_URL_TEMPLATE.format(item_id=item_id)
                item_soup = self.parse_html_as_soup(item_url)
                return item_soup
            except ValueError:
                print("Invalid: ID must be an integer")
            except MissingPriceHistoryException:
                print("Invalid: Could not find price history. Item for ID either does not exist, or is a Neocash item.")

    @retry(
            wait=wait_random(min=MIN_WAIT_BETWEEN_REQ, max=MAX_WAIT_BETWEEN_REQ),
            stop=stop_after_attempt(MAX_RETRIES),
            retry=retry_if_exception_type(RequestException),        
    )

    def parse_html_as_soup(self, url: str) -> BeautifulSoup:
        """
        Request HTML data and parse as a BeautifulSoup object.

        :param str url: URL to send request to
        :return: BeautifulSoup of URL's HTML code
        :rtype: BeautifulSoup
        :raises RetryError: Raised when RequestException is raised after MAX_RETRIES attempts
        :raises MissingPriceHistoryException: Raised when item ID URL does not exist
        """
        resp = requests.get(url)
        if resp.status_code == 404:
            raise MissingPriceHistoryException
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        return soup

    @staticmethod
    def get_item_name(item_soup: BeautifulSoup) -> str:
        """
        Get name of item corresponding to item ID.

        :param BeautifulSoup item_soup: BeautifulSoup of item ID's IDB page
        :return: Item name
        :rtype: str
        """
        return item_soup.find("h1").text
    
    @staticmethod
    def get_item_image(item_soup: BeautifulSoup) -> str:
        """
        Get image URL of item corresponding to item ID.

        :param BeautifulSoup item_soup: BeautifulSoup of item ID's IDB page
        :return: Item image URL
        :rtype: str
        """
        return item_soup.find("meta", {"property": "og:image"})["content"]

    @staticmethod
    def get_price_history(item_soup: BeautifulSoup) -> pd.DataFrame:
        """
        Parse price history data of item corresponding to item ID.
        Skips all entries without an indicated price or date.

        :param BeautifulSoup item_soup: BeautifulSoup of item ID's IDB page
        :return: Dataframe of price history for the given item
        :rtype: pd.DataFrame
        """
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

    @staticmethod
    def check_if_inflated(item_soup: BeautifulSoup) -> tuple(str, str) | None:
        """
        Check if item currently has an inflation notice.
        Return price increase percentage and date inflation was observed if
        there is a notice, and None if there is no notice.

        :param BeautifulSoup item_soup: BeautifulSoup of item ID's IDB page
        :return: Tuple (price increase, date) if inflation notice exists, None otherwise
        :rtype: tuple | None
        """
        inflation_notice = item_soup.find("div", {"class": "alert-box inflated"})
        if inflation_notice:
            percent_increase = inflation_notice.find("strong").text
            date = re.findall("[A-Za-z]+ \d+, \d{4}", inflation_notice.text)[0]
            return (percent_increase, date)
        else:
            return None

