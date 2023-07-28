
from bs4 import BeautifulSoup

from backend import JellyneoIDBCrawler
from const import IDB_URL_TEMPLATE
from errors import MissingPriceHistoryException

class JellyneoIDBDashboard(JellyneoIDBCrawler):

    """Implements utilities to display Jellyneo Item Database data."""

    def __init__(self) -> None:
        self.item_soup = self.send_request()
   
    def run(self):
        print(self.get_price_history(self.item_soup))
        


