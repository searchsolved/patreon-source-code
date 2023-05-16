import streamlit as st

st.set_page_config(page_title="Keyword Entity Extractor by LeeFootSEO - Patreon Beta 3", page_icon="🎞️",
                   layout="wide")

import re
import pandas as pd
from dandelion import DataTXT
from youtube_transcript_api import YouTubeTranscriptApi
import pandas as pd

st.write(
        "[![this is an image link](https://i.imgur.com/Ex8eeC2.png)](https://www.patreon.com/leefootseo) [Become a Patreon for Early Access, Support & More!](https://www.patreon.com/leefootseo)  |  Made in [![this is an image link](https://i.imgur.com/iIOA6kU.png)](https://www.streamlit.io/) by [@LeeFootSEO](https://twitter.com/LeeFootSEO)")

st.title("YouTube Keyword Entity Extractor")

# streamlit variables
api_key = st.sidebar.text_input('Please enter your Dandelion API Key')
accuracy = st.sidebar.slider("Set Entity Accuracy", min_value=10, max_value=100, value=80)

# clean the input data
accuracy = accuracy / 100

# store the YouTube Data
sub_titles = []

# store the entity data
entity = []
confidence = []
title = []
wiki_url = []
categories = []


with st.form(key='columns_in_form_2'):
    yt = st.text_input('Please Paste in a YouTube URL')
    submitted = st.form_submit_button('Submit')

if submitted:

    #strip out the garbage from the urls
    yt = re.sub(r'^.*?=', '=', yt)
    yt = re.sub('\&.*', '&', yt)
    yt = yt.replace("&", "")
    yt = yt.replace("=", "")

    try:
        srt = YouTubeTranscriptApi.get_transcript(yt)
    except Exception:
        st.info("No Transcript Available to Process. Try Another Video!")
        st.stop()

    for text in srt:
        sub_titles.append(text['text'])

    text = " ".join(sub_titles)
    from dandelion import DataTXT

    try:
        datatxt = DataTXT(token=api_key)
    except Exception:
        st.write("Please Check API Key! Visit: https://dandelion.eu/ For a Free Key to Use This App! (1,000 Credits per day)")
    response = datatxt.nex(text)

    for annotation in response.annotations:
        entity.append(annotation['spot'])
        confidence.append(annotation['confidence'])
        title.append(annotation['title'])
        wiki_url.append(annotation['uri'])
        categories.append(annotation['label'])

    df = pd.DataFrame(None)
    df['entity'] = title
    df['confidence'] = confidence
    df['category'] = categories
    df['wiki_url'] = wiki_url

    # drop duplicates
    df['entity'] = df['entity'].str.lower()
    df['category'] = df['category'].str.lower()

    df = df[df.confidence >= accuracy]
    df['# of mentions'] = df['entity'].map(df.groupby('entity')['entity'].count())
    df.drop_duplicates(subset=['entity'], keep="first", inplace=True)
    df.sort_values(["# of mentions", "entity"], ascending=[False, True], inplace=True)

    def convert_df(df):  # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode('utf-8')

    csv = convert_df(df)

    st.download_button(
        label="📥 Download Your Entities!",
        data=csv,
        file_name='extracted_entities.csv',
        mime='text/csv')
