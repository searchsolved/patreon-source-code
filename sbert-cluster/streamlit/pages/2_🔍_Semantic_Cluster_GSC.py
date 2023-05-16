import searchconsole
import streamlit as st
from apiclient import discovery
from google_auth_oauthlib.flow import Flow
from streamlit_elements import Elements  # streamlit-elements==0.0.2
import time
from nltk import ngrams
import pandas as pd
from polyfuzz import PolyFuzz
from polyfuzz.models import SentenceEmbeddings
from sentence_transformers import SentenceTransformer
import numpy as np
import plotly.express as px
from io import BytesIO


st.set_page_config(layout="wide", page_title="Semantic Keyword Cluster v3", page_icon="🔌")

device = "cpu"  # valid options are cuda or cpu

# flow control
gsc_ran = False
submit_fetch_data = False

# row limit
RowCap = 15000

# Convert secrets from the TOML file to strings
clientSecret = str(st.secrets["installed"]["client_secret"])
clientId = str(st.secrets["installed"]["client_id"])
#redirectUri = "http://localhost:8501"
redirectUri = "https://cluster.streamlit.app/Semantic_Cluster_GSC"

if "my_token_input" not in st.session_state:
    st.session_state["my_token_input"] = ""

if "my_token_received" not in st.session_state:
    st.session_state["my_token_received"] = False


def charly_form_callback():
    st.session_state.my_token_received = True
    code = st.experimental_get_query_params()["code"][0]
    st.session_state.my_token_input = code


with st.sidebar.form(key="my_form"):
    st.markdown("")
    mt = Elements()

    mt.button(
        "Sign-in with Google",
        target="_blank",
        size="large",
        variant="contained",
        start_icon=mt.icons.exit_to_app,
        onclick="none",
        style={"color": "#FFFFFF", "background": "#FF4B4B"},
        href="https://accounts.google.com/o/oauth2/auth?response_type=code&client_id="
             + clientId
             + "&redirect_uri="
             + redirectUri
             + "&scope=https://www.googleapis.com/auth/webmasters.readonly&access_type=offline&prompt=consent",
    )

    mt.show(key="687")

    credentials = {
        "installed": {
            "client_id": clientId,
            "client_secret": clientSecret,
            "redirect_uris": [],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://accounts.google.com/o/oauth2/token",
        }
    }

    flow = Flow.from_client_config(
        credentials,
        scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
        redirect_uri=redirectUri,
    )

    auth_url, _ = flow.authorization_url(prompt="consent")

    # set variables
    model_radio_button = st.sidebar.radio(
        "Transformer model",
        [

            "all-MiniLM-L6-v2",
            "multi-qa-mpnet-base-dot-v1",
            "paraphrase-multilingual-MiniLM-L12-v2",
            
        ],
        help="the model to use for the clustering",
    )

    accuracy_slide = st.sidebar.slider(
        "Cluster accuracy: 0-100",
        value=75,
        help="the accuracy of the clusters",
    )

    st.caption("")
    min_similarity = accuracy_slide / 100

    st.write("")

    submit_account = st.form_submit_button(
        label="Access GSC API", on_click=charly_form_callback
    )

    with st.expander("How to access your GSC data?"):
        st.markdown(
            """
        1. Click on the `Sign-in with Google` button
        2. You will be redirected to the Google Oauth screen
        3. Choose the Google account you want to use & click `Continue`
        5. You will be redirected back to this app.
        6. Click on the "Access GSC API" button.
        7. Voilà! 🙌 
        """
        )
        st.write("")

    with st.expander("Check your Oauth token"):
        code = st.text_input(
            "",
            key="my_token_input",
            label_visibility="collapsed",
        )

    st.write("")

container3 = st.sidebar.container()

st.sidebar.write("")

st.sidebar.caption("GSC Connector by [Charly Wargnier](https://www.charlywargnier.com/).")
try:
    if st.session_state.my_token_received == False:
        with st.form(key="my_form2"):

            webpropertiesNEW = st.text_input(
                "Web property to review (please sign in via Google OAuth first)",
                value="",
                disabled=True,
            )

            filename = webpropertiesNEW.replace("https://www.", "")
            filename = filename.replace("http://www.", "")
            filename = filename.replace(".", "")
            filename = filename.replace("/", "")

            st.write("")

            col1, col2 = st.columns(2)

            with col1:
                search_type = st.selectbox(
                    "Search type",
                    ("web", "video", "image", "news", "googleNews"),
                    help="""
                    Specify the search type you want to retrieve
                    -   **Web**: Results that appear in the All tab. This includes any image or video results shown in the All results tab.
                    -   **Image**: Results that appear in the Images search results tab.
                    -   **Video**: Results that appear in the Videos search results tab.
                    -   **News**: Results that show in the News search results tab.

                    """,
                )

            with col2:
                timescale = st.selectbox(
                    "Date range",
                    (
                        "Last 7 days",
                        "Last 30 days",
                        "Last 3 months",
                        "Last 6 months",
                        "Last 12 months",
                        "Last 16 months",
                    ),
                    index=0,
                    help="Specify the date range",
                )

                if timescale == "Last 7 days":
                    timescale = -7
                elif timescale == "Last 30 days":
                    timescale = -30
                elif timescale == "Last 3 months":
                    timescale = -91
                elif timescale == "Last 6 months":
                    timescale = -182
                elif timescale == "Last 12 months":
                    timescale = -365
                elif timescale == "Last 16 months":
                    timescale = -486

            st.write("")

            submit_button = st.form_submit_button(label="Fetch GSC API data", on_click=charly_form_callback)

    if st.session_state.my_token_received == True:

        @st.experimental_singleton
        def get_account_site_list_and_webproperty(token):
            flow.fetch_token(code=token)
            credentials = flow.credentials
            service = discovery.build(
                serviceName="webmasters",
                version="v3",
                credentials=credentials,
                cache_discovery=False,
            )

            account = searchconsole.account.Account(service, credentials)
            site_list = service.sites().list().execute()
            return account, site_list


        account, site_list = get_account_site_list_and_webproperty(
            st.session_state.my_token_input
        )

        first_value = list(site_list.values())[0]

        lst = []
        for dicts in first_value:
            a = dicts.get("siteUrl")
            lst.append(a)

        if lst:

            container3.info("✔️ GSC credentials OK!")

            with st.form(key="my_form2"):

                webpropertiesNEW = st.selectbox("Select web property", lst)

                col1, col2 = st.columns(2)

                with col1:
                    search_type = st.selectbox(
                        "Search type",
                        ("web", "news", "video", "googleNews", "image"),
                        help="""
                    Specify the search type you want to retrieve
                    -   **Web**: Results that appear in the All tab. This includes any image or video results shown in the All results tab.
                    -   **Image**: Results that appear in the Images search results tab.
                    -   **Video**: Results that appear in the Videos search results tab.
                    -   **News**: Results that show in the News search results tab.

                    """,
                    )

                with col2:
                    timescale = st.selectbox(
                        "Date range",
                        (
                            "Last 7 days",
                            "Last 30 days",
                            "Last 3 months",
                            "Last 6 months",
                            "Last 12 months",
                            "Last 16 months",
                        ),
                        index=0,
                        help="Specify the date range",
                    )

                    if timescale == "Last 7 days":
                        timescale = -7
                    elif timescale == "Last 30 days":
                        timescale = -30
                    elif timescale == "Last 3 months":
                        timescale = -91
                    elif timescale == "Last 6 months":
                        timescale = -182
                    elif timescale == "Last 12 months":
                        timescale = -365
                    elif timescale == "Last 16 months":
                        timescale = -486

                st.write("")

                submit_fetch_data = st.form_submit_button(label="Fetch GSC API data", on_click=charly_form_callback)

        if submit_fetch_data:
            webproperty = account[webpropertiesNEW]

            gsc_data = (
                webproperty.query.range("today", days=timescale)
                    .dimension(
                    "query",
                    "page",
                )
                    .limit(RowCap)
                    .get()
            )

            df = pd.DataFrame(gsc_data)

            st.info("Data Pulled Successfully from GSC!")
            gsc_ran = True

except ValueError as ve:

    st.warning("⚠️ You need to sign in to your Google account first!")

except IndexError:
    st.info(
        "⛔ It seems you haven’t correctly configured Google Search Console! Click [here]("
        "https://support.google.com/webmasters/answer/9008080?hl=en) for more information on how to get started! "
    )

 # start clustering ----------------------------------------------------------------------------------------------------

if gsc_ran == True:

    startTime = time.time()  # start timing the script
    st.info("Clustering keywords. This may take a while!")
    from_list = df['query'].to_list()


    @st.cache_resource
    def get_model():
        embedding_model = SentenceTransformer(model_radio_button, device=device)

        return embedding_model


    embedding_model = get_model()
    distance_model = SentenceEmbeddings(embedding_model)

    model = PolyFuzz(distance_model)
    model = model.fit(from_list)
    model.group(link_min_similarity=0.65)

    df_cluster = model.get_matches()

    df = pd.merge(df, df_cluster, left_index=True, right_index=True)
    del df['query']
    df.rename(columns={'Group': 'spoke', 'From': 'query'}, inplace=True)

    # create uni-grams for each cluster to be used as the parent_topic -------------------------------------------------

    df_unigram = (
        df.assign(
            query=[[" ".join(x) for x in ngrams(s.split(), n=1)] for s in df["query"]]
        )
            .explode("query")
            .groupby("spoke")["query"]
            .apply(lambda g: g.mode())
            .reset_index(name="hub")
    )

    df = df.merge(df_unigram.drop_duplicates('spoke'), how='left', on="spoke")

    df_bigram = (
        df.assign(
            query=[[" ".join(x) for x in ngrams(s.split(), n=2)] for s in df["query"]]
        )
            .explode("query")
            .groupby("spoke")["query"]
            .apply(lambda g: g.mode())
            .reset_index(name="bigrams")
    )

    df = df.merge(df_bigram.drop_duplicates('spoke'), how='left', on="spoke")
    df['spoke'] = df['bigrams']

    # calculate no_clusters --------------------------------------------------------------------------------------------

    df['hub'] = df['hub'].fillna("no_cluster")
    df['spoke'] = df['spoke'].fillna("no_cluster")
    df['cluster_size'] = df['spoke'].map(df.groupby('spoke')['spoke'].count())
    df.loc[df["cluster_size"] == 1, "spoke"] = "no_cluster"

    df.loc[df["spoke"] == "no_cluster", "hub"] = "no_cluster"
    df['spoke'] = df['spoke'].replace(to_replace=r'^&\s', value='', regex=True)  # cluster names that start with "& "
    df[['ctr', 'position']] = df[['ctr', 'position']].apply(lambda x: pd.Series.round(x, 2))
    df = df[["hub", "spoke", "query", "page", "clicks", "impressions", "ctr", "position", "cluster_size"]]
    st.success("All keywords clustered successfully. Took {0} seconds!".format(time.time() - startTime))
    
    @st.cache_data
    def convert_df(df):
        return df.to_csv(index=False).encode("utf-8")

    st.markdown("### **🎈 Download a CSV Export!**")
    st.write("")
    csv = convert_df(df)
    st.download_button(
        label="📥 Download your report!",
        data=csv,
        file_name="your_keywords_clustered.csv",
        mime="text/csv",
    )
    # create sunburst plot ---------------------------------------------------------------------------------------------

    fig = px.sunburst(df, path=[px.Constant("Semantic Clusters"), "hub", "spoke"], values='clicks', color_discrete_sequence=px.colors.qualitative.Pastel2)
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)
    fig.show()
