
import altair as alt
import streamlit as st
from bs4 import BeautifulSoup

from backend import JellyneoIDBCrawler
from const import IDB_URL_TEMPLATE
from errors import MissingPriceHistoryException

class JellyneoIDBDashboard(JellyneoIDBCrawler):

    """Implements utilities to display Jellyneo Item Database data."""

    def run(self):
        item_soup = None
        input_id = st.text_input("Enter Neopets item ID:", value="2288")
        if st.button("Confirm"):
            try:
                input_id = int(input_id)
                item_soup = self.send_request(input_id)
            except ValueError:
                st.write("Invalid: Item ID must be an integer")
            except MissingPriceHistoryException:
                st.write("Invalid: Could not find price history. Item for ID either does not exist or is a Neocash item")

        if item_soup:
            price_history = self.get_price_history(item_soup)
            item_name = self.get_item_name(item_soup)
            line_chart = (
                alt.Chart(price_history, title=f"Price History of {item_name}")
                .mark_line(point=True)
                .encode(
                    x=alt.X("date", title="Date"),
                    y=alt.Y("price", title="Price (thousand NPs)"),
                    color=alt.value("red")
                )
            )
            st.altair_chart(line_chart)
        


