import streamlit as st
import re
import altair as alt
import snscrape.modules.twitter as sntwitter
import pandas as pd

########################### Streamlit configs ###########################

st.set_page_config(page_title='Twitter dashboard', page_icon='https://www.flaticon.com/br/icone-gratis/sinal-do-twitter_25347?term=twitter&page=1&position=5&page=1&position=5&related_id=25347&origin=tag')


########################### Data Pipeline ###########################

def twitterProfileScrape(twitter_url, n_tweets=100):
    # Creating list to append tweet data to
    tweets_list = []
    user = twitter_url.replace('https://twitter.com/', '')
    # Using TwitterSearchScraper to scrape data and append tweets to list
    for i,tweet in enumerate(sntwitter.TwitterSearchScraper(f'from:{user}').get_items()):
        if i > n_tweets:
            break
        
        else:
            
            tweets_list.append([tweet.user.username, tweet.user.displayname, tweet.user.renderedDescription,
                             tweet.user.followersCount,tweet.user.friendsCount, tweet.date, tweet.id, 
                             tweet.rawContent, tweet.likeCount, tweet.retweetCount, tweet.replyCount])

    # Creating a dataframe from the tweets list above 
    tweets_df = pd.DataFrame(tweets_list, columns=['Username', 'Displayname', 'Description', 'Follower Count', 
                                                    'Following Count', 'Datetime', 'Tweet Id', 'Text', 'Likes',
                                                     'Retweets', 'Replies'])
    
    tweets_df['like_ratio'] = (tweets_df['Likes'] / tweets_df['Follower Count']) * 100
    tweets_df['RT_ratio'] = (tweets_df['Retweets'] / tweets_df['Follower Count']) * 100
    tweets_df['reply_ratio'] = (tweets_df['Replies'] / tweets_df['Follower Count']) * 100
    tweets_df['engagement_ratio'] = ((tweets_df['Likes'] + tweets_df['Retweets'] + tweets_df['Replies']) / tweets_df['Follower Count']) * 100
    tweets_df['day'] = tweets_df.Datetime.dt.day
    tweets_df['week'] = tweets_df.Datetime.dt.isocalendar().week
    tweets_df['month'] = tweets_df.Datetime.dt.month
    tweets_df['date'] = tweets_df.Datetime.dt.date

    return tweets_df

@st.experimental_memo(show_spinner=False)
def twitterDataframeConcat(url_list, n_tweets):
    dataframe = pd.DataFrame(columns=['Username', 'Displayname', 'Description', 'Follower Count', 
                                      'Following Count', 'Datetime', 'Tweet Id', 'Text', 'Likes',
                                      'Retweets', 'Replies'])
    for twitter_url in url_list:
        dataframe = pd.concat([dataframe, twitterProfileScrape(twitter_url, n_tweets)])
    
    return dataframe

########################### Data viz ###########################
def make_chart(df, kind, period='week'):
    chart = (
        alt.Chart(df.groupby(['Username', f'{period}'])[f'{kind}'].sum().rolling(4).mean().reset_index(), title=f'{kind}')
        .mark_area(opacity=0.3)
        .encode(
            x=f'{period}:T',
            y=alt.Y(f'{kind}:Q', stack=None),
            color='Username:N'
        )
    )
    return chart

########################### Event Handlers ###########################
def handle_load_tweets(candidates, n_tweets):
    
    with st.spinner(f'Carregando os últimos {n_tweets} tweets...'):
        df = twitterDataframeConcat(candidates, n_tweets)
        return df

def handle_show_analytics(df, period):
    st.altair_chart(make_chart(df=df, kind='engagement_ratio', period=period), use_container_width=True)
    st.altair_chart(make_chart(df=df, kind='like_ratio', period=period), use_container_width=True)
    st.altair_chart(make_chart(df=df, kind='RT_ratio', period=period), use_container_width=True)
    st.altair_chart(make_chart(df=df, kind='reply_ratio', period=period), use_container_width=True)
    st.altair_chart(make_chart(df=df, kind='Likes', period=period), use_container_width=True)
    st.altair_chart(make_chart(df=df, kind='Retweets', period=period), use_container_width=True)
    st.altair_chart(make_chart(df=df, kind='Replies', period=period), use_container_width=True)

###########################  UI  ###########################


candidates = st.sidebar.multiselect(
    label = 'Escolha os candidatos a serem analisados',
    options = ['https://twitter.com/jairbolsonaro', 'https://twitter.com/LulaOficial',
    'https://twitter.com/cirogomes','https://twitter.com/simonetebetbr', 
    'https://twitter.com/fdavilaoficial', 'https://twitter.com/verapstu',
    'https://twitter.com/pablomarcal'],
    default = ['https://twitter.com/jairbolsonaro', 'https://twitter.com/LulaOficial', 
               'https://twitter.com/cirogomes'],
    format_func = lambda any : re.sub('https://twitter.com/', '', any)
)

period = st.sidebar.radio('Escolha o intervalo de agregação', ('date','week', 'month'))

if period == 'week' or period == 'date':
    n_tweets = st.sidebar.slider('Escolha o número de tweets a serem analisados', 100, 4000)
else:
    n_tweets = st.sidebar.slider('Escolha o número de tweets a serem analisados', 1000, 5000)

if st.sidebar.button('Carregar tweets'):
    st.session_state['df'] = handle_load_tweets(candidates, n_tweets)

if st.sidebar.button('Analisar'):
    handle_show_analytics(st.session_state['df'], period)
else:
    st.markdown('# Twitter data dashboard')
    st.write("Análise quantitativa do perfil do twitter dos candidatos a presidência")
    st.write('Para usar o app, escolha os candidatos, o período de agregação dos dados e o número de tweets.  \
              Depois clique em "Carregar tweets" e quando o carregamento for concluído (pode levar uns minutos),\
               clique em "Analisar"')