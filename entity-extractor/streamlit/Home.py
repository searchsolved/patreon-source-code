import streamlit as st

st.set_page_config(
    page_title="Entity Extraction App - Beta 3",
    page_icon="🌠",
)

st.write("# Entity Extraction App - Beta 3")

st.sidebar.success("Select a page above.")

st.markdown(
    """
    This app uses the [dandelion.eu API](https://dandelion.eu/) to extract entities from the live SERPS
    a keyword export from SEMRush / Ahrefs etc or a Youtube URL.

    If scraping the live serps, you will need a [ValueSERP API Key](https://www.valueserp.com/pricing).
    They offer PAYG pricing with no expiration date. (A lot of my other scripts use this API too).
    
    If you just want to use this to process keyword export files, then there is no cost unless you want to increase
    from the 1,000 free entity searches per day.

    **👈 Select a page from the sidebar** to get started!
"""
)
