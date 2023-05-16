import streamlit as st

st.set_page_config(page_title="SERP Keyword Extractor", page_icon="📈",
                   layout="wide")
import pandas as pd
import requests
import json
import trafilatura
from trafilatura import extract
from trafilatura.settings import use_config
import altair as alt
from stqdm import stqdm
from rakun2 import RakunKeyphraseDetector
from io import BytesIO

hyperparameters = {"num_keywords": 10,
                   "merge_threshold": 1.1,
                   "alpha": 0.3,
                   "token_prune_len": 3}



newconfig = use_config()
newconfig.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")

st.write(
    "[![this is an image link](https://i.imgur.com/Ex8eeC2.png)](https://www.patreon.com/leefootseo) [Become a Patreon for Early Access, Support & More!](https://www.patreon.com/leefootseo)  |  Made in [![this is an image link](https://i.imgur.com/iIOA6kU.png)](https://www.streamlit.io/) by [@LeeFootSEO](https://twitter.com/LeeFootSEO)")

with st.expander("How do I use this app?"):
    st.write("""

        1. You will need an API key from www.ValueSERP.Com - they offer 100 searches for free
        Plenty to test this with!
        2. Enter your API key, enter a seed keyword, and click submit.
        3. This data can be used to dual optimise pages / expand on existing content etc""")

st.title("SERP Keyword Extractor")

# streamlit variables
q = st.text_input('Input Your Search Keyword')
value_serp_key = st.sidebar.text_input('Input your ValueSERP API Key')

location_select = st.sidebar.selectbox(
    "Select The Region To Search Google From",
    (
        "United Kingdom",
        "United States",
        "Australia",
        "Brazil",
        "Canada",
        "Delhi,India",
        "Denmark",
        "France",
        "Germany",
        "Hungary",
        "Italy",
        "Kenya",
        "New Zealand",
        "Norway",
        "Peru",
        "Poland",
        "Portugal",
        "Saudi Arabia",
        "South Africa",
        "Spain",
        "Sweden",

    ),
)

device_select = st.sidebar.selectbox(
    "Select The Host Device To Use To Search Google",
    (
        "Desktop",
        "Mobile",
        "Tablet",
    ),
)

num_pages = st.sidebar.slider("Set Number of Pages to Analyse", min_value=1, max_value=10, value=1)
top_kws = st.sidebar.slider("Set The Number of Keywords to Display", min_value=5, max_value=25, value=10)

num_pages = num_pages * 10

# store the SERP Data
query = []
serp_title = []
link = []

# store the keyphrase extractions
key_title = []
key_phrases = []
key_urls = []

with st.form(key='columns_in_form_2'):
    submitted = st.form_submit_button('Submit')
    keyword_detector = RakunKeyphraseDetector(hyperparameters)

if submitted:
    st.write("Searching Google for: %s" % q)

    params = {
        'api_key': value_serp_key,
        'q': q,
        'location': location_select,
        'include_fields': 'organic_results',
        'location_auto': True,
        'device': device_select,
        'output': 'json',
        'page': '1',
        'num': num_pages
    }

    response = requests.get('https://api.valueserp.com/search', params)
    response_data = json.loads(response.text)
    result = response_data.get('organic_results')

    try:
        for var in result:
            serp_title.append(var['title'])
            link.append(var['link'])
            query.append(q)
    except TypeError:
        st.info("No results returned, Did you enter a keyword to search?")
        st.stop()

    # make the serp df
    df_serp = pd.DataFrame(None)
    df_serp['Keyword'] = query
    df_serp['url'] = link
    df_serp['page_title'] = serp_title

    ######################################## get the entities

    df_serp['Keyword'] = df_serp['Keyword'].astype(str)
    df_serp.drop_duplicates(subset=['url'], keep="first", inplace=True)
    unique_urls = list(set(df_serp['url']))
    unique_titles = list(set(df_serp['page_title']))

    for url in stqdm(unique_urls):

        try:
            downloaded = trafilatura.fetch_url(url)
            txt = extract(downloaded, config=newconfig, favor_precision=True)

            out_keywords = keyword_detector.find_keywords(txt, input_type="string")
            key_phrases.append(out_keywords)
            key_urls.append(url)
        except Exception:
            pass

    df = pd.DataFrame(None)
    df['url'] = key_urls
    df['extracted_keywords'] = key_phrases

    df = pd.merge(df, df_serp[['url', 'page_title']], on='url', how='left')

    df = df.explode("extracted_keywords")

    df = df[df["extracted_keywords"].notna()]
    df['extracted_keywords'] = [val[0] for val in df["extracted_keywords"]]

    # make stats dataframe
    df_count_ifs = df.copy()
    df_count_ifs['keyword_freq'] = df['extracted_keywords'].map(
        df.groupby('extracted_keywords')['extracted_keywords'].count())
    df_count_ifs.drop_duplicates(subset=['extracted_keywords'], keep="first", inplace=True)
    df_count_ifs = df_count_ifs[["extracted_keywords", "keyword_freq"]]
    df_count_ifs = df_count_ifs.sort_values(by="keyword_freq", ascending=False)

    # change from tall to wide dataframe
    df['idx'] = (df.groupby(['url', 'page_title']).cumcount() + 1).astype(str)

    df = (df.pivot_table(index=['url', 'page_title'],
                         columns=['idx'],
                         values=['extracted_keywords'],
                         aggfunc='first'))
    df.columns = [' '.join(col) for col in df.columns]
    df = df.reset_index()

    # re-order the columns
    df = df[["url", "page_title", "extracted_keywords 1", "extracted_keywords 2", "extracted_keywords 3",
             "extracted_keywords 4", "extracted_keywords 5", "extracted_keywords 6", "extracted_keywords 7",
             "extracted_keywords 8", "extracted_keywords 9", "extracted_keywords 10"]]

    st.write(df)

    # altair
    df_chart = df_count_ifs[["extracted_keywords", "keyword_freq"]].copy()
    df_chart_download = df_chart
    df_chart = df_chart[:top_kws]
    st.subheader("📊 Top Extracted SERP Keywords")
    chart = (
        alt.Chart(df_chart)
            .mark_bar()
            .encode(
            alt.X("extracted_keywords:O", sort=alt.EncodingSortField(field="entity", op="count", order='ascending')),
            alt.Y("keyword_freq"),
            alt.Color("extracted_keywords:O", sort=alt.SortField('count', order='descending')),
            alt.Tooltip(["extracted_keywords", "keyword_freq"]),
        )
            .properties(width=800, height=400)
            .interactive()
    )
    st.altair_chart(chart)

    # save to Excel sheet
    dfs = [df, df_chart_download]  # make a list of the dataframe to use as a sheet


    def dfs_tabs(df_list, sheet_list, file_name):  # function to save all dataframes to one single excel doc

        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        count = 0
        for dataframe, sheet in zip(df_list, sheet_list):
            dataframe.to_excel(writer, sheet_name=sheet, startrow=0, startcol=0, index=False)

            workbook = writer.book
            worksheet = writer.sheets[sheet]

            # Get the dimensions of the dataframe.
            (max_row, max_col) = dfs[count].shape

            # Create a list of column headers, to use in add_table().
            column_settings = [{'header': column} for column in dfs[count].columns]

            # Add the Excel table structure. Pandas will add the data.
            worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': column_settings})

            # Make the columns wider for clarity.
            worksheet.set_column(0, max_col - 1, 25)

            # increase the count
            count = count +1

        writer.save()
        processed_data = output.getvalue()
        return processed_data


    sheets = ['Top Keywords Per Site', 'Top Keywords All']  # set list of worksheet names

    df_xlsx = dfs_tabs(dfs, sheets, 'keyword-serp-extraction.xlsx')
    st.download_button(label='📥 Download SERP Keyword Results', data=df_xlsx, file_name='serp_keyword_extraction_results.xlsx')
