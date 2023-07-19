import plotly.express as px
import pandas as pd
import numpy as np
import dash
from dash import html, dcc
from dash.dependencies import Input, Output

app = dash.Dash(__name__)

path_input_csv = 'comments_2023-06-17_2133_sentiment.csv'
df = pd.read_csv(path_input_csv, sep=';')

# Ensure your dates are in datetime format
df['Episode_Date'] = pd.to_datetime(df['Episode_Date'])
df['Comment_Date'] = pd.to_datetime(df['Comment_Date'])
df['Reply_Date'] = pd.to_datetime(df['Reply_Date'])


# Calculate the sentiment score for each comment and reply
# Handle empty comments and replies
def sentiment_score(row, label, score, text):
    if pd.isna(row[text]):
        return np.nan
    elif row[label] == 'positive':
        return row[score]
    elif row[label] == 'negative':
        return -1*row[score]
    else:
        return 0


df['Sentiment_Score_comment'] = df.apply(lambda row: sentiment_score(row,'SA_label_comment_text','SA_score_comment_text', 'Comment_Text'),axis=1)
df['Sentiment_Score_reply'] = df.apply(lambda row: sentiment_score(row,'SA_label_reply_text','SA_score_reply_text','Reply_Text'),axis=1)

# Print unique series_name alongside their series_genre
#print(df[['series_name','series_genre']].drop_duplicates())

df_likes_date = df[['series_genre','Episode_Date','Episode_Likes','episode_ID_number']]
#Keep only the unique occurence of series_name and episode_ID_number
df_likes_date = df_likes_date.drop_duplicates(subset=['series_genre','episode_ID_number'], keep='first')
# Order by series_genre and episode_ID_number
df_likes_date = df_likes_date.sort_values(by=['series_genre','episode_ID_number'])
df_likes_date = df_likes_date.reset_index(drop=True)

#Group by series_genre and average the Episode_Likes
df_grouped_avg = df_likes_date.groupby(['series_genre']).mean().reset_index()
df_grouped_count = df_likes_date.groupby(['series_genre']).count().reset_index()
df_grouped_count = df_grouped_count[['series_genre','Episode_Date']]
df_grouped_count.columns = ['series_genre','Episode_Count']

fig_avg = px.bar(df_grouped_avg, x='series_genre', y='Episode_Likes', color='series_genre', title='Average likes per genre')
fig_likes = px.line(df_likes_date, x='episode_ID_number', y='Episode_Likes', color='series_genre', title='Likes per episode')

# For each genre, store the number of likes of the first episode in a list
list_first_episode = []
for genre in df_grouped_count['series_genre']:
    list_first_episode.append(df_likes_date[df_likes_date['series_genre']==genre]['Episode_Likes'].iloc[0])

#print(list_first_episode)

# For each genre, calcualte the percentage of likes compared to the first episode
df_likes_date['Percentage_Likes'] = df_likes_date.apply(lambda row: row['Episode_Likes']/list_first_episode[df_grouped_count[df_grouped_count['series_genre']==row['series_genre']].index[0]], axis=1)

# Plot the percentage of likes compared to the first episode
fig_percentdrop = px.line(df_likes_date, x='episode_ID_number', y='Percentage_Likes', color='series_genre', title='Percentage of likes compared to the first episode')

df_sentiment_score = df[['series_genre','Episode_Date','Episode_Likes','episode_ID_number','Sentiment_Score_comment','Sentiment_Score_reply']]
#Keep only the occurence where the Sentiment_Score_comment and Sentiment_Score_reply are not 0
df_sentiment_score_nozero = df_sentiment_score[(df_sentiment_score['Sentiment_Score_comment']!=0)]
df_sentiment_score_nozero = df_sentiment_score_nozero.dropna(subset=['Sentiment_Score_comment'])

fig_boxplot = px.box(df_sentiment_score_nozero, x='series_genre', y='Sentiment_Score_comment', color='series_genre', title='Sentiment score per genre')

app.layout = html.Div([
    html.H1("WEM - Manga sentiment analysis dashboard"),
    dcc.Dropdown(
        id='genre-dropdown',
        options=[
            {'label': 'Action', 'value': 'Action'},
            {'label': 'Thriller/Crime/Mystery', 'value': 'Thriller/Crime/Mystery'},
            {'label': 'Romance/Drama', 'value': 'Romance/Drama'},
            {'label': 'Fantasy/Comedy', 'value': 'Fantasy/Comedy'},
            {'label': 'Comedy/Slice of life', 'value': 'Comedy/Slice of life'},
            {'label': 'Superhero/Comedy', 'value': 'Superhero/Comedy'},
            {'label': 'Sci-fi/Drama', 'value': 'Sci-fi/Drama'},
            {'label': 'Romance', 'value': 'Romance'},
            {'label': 'All Genres', 'value': 'All'}
        ],
        value=['All'],
        multi=True
    ),
    html.Div(
        className='grid-container',
        children=[
            html.Div(
                className='graph-container',
                children=[
                    dcc.Graph(id='average-likes-graph')
                ]
            ),
            html.Div(
                className='graph-container',
                children=[
                    dcc.Graph(id='likes-per-episode-graph')
                ]
            ),
            html.Div(
                className='graph-container',
                children=[
                    dcc.Graph(id='percentage-likes-graph')
                ]
            ),
            html.Div(
                className='graph-container',
                children=[
                    dcc.Graph(id='sentiment-score-graph')
                ]
            )
        ],
        style={'display': 'grid', 'grid-template-columns': '50% 50%', 'grid-gap': '20px'}
    )
])



@app.callback(
    Output('average-likes-graph', 'figure'),
    Output('likes-per-episode-graph', 'figure'),
    Output('percentage-likes-graph', 'figure'),
    Output('sentiment-score-graph', 'figure'),
    Input('genre-dropdown', 'value')
)
def update_graphs(selected_genres):
    if 'All' in selected_genres:
        filtered_likes_date = df_likes_date.copy()
        filtered_grouped_avg = df_grouped_avg.copy()
        filtered_sentiment_score_nozero = df_sentiment_score_nozero.copy()
    else:
        filtered_likes_date = df_likes_date[df_likes_date['series_genre'].isin(selected_genres)]
        filtered_grouped_avg = df_grouped_avg[df_grouped_avg['series_genre'].isin(selected_genres)]
        filtered_sentiment_score_nozero = df_sentiment_score_nozero[df_sentiment_score_nozero['series_genre'].isin(selected_genres)]
    
    fig_avg = px.bar(filtered_grouped_avg, x='series_genre', y='Episode_Likes', color='series_genre',
                     title='Average likes per genre')
    
    fig_likes = px.line(filtered_likes_date, x='episode_ID_number', y='Episode_Likes', color='series_genre',
                        title='Likes per episode')
    
    fig_percentdrop = px.line(filtered_likes_date, x='episode_ID_number', y='Percentage_Likes', color='series_genre',
                              title='Percentage of likes compared to the first episode')
    
    fig_boxplot = px.box(filtered_sentiment_score_nozero, x='series_genre', y='Sentiment_Score_comment', color='series_genre',
                            title='Sentiment score per genre')
    
    return fig_avg, fig_likes, fig_percentdrop, fig_boxplot

if __name__ == '__main__':
    app.run_server(debug=True)