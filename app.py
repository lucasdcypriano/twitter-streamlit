import streamlit as st
import re
import altair as alt
import snscrape.modules.twitter as sntwitter
import pandas as pd

def twitterProfileScrape(twitter_url, n_tweets=500):
    # Creating list to append tweet data to
    tweets_list = []
    user = twitter_url.replace('https://twitter.com/', '')
    # Using TwitterSearchScraper to scrape data and append tweets to list
    for i,tweet in enumerate(sntwitter.TwitterSearchScraper(f'from:{user}').get_items()):
        if i>n_tweets:
            break
        
        else:
            
            tweets_list.append([tweet.user.username, tweet.user.displayname, tweet.user.renderedDescription,
                             tweet.user.followersCount,tweet.user.friendsCount, tweet.date, tweet.id, 
                             tweet.rawContent, tweet.likeCount, tweet.retweetCount, tweet.replyCount])

    # Creating a dataframe from the tweets list above 
    tweets_df = pd.DataFrame(tweets_list, columns=['Username', 'Displayname', 'Description', 'Follower Count', 
                                                    'Following Count', 'Datetime', 'Tweet Id', 'Text', 'Likes',
                                                     'Retweets', 'Replies'])
    
    tweets_df['day'] = tweets_df.Datetime.dt.day
    tweets_df['week'] = tweets_df.Datetime.dt.isocalendar().week
    tweets_df['month'] = tweets_df.Datetime.dt.month
    tweets_df['date'] = tweets_df.Datetime.dt.date

    return tweets_df

def twitterDataframeConcat(url_list, n_tweets):
    dataframe = pd.DataFrame(columns=['Username', 'Displayname', 'Description', 'Follower Count', 
                                      'Following Count', 'Datetime', 'Tweet Id', 'Text', 'Likes',
                                      'Retweets', 'Replies'])
    for twitter_url in url_list:
        dataframe = pd.concat([dataframe, twitterProfileScrape(twitter_url, n_tweets)])
    
    return dataframe

def display_chart(kind, period='week'):
    chart = (
        alt.Chart(df.groupby(['Username', f'{period}'])[f'{kind}'].sum().reset_index(), title=f'Nº {kind}')
        .mark_area(opacity=0.3)
        .encode(
            x=f'{period}:T',
            y=alt.Y(f'{kind}:Q', stack=None),
            color='Username:N'
        )
    )
    return chart


candidates = st.multiselect(
    label = 'Escolha os candidatos a serem analisados',
    options = ['https://twitter.com/jairbolsonaro', 'https://twitter.com/LulaOficial',
    'https://twitter.com/cirogomes','https://twitter.com/simonetebetbr', 
    'https://twitter.com/fdavilaoficial', 'https://twitter.com/verapstu',
    'https://twitter.com/pablomarcal'],
    default = ['https://twitter.com/jairbolsonaro', 'https://twitter.com/LulaOficial'],
    format_func = lambda any : re.sub('https://twitter.com/', '', any)
)

n_tweets = st.slider('Escolha o número de tweets a serem analisados', 500, 4000)
period = st.radio('Escolha o intervalo', ('week', 'month'))


if st.button('Analisar'):
    with st.spinner(f'Carregando os últimos {n_tweets} tweets...'):
        df = twitterDataframeConcat(candidates, n_tweets)

        st.altair_chart(display_chart(kind='Likes', period=period), use_container_width=True)
        st.altair_chart(display_chart(kind='Retweets', period=period), use_container_width=True)
        st.altair_chart(display_chart(kind='Replies', period=period), use_container_width=True)
else:
    pass