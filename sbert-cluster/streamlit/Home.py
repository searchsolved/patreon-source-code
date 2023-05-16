import streamlit as st

st.set_page_config(
    page_title="Keyword Clustering App - Beta 3",
    page_icon="🌠",
)

st.write("# Keyword Clustering App - Beta 3")

st.sidebar.success("Select a page above.")

st.markdown(
    """
	Uses sentence transformers for semantic clustering.

    **👈 Select a page from the sidebar** to get started!
"""
)
