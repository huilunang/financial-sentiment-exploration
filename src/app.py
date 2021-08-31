import base64

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from plotly.subplots import make_subplots
from data import get_stock, get_tweets_sentiment


# Delete cache after 3 hr to load new data
@st.cache(ttl=10800)
def load_data(ticker: str):
    """
    To load twitter's tweet on stock data occurring past 7 days

        Param:
            ticker: Specific interest of stock

        Return:
            Dataframe object
    """
    tweets = get_tweets_sentiment(ticker)
    return tweets


def display_data(tweets, stocks):
    """
    To plot sentiment data on tweets, and available stock close price movement

        Param:
            tweets: Dataframe on tweets data
            stocks: Dataframe on stocks data

        Return:
            Plotly figure/chart
    """
    tweets = (pd.DataFrame(tweets.groupby("date").mean().round(2))).reset_index()
    tweets["date"] = pd.to_datetime(tweets["date"])

    # Merge the 2 DataFrame
    df = pd.merge(tweets, stocks, how="left")

    # Plot the graphs
    fig = make_subplots(rows=2, cols=1,
                        shared_xaxes=True,
                        subplot_titles=("Sentiment", "Close Price"),
                        vertical_spacing=0.1)

    fig.add_trace(go.Scatter(name="Score", x=df["date"], y=df["score"]),
                row=1, col=1)

    fig.add_trace(go.Bar(name="Price", x=df["date"], y=df["close"]),
                row=2, col=1)

    title = f"Sentiment on {input_ticker} stock"
    fig.update_layout(height=600, width=700,
                    title_text=title)
    return fig


def download_data(tweets):
    """
    To enable downloading of current financial stock tweet search

        Param:
            tweets: Dataframe object on tweet data
            ticker: Specific interest of stock

        Return:
            Clickable link to download file
    """
    csv = tweets.loc[:, tweets.columns != 'date'].to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    custom_css = """
        <style>
            #button {
                color: #5B5B60;
                text-decoration: none;
                font-size: 0.8em;
                border-radius: 4px;
                border-width: 1px;
                border-style: solid;
                border-color: #C9C9D1;
                padding: 5px;
            }

            #button:hover {
                color: #E8CAAC;
                border-color: #E8CAAC;
            }
        </style>
    """
    link = custom_css + f'''<a href="data:file/csv;base64,{b64}" download="tweets_data.csv"
                            id="button">Click to download data :paw_prints:</a>'''
    return link


def round_fig(num):
    """
    To round number to 2dp
    """
    if num is None:
        return 'None'
    return str(round(num, 2))


st.title("Sentiment on stocks")
st.write("A sentiment reader on twitter data to find out public opinion on the specific stock")
input_ticker = st.text_input("Ticker", "MSFT", help="Enter a ticker!")
stock_info, stock_data = get_stock(input_ticker)


if stock_info.get("regularMarketPrice") is None:
    st.write(f"The ticker '{input_ticker}' does not exist.")
else:
    tweets_data = load_data(input_ticker)
    chart = display_data(tweets_data, stock_data)
    with st.expander("Show ticker information"):
        c1, c2 = st.columns(2)
        c1.text("Company: " + stock_info.get("longName"))
        c1.text("Sector: " + stock_info.get("sector"))
        c1.text("Ytd's close price: " + round_fig(stock_info.get("previousClose")))
        c1.text("------------------------------------")
        c1.text("Trailing annual dividend yield: " +round_fig(stock_info.get("trailingAnnualDividendYield")))
        c1.caption("""Trailing annual dividend yield gives the dividend percentage
                    paid over a year. It represents the ratio of a company's
                    current annual dividend compared to its current share price. """)
        c1.text("P/B ratio (recent quarter): " + round_fig(stock_info.get("priceToBook")))
        c1.caption("""The price-to-book-value (P/B) ratio, compares the price of the
                    stock to the current book value of the company — the total value of the
                    company’s assets minus any liabilities — on a per-share basis.""")
        c2.text("Trailing P/E: " + round_fig(stock_info.get("trailingPE")))
        c2.caption("""Trailing P/E ratio compares the company’s earnings per share (EPS),
                    generated over the past 12 months to the current price of the stock.
                    This enables comparison of the price paid for a unit of profits from
                    one stock to another.""")
        c2.text("Beta (5Y Monthly): " + round_fig(stock_info.get("beta")))
        c2.caption("""It measures volatility, or how 'moody' the company's stock has acted
                    over the last five years. In essence, it measures the systemic risk
                    involved with a company's stock compared to that of the entire market.
                    If a company drops or rises in value more than the index over a five-year
                    period, it has a higher beta. With beta > 1 would mean a higher risk -
                    and anything < 1 would mean a lower risk.""")

    st.plotly_chart(chart, use_container_width=True)
    with st.expander("Show raw data"):
        st.markdown(download_data(tweets_data, input_ticker), unsafe_allow_html=True)
        st.dataframe(tweets_data.loc[:, tweets_data.columns != 'date'])
