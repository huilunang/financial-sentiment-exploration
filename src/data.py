import re

from datetime import datetime, timedelta

import os
import pandas as pd
import requests
import yfinance as yf

from textblob import TextBlob


def tweet_url(ticker: str, start_time: str, end_time: str):
    """
    Get tweets on specific stock ticker

        Param:
            ticker: Specific interest of stock
            start_time (ISO): Oldest UTC timestamp to get tweets from (From)
            end_time (ISO): Most recent UTC timestamp to get tweets (To)

        Return:
            Query response, data
    """
    payload = {
        "max_results": "100",
        "query": "#{} lang:en has:hashtags -is:retweet".format(ticker),
        # "tweet.fields": "author_id,created_at,entities,id,in_reply_to_user_id,lang,
        #                   possibly_sensitive,referenced_tweets,source,text,withheld",
        "tweet.fields": "author_id,id,text,created_at,possibly_sensitive,source",
        "expansions": "author_id",
        "user.fields": "username,verified",
        "start_time": start_time,
        "end_time": end_time,
    }
    token = {"Authorization": "Bearer {}".format(os.environ.get("BEARER_TOKEN"))}

    response = requests.get("https://api.twitter.com/2/tweets/search/recent",
                            params=payload, headers=token)

    # print("This is res headers: ", response.headers)
    # print("This is response: ", response.json())
    return response


def clean_tweets(tweet):
    """
    Clean tweets for final display to user

        Param:
            tweet: Series object

        Return:
            Cleaned series object
    """
    ticker = re.compile(r"(\$[A-Za-z]{1,5})")
    space = re.compile(r"\s+")
    newline = re.compile(r"\n+")

    tweet = ticker.sub("", tweet)
    tweet = space.sub(" ", tweet)
    tweet = newline.sub("", tweet)
    return tweet


def get_tweets(ticker: str):
    """
        To load ~100 (t)weets, interval at 12 hrs of last 7 days (appx. 200t/day)

            Param:
                ticker: Specific interest of stock

            Return:
                    Dataframe object
    """
    time = timedelta(hours=12)
    dt_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    end_time = (datetime.utcnow() - timedelta(seconds=10)).isoformat() + "Z"
    start_time = (datetime.strptime(end_time, dt_format) - time + timedelta(seconds=10)).isoformat() + "Z"
    df = pd.DataFrame()
    for _ in range(14):
        try:
            data = tweet_url(ticker, start_time, end_time).json()
            tdata, udata = data["data"], data["includes"]["users"]
        except Exception as e:
            print("Exception occurred: ", e)
        else:
            tdf = pd.DataFrame(tdata).rename(columns={"id": "tweet_id"})
            udf = (pd.DataFrame(udata).drop(columns=["name"])).rename(columns={"id": "author_id"})
            temp_df = pd.merge(tdf, udf, on="author_id")
            df = df.append(temp_df, ignore_index=True).sort_values(by=["created_at"])
        finally:
            end_time = start_time
            start_time = (datetime.strptime(end_time, dt_format) - time).isoformat() + "Z"

    # Clean up datetime to date
    date_func = lambda x: (datetime.strptime(x, dt_format).date())
    df["date"] = df["created_at"].apply(date_func)
    df['ticker'] = ticker

    return df.loc[:, ["tweet_id", "text", "created_at", "date", "author_id",
                "username", "verified", "source", "possibly_sensitive", "ticker"]]


def clean_tweets_sentiment(tweet):
    """
    Clean tweets for sentiment analysis

        Param:
            tweet: Series object

        Return:
            Cleaned series object
    """
    space = re.compile(r"\s+")
    username = re.compile(r"(@[\w]{1,15})")
    ticker = re.compile(r"(\$[A-Za-z]{1,5})")
    # non-alphanum char (except \t\+.$#-:), links
    general = re.compile(r"([^0-9A-Za-z \t\+.$#-:])|(\w+:\/\/\S+)")

    tweet = username.sub("", tweet)
    tweet = ticker.sub("", tweet)
    tweet = general.sub("", tweet)
    tweet = space.sub(" ", tweet)
    return tweet


def get_tweets_sentiment(ticker: str):
    """
    To generate sentiment on the tweets

        Param:
            ticker: Specific interest of stock

        Return:
            Dataframe object
    """
    tweets = get_tweets(ticker)
    ctweets = tweets["text"].apply(clean_tweets_sentiment)
    senti_scores = pd.DataFrame(ctweets.apply(lambda x: TextBlob(x).sentiment).to_list())
    tweets["score"] = senti_scores["polarity"].round(2)
    senti_func = lambda x: "Negative" if x<0 else ("Positive" if x>0 else "Neutral")
    tweets["sentiment"] = tweets["score"].apply(senti_func)
    df = tweets.loc[:, ["text", "score", "sentiment", "created_at", "date"]]
    df.drop_duplicates(subset=['text'], inplace=True)
    df.loc[:, "text"] = df["text"].apply(clean_tweets)
    return df


def get_stock(ticker: str):
    """
    Get market data on stocks using yfinance

        Param:
            ticker: Specific interest of stock

        Return:
            Company information and close price of ticker
    """
    ticker_info = yf.Ticker(ticker)
    data = yf.download(ticker, period="5d")
    data["date"] = data.index
    data.columns = ["open", "high", "low", "close", "adj_close", "volume", "date"]
    data = data.loc[:, ["date", "close"]].reset_index(drop=True)
    return ticker_info.info, data
