"""
Ahrefs Version - @LeeFootSEO - 19/06/2023

Find opportunities to optimise eCommerce category page titles.

What Does This Script Do?
----------------

This script splits out keywords in category page titles and checks to see how they are performing, and whether there
is opportunity for a better or additional keyword in the title.

Note and Caveats
----------------

This version works with an ahrefs keyword export, the recommended version uses the Search Console API. This version
was written to showcase demo data but is still useful. For example, pitch decks when you don't have Search Console 
access etc. 

How to Use:
----------------

1) Export all keywords a site is ranking for (Make sure to disable the report comparison option, or rename the columns in the script).
2) Crawl the same site using Screaming Frog and export the internal_html.csv report.
3) Point the script to read in the both files

Setting Variables
----------------

1) delimiter - This is the character that separates keywords in the page title E.g. Keyword 1 | Keyword 2 would be a "|"
2) branding - Removes branded keywords - Set this exactly as it appears in the page title.
3) max_kw_suggestions - how many keywords to suggest (Default of 10 is fine and a sane default)
4) url_filter - This filters urls in the crawl file. e.g. /category/

"""

import pandas as pd

# set the variables
delimiter = "|"
branding = "b&q"
max_kw_suggestions = 10
url_filter = ".cat"

print("Delimiter is:", delimiter)
print("URL Filter is set to:", url_filter)

# import crawl file and rename columns
df = pd.read_csv('/python_scripts/page_title_ecom_ahrefs/internal_html.csv',
                 usecols=["Address", "Title 1", "Indexability"], dtype="str")

df = df[df["Address"].str.contains(url_filter, na=False)]

df = df[["Address", "Title 1"]]

df.rename(columns={"Address": "Current URL", "Title 1": "title"}, inplace=True)

# import data from ahrefs organic keyword export
df_kws = pd.read_csv('/python_scripts/page_title_ecom_ahrefs/ahrefs.csv', dtype="str")

df_kws = df_kws[~df_kws["Keyword"].str.contains(branding)].reset_index(drop=True)

df_kws['kw_source'] = "Keyword Import"

# drop any rows which are missing Current URL titles and Current URLs
df = df[df["title"].notna()]
df = df[df["Current URL"].notna()]

# split the queries out of the Current URL title
df = df.join(df['title'].str.split(delimiter, expand=True).add_prefix('title_'))

# creates a list to be exploded to a tall dataframe
df['Keyword'] = df.to_numpy().tolist()
df = df.explode("Keyword")

# checks whether the title and address are found in the tall dataframe and flags as True
df['title_equal'] = df['Keyword'] == df['title']
df['Current URL_equal'] = df['Keyword'] == df['Current URL']

# True values are dropped along with the branding
df = df[~df["title_equal"].isin([True])]
df = df[~df["Current URL_equal"].isin([True])]

df = df[df["Keyword"].notna()]
df = df[~df["Keyword"].str.contains(branding, na=False)]

# reindex, remove, whitespace, drop to lower case and remove nans
df = df[["Keyword", "Current URL", "title"]]
df['Keyword'] = (df['Keyword'].str.split()).str.join(' ')  # removes whitespace after delimiter split
df['Keyword'] = df['Keyword'].str.lower()
df = df[df["Keyword"].notna()]  # drop nans from Keyword column

# count the number of keywords in the Current URL title and set the data source
df['kw_source'] = "current_page_title"
df['kws_in_title'] = df['Current URL'].map(df.groupby('Current URL')['Current URL'].count())
df = df[~df["Keyword"].str.contains(branding)].reset_index(drop=True)  # remove branding from Current URL titles

# VLOOKUP gsc stats and create a dataframe for single keyword Current URL titles
df_merged = pd.merge(df, df_kws[['Keyword', 'Current URL', 'Organic traffic']], on=['Keyword', 'Current URL'], how='left')
df_merged = pd.merge(df_merged, df_kws[['Keyword', 'Current URL', 'Volume']], on=['Keyword', 'Current URL'], how='left')

# reset the column order
cols = 'Current URL', 'Keyword', 'kw_source', 'Organic traffic', 'Volume'
df_merged = df_merged.reindex(columns=cols)

# filter the gsc dataframe
df_kws = df_kws.reindex(columns=cols)
df_kws = df_kws[df_kws["Current URL"].str.contains(url_filter, na=False)]

# keep the top x keywords by Organic traffic
df_kws = df_kws.sort_values(by="Organic traffic", ascending=False)
df_kws = df_kws.groupby(['Current URL']).head(max_kw_suggestions)

df_merged = pd.concat([df_merged, df_kws])

# cleanup the formatting, fillna, round and drop branded queries
df_merged.fillna({"Organic traffic": 0, "Volume": 0}, inplace=True)
df_merged.drop_duplicates(subset=["Keyword", "Current URL"], keep="first", inplace=True)
df_merged.sort_values(["Current URL", "Organic traffic"], ascending=[True, False], inplace=True)

# merge the Current URL title back in
df_merged = pd.merge(df_merged, df[['Current URL', 'title']], on='Current URL', how='left')
df_merged.drop_duplicates(subset=["Current URL", "Keyword"], keep="first", inplace=True)  # drop dupes created at merge

df_merged = df_merged[df_merged["title"].notna()]
df_merged['Organic traffic'] = pd.to_numeric(df_merged['Organic traffic'], errors='coerce')
df_merged['Volume'] = pd.to_numeric(df_merged['Volume'], errors='coerce')

df_merged['total_organic traffic'] = df_merged.groupby('Current URL')['Organic traffic'].transform('sum')
df_merged['total_volume'] = df_merged.groupby('Current URL')['Volume'].transform('sum')

# export csvs
df_merged.to_csv("/python_scripts/page_title_refresh.csv", index=False)
