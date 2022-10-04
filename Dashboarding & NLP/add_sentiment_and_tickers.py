import pandas as pd
import re
import string
import os

from textblob import TextBlob
pol = lambda x: TextBlob(x).sentiment.polarity
sub = lambda x: TextBlob(x).sentiment.subjectivity

#%%

posts_df = pd.read_csv('./all_posts_week_week_recent.csv')
comments_df = pd.read_csv('./all_comments_week_recent.csv')

#clean the body section of both dataframes
def clean_comments(comment):
    comment = str(comment)#.lower()
    comment = re.sub(r'[\(\[].*?[\)\]]', '', comment)
    comment = re.sub('[%s]' % re.escape(string.punctuation), '', comment)
    comment = os.linesep.join([s for s in comment.splitlines() if s])
#     comment = re.sub('[%s]' % re.escape(string.punctuation), '', comment)
    return comment

posts_df['clean_body'] = posts_df['title'].apply(lambda x: clean_comments(x))
comments_df['clean_body'] = comments_df['body'].apply(lambda x: clean_comments(x))


#%%
#get the sentiment for the clean_body columns
for df in [posts_df,comments_df]:
    df['polarity'] = df['clean_body'].apply(pol)
    df['subjectivity'] = df['clean_body'].apply(sub)
    df['weighted_sentiment'] = df['score'].abs() * df['polarity'] * ((1-df['subjectivity']))

#%%

posts_df = posts_df[[c for c in posts_df.columns if "Unnamed" not in c]].copy()
comments_df = comments_df[[c for c in comments_df.columns if "Unnamed" not in c]].copy()

#posts_df.to_csv('./new_data_2/all_posts_withSentiment.csv')
#comments_df.to_csv('./new_data_2/all_comments_withSentiment.csv')


#%%

#ticker_dfs = ['./amex_stocks.csv',
#              './nasdaq_stocks.csv',
#              './nyse_stocks.csv']

ticker_dfs = ['sp500_tickers.csv']
tickers = []

for path in ticker_dfs:
    tickers.append(pd.read_csv(path))

tickers = pd.concat(tickers)
unique_tickers = set(tickers['Symbol'].astype(str).unique())

for df in [posts_df,comments_df]:
    df['word_list'] = df['clean_body'].astype(str).str.split(" ").apply(set)
    df['tickers_mentioned'] = df['word_list'].apply(lambda x: " ,".join(list(x.intersection(unique_tickers))))
    
    
posts_df.to_csv('./all_posts_withSentimentTickers_week_recent.csv')
comments_df.to_csv('./all_comments_withSentimentTickers_week_recent.csv')

#%%

#example
gme = comments_df[comments_df['tickers_mentioned'].apply(lambda x: "TSLA" in x)].copy()

gme['created_utc'] = pd.to_datetime(gme['created_utc'],unit='s', origin='unix')
gme['created_date'] = gme['created_utc'].dt.date
gme.groupby('created_date').agg({'weighted_sentiment':'sum'}).plot()

