from dataclasses import fields
import streamlit as st
import re
import altair as alt
import snscrape.modules.twitter as sntwitter
import pandas as pd

########################### Streamlit configs ###########################

st.set_page_config(page_title='Twitter dashboard', page_icon='https://cdn-icons-png.flaticon.com/512/25/25347.png')
# hide_streamlit_style = """
#                 <style>
#                 div[data-testid="stToolbar"] {
#                 visibility: hidden;
#                 height: 0%;
#                 position: fixed;
#                 }
#                 div[data-testid="stDecoration"] {
#                 visibility: hidden;
#                 height: 0%;
#                 position: fixed;
#                 }
#                 div[data-testid="stStatusWidget"] {
#                 visibility: hidden;
#                 height: 0%;
#                 position: fixed;
#                 }
#                 #MainMenu {
#                 visibility: hidden;
#                 height: 0%;
#                 }
#                 header {
#                 visibility: hidden;
#                 height: 0%;
#                 }
#                 footer {
#                 visibility: hidden;
#                 height: 0%;
#                 }
#                 </style>
#                 """
# st.markdown(hide_streamlit_style, unsafe_allow_html=True)



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
    hover = alt.selection_single(
        fields=[f'{period}'],
        nearest=True,
        on='mouseover',
        empty='none',
    )

    lines = (
        alt.Chart(df, title=f'{kind}')
        .mark_line()
        .encode(
            x=f'{period}:T',
            y=alt.Y(f'sum({kind}):Q', title=f'{kind}'),
            color='Username:N'
        )
    )

    points = lines.transform_filter(hover).mark_circle(size=65)

    tooltips = (
        alt.Chart(df)
        .mark_rule()
        .encode(
            x=f'{period}',
            y=f'{kind}',
            opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
            tooltip=[
                alt.Tooltip(f'{period}', title=f'{period}'),
                alt.Tooltip(f'{kind}', title=f'{kind}')
            ],
        )
        .add_selection(hover)
    )
    return (lines + points + tooltips).interactive()

def make_boxplot(df, kind):
    chart = (
        alt.Chart(df, title=f'{kind}')
        .mark_boxplot(size=50, extent=2, outliers=False)
        .encode(
            x='Username:N',
            y=alt.Y(f'{kind}:Q', scale=alt.Scale(zero=False)),
            color=alt.Color('Username')
        )
        .properties(width=600)
    )
    return chart

########################### Event Handlers ###########################
def handle_load_tweets(candidates, n_tweets):
    
    with st.spinner(f'Carregando os ??ltimos {n_tweets} tweets...'):
        df = twitterDataframeConcat(candidates, n_tweets)
        return df

def handle_show_analytics(df, period):
    st.latex(r'''engagement\underline{\hspace{.05in}}ratio = \frac{(Likes + Retweets + Replies)}{Followers}''')
    st.altair_chart(make_chart(df=df, kind='engagement_ratio', period=period).interactive(), use_container_width=True)
    st.latex(r'''like\underline{\hspace{.05in}}ratio = \frac{Likes}{Followers}''')
    st.altair_chart(make_chart(df=df, kind='like_ratio', period=period).interactive(), use_container_width=True)
    st.latex(r'''RT\underline{\hspace{.05in}}ratio = \frac{Retweets}{Followers}''')
    st.altair_chart(make_chart(df=df, kind='RT_ratio', period=period).interactive(), use_container_width=True)
    st.latex(r'''Reply\underline{\hspace{.05in}}ratio = \frac{Replies}{Followers}''')
    st.altair_chart(make_chart(df=df, kind='reply_ratio', period=period).interactive(), use_container_width=True)
    st.altair_chart(make_chart(df=df, kind='Likes', period=period).interactive(), use_container_width=True)
    st.altair_chart(make_chart(df=df, kind='Retweets', period=period).interactive(), use_container_width=True)
    st.altair_chart(make_chart(df=df, kind='Replies', period=period).interactive(), use_container_width=True)

def handle_show_boxplot(df):
    st.altair_chart(make_boxplot(df=df, kind='Likes'), use_container_width=True)
    st.altair_chart(make_boxplot(df=df, kind='Retweets'), use_container_width=True)
    st.altair_chart(make_boxplot(df=df, kind='Replies'), use_container_width=True)
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

n_tweets = st.sidebar.slider('Escolha o n??mero de tweets a serem analisados', 1000, 5000)

tab1, tab2 = st.tabs(['Linha', 'Boxplot'])

if st.sidebar.button('Carregar tweets e analisar'):
    st.session_state['df'] = handle_load_tweets(candidates, n_tweets)
    
    with tab1:
        handle_show_analytics(st.session_state['df'], period='date')
    with tab2:
        handle_show_boxplot(st.session_state['df'])

else:
    st.markdown('# Twitter data dashboard')
    st.write("An??lise quantitativa do perfil do twitter dos candidatos a presid??ncia")
    st.write('Para usar o app, escolha os candidatos e o n??mero de tweets.  \
              Depois clique em "Carregar tweets e analisar" e quando o carregamento for conclu??do (pode levar uns minutos),\
               navegue pelas abas para ver o comportamento ao longo do tempo nos gr??ficos de linha ou um resumo das m??tricas \
                no boxplot')