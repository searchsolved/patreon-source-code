import streamlit as st
import pandas as pd
from pandas import DataFrame, Series
from typing import Union
import chardet

st.set_page_config(
    page_title="Striking Distance Creator by LeeFootSEO",
    page_icon="baseball",
    layout="wide",
)
st.title("Striking Distance Creator")
st.subheader("Automatic On-page Checker for Keywords Close to Ranking")
st.write(
    "An app which blends keyword data and crawl data to provide actionable insights for keywords close to ranking.")
st.write(
    "[![this is an image link](https://i.imgur.com/Ex8eeC2.png)](https://www.patreon.com/leefootseo) [Become a Patreon for Early Access, Support & More!](https://www.patreon.com/leefootseo)  |  Made in [![this is an image link](https://i.imgur.com/iIOA6kU.png)](https://www.streamlit.io/) by [@LeeFootSEO](https://twitter.com/LeeFootSEO)")
st.write("")
with st.expander("How do I use this app?"):
    st.write("""

        **Preparation**
        1. Crawl the site and set a custom extraction for the page copy
        2. Export Keywords from your tool (Must include a URL! Column)
        3. Custom Map the Column Names
        4. Click to Download your File!


        **Variable Slider**
        1. Set Min and Max Position to Be Consider Within Striking Distance (Default 4 - 20)
        2. Set the Minimum Monthly Search Volume Before Suggesting a Keyword

        **File Formats**
        1. UTF-8 Only
        2. CSV File Only

        **Please note**: Search Console exports won't work (because they do not contain a URL column. The API does, (page) and are fine to use. 

        **Demo Files**
     """)
    link = '[Download a Demo Crawl File (Control + S to Save)](https://gist.githubusercontent.com/searchsolved/ff92f8e41216879ff61c753493e2ab77/raw/4dd1af435f4fa477638e82822acb2713344207aa/crawl_file.csv)'
    st.markdown(link, unsafe_allow_html=True)
    link2 = '[Download a Demo Keyword File (Control + S to Save)](https://gist.githubusercontent.com/searchsolved/3504cc560264d7ebd0053530db6b59c5/raw/e8cdae4922638badbba1726f2c56f781d41455a2/demo_keywords_csv)'
    st.markdown(link2, unsafe_allow_html=True)
    link3 = '[Read Indepth Instructions](https://www.searchenginejournal.com/python-seo-striking-distance/423009/)'
    st.markdown(link3, unsafe_allow_html=True)

st.write("")
drop_all_true = True

pagination_filters = "filterby|page|p="  # filter patterns used to detect and drop paginated pages

# set slider values
min_position = st.sidebar.slider("Set The Min Position Cutoff", value=4, max_value=10)
max_position = st.sidebar.slider("Set The Max Position Cutoff", value=20, max_value=20)
min_volume = st.sidebar.slider("Set Minimum Search Volume", value=50, max_value=500000, step=50)

# set the layout columns
col1, col2 = st.columns(2)

# -------------------------------- read the keyword to a dataframe called df_crawl ----------------------------------
with col1:
    uploaded_file = st.file_uploader("Upload your keyword report in .csv format",
                                     help="""Which reports does the tool currently support?""")

    if uploaded_file is not None:
        try:
            result = chardet.detect(uploaded_file.getvalue())
            encoding_value = result["encoding"]

            if encoding_value == "UTF-16":
                white_space = True
            else:
                white_space = False

            df_keywords = pd.read_csv(
                uploaded_file,
                encoding=encoding_value,
                delim_whitespace=white_space,
                error_bad_lines=False,
            )
            number_of_rows = len(df_keywords)
            if number_of_rows == 0:
                st.caption("🚨 Your sheet seems empty!")

        except UnicodeDecodeError:
            st.warning("""🚨 The file doesn't seem to load. Check the filetype, file format and Schema""")

    else:
        st.stop()

# -------------------------------- read the crawl file to a dataframe called df_crawl ----------------------------------
with col2:
    uploaded_crawl_file = st.file_uploader("Upload your crawl export .csv format",
                                           help="""Which reports does the tool currently support?""")
    if uploaded_crawl_file is not None:

        try:
            result = chardet.detect(uploaded_crawl_file.getvalue())
            encoding_value = result["encoding"]
            if encoding_value == "UTF-16":
                white_space = True
            else:
                white_space = False

            df_crawl = pd.read_csv(
                uploaded_crawl_file,
                encoding=encoding_value,
                delim_whitespace=white_space,
                error_bad_lines=False,
            )

            number_of_rows = len(df_crawl)
            if number_of_rows == 0:
                st.caption("Your sheet seems empty!")

        except UnicodeDecodeError:
            st.warning("""🚨 The file doesn't seem to load. Check the filetype, file format and Schema""")

    else:
        st.stop()

# --------------------------------------------- forms to select columns ------------------------------------------------
with col1:
    st.subheader("Map the Keyword Export Columns")
    kw_col = st.selectbox('Select the KEYWORD column:', df_keywords.columns)
    vol_col = st.selectbox('Select the VOLUME column:', df_keywords.columns)
    url_col = st.selectbox('Select the URL column:', df_keywords.columns)
    position_col = st.selectbox('Select the POSITION column:', df_keywords.columns)

with col2:
    with st.form(key='columns_in_form_2'):
        st.subheader("Map the Crawl File Columns")
        address_col = st.selectbox('Select the URL column:', df_crawl.columns)
        title_col = st.selectbox('Select the PAGE TITLE column:', df_crawl.columns)
        h1_col = st.selectbox('Select the H1 column:', df_crawl.columns)
        copy_col = st.selectbox('Select the copy column:', df_crawl.columns)
        submitted_crawl_btn = st.form_submit_button('Submit')
# --------------------------------------------- start colab code -------------------------------------------------------

if submitted_crawl_btn == True:

    # just keep the required columns and rename them to standardised names
    df_crawl = df_crawl[[address_col, title_col, h1_col, copy_col]]
    df_crawl.rename(columns={address_col: "URL", title_col: "Title", h1_col: "H1", copy_col: "Copy"}, inplace=True)

    df_keywords = df_keywords[[url_col, kw_col, vol_col, position_col]]
    df_keywords.rename(columns={url_col: "URL", kw_col: "Keyword", vol_col: "Volume", position_col: "Position"},
                       inplace=True)

    # check if multiple urls are mapped to the same column
    dupe_crawl_cols = len(df_crawl.columns) == len(set(df_crawl.columns))
    dupe_kw_cols = len(df_keywords.columns) == len(set(df_keywords.columns))

    if dupe_crawl_cols == False:
        st.caption("🚨 Multiple values mapped to the same column! Please Re-check your mapping!")
        st.stop()

    if dupe_kw_cols == False:
        st.caption("🚨 Multiple values mapped to the same column! Please Re-check your mapping!")
        st.stop()

    # clean the keyword data
    df_keywords = df_keywords[df_keywords["URL"].notna()]  # remove any missing values
    df_keywords = df_keywords[df_keywords["Volume"].notna()]  # remove any missing values
    df_keywords = df_keywords.astype({"Volume": int})  # change data type to int
    df_keywords = df_keywords.sort_values(by="Volume",
                                          ascending=False)  # sort by highest vol to keep the top opportunity

    # make new dataframe to merge search volume back in later
    df_keyword_vol = df_keywords[["Keyword", "Volume"]]

    # drop rows if minimum search volume doesn't match specified criteria

    df_keywords.loc[df_keywords["Volume"] < min_volume, "Volume_Too_Low"] = "drop"
    df_keywords = df_keywords[~df_keywords["Volume_Too_Low"].isin(["drop"])]

    # drop rows if minimum search position doesn't match specified criteria
    df_keywords.loc[df_keywords["Position"] <= min_position, "Position_Too_High"] = "drop"
    df_keywords = df_keywords[~df_keywords["Position_Too_High"].isin(["drop"])]

    # drop rows if maximum search position doesn't match specified criteria
    df_keywords.loc[df_keywords["Position"] >= max_position, "Position_Too_Low"] = "drop"
    df_keywords = df_keywords[~df_keywords["Position_Too_Low"].isin(["drop"])]

    # drop pagination
    df_crawl = df_crawl[~df_crawl.URL.str.contains(pagination_filters)]

    df_keywords_group = df_keywords.copy()
    df_keywords_group["KWs in Striking Dist."] = 1  # used to count the number of keywords in striking distance
    df_keywords_group = (
        df_keywords_group.groupby("URL")
            .agg({"Volume": "sum", "KWs in Striking Dist.": "count"})
            .reset_index()
    )
    df_keywords_group.head()

    # create a new df, combine the merged data with the original data. display in adjacent rows ala grepwords
    df_merged_all_kws = df_keywords_group.merge(
        df_keywords.groupby("URL")["Keyword"]
            .apply(lambda x: x.reset_index(drop=True))
            .unstack()
            .reset_index()
    )

    df_merged_all_kws = df_merged_all_kws.sort_values(
        by="KWs in Striking Dist.", ascending=False
    )

    # reindex the columns to keep just the top five keywords
    cols = "URL", "Volume", "KWs in Striking Dist.", 0, 1, 2, 3, 4
    df_merged_all_kws = df_merged_all_kws.reindex(columns=cols)

    # create union and rename the columns
    df_striking: Union[Series, DataFrame, None] = df_merged_all_kws.rename(
        columns={
            "Volume": "Striking Dist. Vol",
            0: "KW1",
            1: "KW2",
            2: "KW3",
            3: "KW4",
            4: "KW5",
        }
    )

    # merges striking distance df with crawl df to merge in the title, h1 and category description
    df_striking = pd.merge(df_striking, df_crawl, on="URL", how="inner")

    # set the final column order and merge the keyword data in
    cols = [
        "URL",
        "Title",
        "H1",
        "Copy",
        "Striking Dist. Vol",
        "KWs in Striking Dist.",
        "KW1",
        "KW1 Vol",
        "KW1 in Title",
        "KW1 in H1",
        "KW1 in Copy",
        "KW2",
        "KW2 Vol",
        "KW2 in Title",
        "KW2 in H1",
        "KW2 in Copy",
        "KW3",
        "KW3 Vol",
        "KW3 in Title",
        "KW3 in H1",
        "KW3 in Copy",
        "KW4",
        "KW4 Vol",
        "KW4 in Title",
        "KW4 in H1",
        "KW4 in Copy",
        "KW5",
        "KW5 Vol",
        "KW5 in Title",
        "KW5 in H1",
        "KW5 in Copy",
    ]
    # re-index the columns to place them in a logical order + inserts new blank columns for kw checks.
    df_striking = df_striking.reindex(columns=cols)

    # merge in keyword data for each keyword column (KW1 - KW5)
    df_striking = pd.merge(df_striking, df_keyword_vol, left_on="KW1", right_on="Keyword", how="left")
    df_striking['KW1 Vol'] = df_striking['Volume']
    df_striking.drop(['Keyword', 'Volume'], axis=1, inplace=True)
    df_striking = pd.merge(df_striking, df_keyword_vol, left_on="KW2", right_on="Keyword", how="left")
    df_striking['KW2 Vol'] = df_striking['Volume']
    df_striking.drop(['Keyword', 'Volume'], axis=1, inplace=True)
    df_striking = pd.merge(df_striking, df_keyword_vol, left_on="KW3", right_on="Keyword", how="left")
    df_striking['KW3 Vol'] = df_striking['Volume']
    df_striking.drop(['Keyword', 'Volume'], axis=1, inplace=True)
    df_striking = pd.merge(df_striking, df_keyword_vol, left_on="KW4", right_on="Keyword", how="left")
    df_striking['KW4 Vol'] = df_striking['Volume']
    df_striking.drop(['Keyword', 'Volume'], axis=1, inplace=True)
    df_striking = pd.merge(df_striking, df_keyword_vol, left_on="KW5", right_on="Keyword", how="left")
    df_striking['KW5 Vol'] = df_striking['Volume']
    df_striking.drop(['Keyword', 'Volume'], axis=1, inplace=True)

    # drop duplicate url rows
    df_striking.drop_duplicates(subset="URL", inplace=True)

    # replace nan values with empty strings
    df_striking = df_striking.fillna("")

    # drop the title, h1 and category description to lower case so kws can be matched to them
    df_striking["Title"] = df_striking["Title"].str.lower()
    df_striking["H1"] = df_striking["H1"].str.lower()
    df_striking["Copy"] = df_striking["Copy"].str.lower()

    # check whether a keyword appears in title, h1 or category description
    df_striking["KW1 in Title"] = df_striking.apply(lambda row: row["KW1"] in row["Title"], axis=1)
    df_striking["KW1 in H1"] = df_striking.apply(lambda row: row["KW1"] in row["H1"], axis=1)
    df_striking["KW1 in Copy"] = df_striking.apply(lambda row: row["KW1"] in row["Copy"], axis=1)
    df_striking["KW2 in Title"] = df_striking.apply(lambda row: row["KW2"] in row["Title"], axis=1)
    df_striking["KW2 in H1"] = df_striking.apply(lambda row: row["KW2"] in row["H1"], axis=1)
    df_striking["KW2 in Copy"] = df_striking.apply(lambda row: row["KW2"] in row["Copy"], axis=1)
    df_striking["KW3 in Title"] = df_striking.apply(lambda row: row["KW3"] in row["Title"], axis=1)
    df_striking["KW3 in H1"] = df_striking.apply(lambda row: row["KW3"] in row["H1"], axis=1)
    df_striking["KW3 in Copy"] = df_striking.apply(lambda row: row["KW3"] in row["Copy"], axis=1)
    df_striking["KW4 in Title"] = df_striking.apply(lambda row: row["KW4"] in row["Title"], axis=1)
    df_striking["KW4 in H1"] = df_striking.apply(lambda row: row["KW4"] in row["H1"], axis=1)
    df_striking["KW4 in Copy"] = df_striking.apply(lambda row: row["KW4"] in row["Copy"], axis=1)
    df_striking["KW5 in Title"] = df_striking.apply(lambda row: row["KW5"] in row["Title"], axis=1)
    df_striking["KW5 in H1"] = df_striking.apply(lambda row: row["KW5"] in row["H1"], axis=1)
    df_striking["KW5 in Copy"] = df_striking.apply(lambda row: row["KW5"] in row["Copy"], axis=1)

    # delete true / false values if there is no keyword
    df_striking.loc[df_striking["KW1"] == "", ["KW1 in Title", "KW1 in H1", "KW1 in Copy"]] = ""
    df_striking.loc[df_striking["KW2"] == "", ["KW2 in Title", "KW2 in H1", "KW2 in Copy"]] = ""
    df_striking.loc[df_striking["KW3"] == "", ["KW3 in Title", "KW3 in H1", "KW3 in Copy"]] = ""
    df_striking.loc[df_striking["KW4"] == "", ["KW4 in Title", "KW4 in H1", "KW4 in Copy"]] = ""
    df_striking.loc[df_striking["KW5"] == "", ["KW5 in Title", "KW5 in H1", "KW5 in Copy"]] = ""


    def true_dropper(col1, col2, col3):
        drop = df_striking.drop(
            df_striking[
                (df_striking[col1] == True)
                & (df_striking[col2] == True)
                & (df_striking[col3] == True)
                ].index
        )
        return drop


    if drop_all_true == True:
        df_striking = true_dropper("KW1 in Title", "KW1 in H1", "KW1 in Copy")
        df_striking = true_dropper("KW2 in Title", "KW2 in H1", "KW2 in Copy")
        df_striking = true_dropper("KW3 in Title", "KW3 in H1", "KW3 in Copy")
        df_striking = true_dropper("KW4 in Title", "KW4 in H1", "KW4 in Copy")
        df_striking = true_dropper("KW5 in Title", "KW5 in H1", "KW5 in Copy")

        del df_striking['Copy']

        st.markdown("### **🎈 Finished! Download Your Report!**")
        st.write("")


        def convert_df(df):  # IMPORTANT: Cache the conversion to prevent computation on every rerun
            return df.to_csv(index=False).encode('utf-8')


        csv = convert_df(df_striking)

        st.download_button(
            label="📥 Download your striking distance report!",
            data=csv,
            file_name='keywords_within_striking_distance.csv',
            mime='text/csv')
