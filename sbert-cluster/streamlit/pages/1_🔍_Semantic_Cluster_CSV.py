import streamlit as st
from sentence_transformers import SentenceTransformer, util
import time
import chardet
import pandas as pd
from nltk import ngrams

from polyfuzz import PolyFuzz
from polyfuzz.models import SentenceEmbeddings

# The code below is for the layout of the page
if "widen" not in st.session_state:
    layout = "centered"
else:
    layout = "wide" if st.session_state.widen else "centered"

# region format
st.set_page_config(page_title="Semantic Keyword Clustering Tool - Patreon Beta 3", page_icon="✨", layout=layout)

beta_limit = 15000
st.write("Web App Limited to First 15,000 Rows - Run Locally for More!")
st.title("Semantic Keyword Clustering Tool - Patreon Beta 21022023")
device = "cpu"

st.checkbox(
    "Widen layout",
    key="widen",
    help="Tick this box to change the layout to 'wide' mode",
)
st.caption("")

with st.form("my_form"):
    st.caption("")

    cols, col1, cole = st.columns([0.05, 1, 0.05])

    with col1:
        st.markdown("##### ① Upload your keyword report")

    cols, col1, cole = st.columns([0.2, 1, 0.2])

    with col1:
        uploaded_file = st.file_uploader(
            "CSV File in UTF-8 Format",
            help="""
    Which reports does the tool currently support?
    -   Input file must have a column named 'keyword'
    """,
        )

    cols, col1, cole = st.columns([0.2, 1, 0.2])

    st.markdown("")

    with st.expander("Advanced settings", expanded=True):
        st.markdown("")

        cols, col1, cole = st.columns([0.001, 1, 0.001])

        with col1:
            st.markdown("##### ② Pick Your Transformer Model")

        cols, col1, cole = st.columns([0.05, 1, 0.05])

        with col1:
            model_radio_button = st.radio(
                "Transformer model",
                [
                    "all-MiniLM-L6-v2",
                    "multi-qa-mpnet-base-dot-v1",
                    "paraphrase-multilingual-MiniLM-L12-v2",

                ],
                help="""all-MiniLM-L6-v2 - is the best balanced transformer model (Semantic score Vs Speed). 
                multi-qa-mpnet-base-dot-v1 - is the highest scoring semantic transformer - but is very slow.
                paraphrase-multilingual-MiniLM-L12-v2 - use this one for multi-lingual datasets""",
            )

        cols, col1, cole = st.columns([0.2, 1, 0.2])

        with col1:
            st.markdown("***")

        cols, col1, cole = st.columns([0.001, 1, 0.001])

        with col1:
            st.write(
                "##### ③ Configure Your Cluster Settings",
                help="here you can configure the clustering settings",
            )

        st.caption("")

        # Three different columns:
        cols, col1, col2, cole = st.columns([0.1, 1, 1, 0.1])

        # You can also use "with" notation:
        with col1:
            accuracy_slide = st.slider(
                "Cluster accuracy: 0-100",
                value=85,
                help="the accuracy of the clusters",
            )

        with col2:
            min_cluster_size = st.slider(
                "Minimum Cluster size: 0-100",
                value=2,min_value=2,
                help="the minimum size of the clusters",
            )

        st.caption("")

        min_similarity = accuracy_slide / 100

        with col1:
            st.write("")
            remove_dupes = st.checkbox("Remove duplicate keywords?", value=True)

    st.write("")

    # Every form must have a submit button.
    submitted = st.form_submit_button("Submit")

@st.cache_resource
def get_model():
    model = SentenceTransformer(model_radio_button)

    return model

model = get_model()

if uploaded_file is not None:

    try:

        result = chardet.detect(uploaded_file.getvalue())
        encoding_value = result["encoding"]

        if encoding_value == "UTF-16":
            white_space = True
        else:
            white_space = False

        df = pd.read_csv(
            uploaded_file,
            encoding=encoding_value,
            delim_whitespace=white_space,
            on_bad_lines='skip',
            nrows=beta_limit,
        )

        number_of_rows = len(df)

        if number_of_rows > beta_limit:
            df = df[:beta_limit]
            st.caption(
                "🚨 Imported rows over the beta limit, limiting to first "
                + str(beta_limit)
                + " rows."
            )

        if number_of_rows == 0:
            st.caption("Your sheet seems empty!")
    except UnicodeDecodeError:
        st.warning(
            """
            🚨 The file doesn't seem to load. Check the filetype, file format and Schema

            """
        )

else:
    st.stop()

with st.form(key="columns_in_form_2"):
    # Three different columns:
    cols, col1, col2, cole = st.columns([0.05, 1, 1, 0.05])

    with col1:

        st.subheader("")
        st.caption("")
        st.markdown("##### ④ Select the column to cluster 👉")

    with col2:
        kw_col = st.selectbox("", df.columns)
    st.write("")

    cols, col1, cole = st.columns([0.0025, 1, 0.03])

    with col1:
        with st.expander("View imported data (pre-clustering)", expanded=False):
            st.write(df)

    st.caption("")

    submitted = st.form_submit_button("Submit")
    df.rename(columns={kw_col: 'keyword', "spoke": "spoke Old"}, inplace=True)

# store the data
cluster_name_list = []
corpus_sentences_list = []
df_all = []

if submitted:
    if remove_dupes:
        df.drop_duplicates(subset='keyword', inplace=True)

if submitted == True:

    if remove_dupes:
        df.drop_duplicates(subset='keyword', inplace=True)

    startTime = time.time()  # start timing the script
    st.info("Clustering keywords. This may take a while!")

    df = df[df["keyword"].notna()]
    df['keyword'] = df['keyword'].astype(str)
    from_list = df['keyword'].to_list()

    @st.cache_resource
    def get_model():
        embedding_model = SentenceTransformer(model_radio_button, device=device)

        return embedding_model

    embedding_model = get_model()
    distance_model = SentenceEmbeddings(embedding_model)

    model = PolyFuzz(distance_model)
    model = model.fit(from_list)
    model.group(link_min_similarity=min_similarity)

    df_cluster = model.get_matches()

    # rename to merge vlookup style
    df_cluster.rename(columns={"From": "keyword", "Similarity": "similarity", "Group": "cluster"}, inplace=True)
    df = pd.merge(df, df_cluster[['keyword', 'cluster']], on='keyword', how='left')

    # calculate no_clusters --------------------------------------------------------------------------------------------

    df['cluster_size'] = df['cluster'].map(df.groupby('cluster')['cluster'].count())
    df.loc[df["cluster_size"] == 1, "cluster"] = "no_cluster"
    df.insert(0, 'cluster', df.pop('cluster'))  # pop the cluster column to the front
    df['cluster'] = df['cluster'].str.encode('ascii', 'ignore').str.decode('ascii')


    # ----------------------------------------------------------- rename clusters to the shortest keyword in the cluster

    df['keyword_len'] = df['keyword'].astype(str).apply(len)
    df = df.sort_values(by="keyword_len", ascending=True)
    df['serp_cluster'] = df.groupby('cluster')['keyword'].transform('first')

    df.insert(0, 'cluster', df.pop('cluster'))
    df.insert(1, 'keyword', df.pop('keyword'))
    df.insert(3, 'cluster_size', df.pop('cluster_size'))

    # ------------------------------------------------------------------------------clean and sort columns before export

    df.sort_values(["cluster", "cluster_size"], ascending=[True, False], inplace=True)
    df['cluster'] = (df['cluster'].str.split()).str.join(' ')
    del df['cluster_size']

    # ------------------------------------------------------------------------------------------------ download csv file

    st.success(
        "All keywords clustered successfully. Took {0} seconds!".format(
            time.time() - startTime
        )
    )

    @st.cache_data
    def convert_df(df):
        return df.to_csv(index=False).encode("utf-8")

    # download results
    st.markdown("### **🎈 Download a CSV Export!**")
    st.write("")
    csv = convert_df(df)
    st.download_button(
        label="📥 Download your report!",
        data=csv,
        file_name="your_keywords_clustered.csv",
        mime="text/csv",
    )
