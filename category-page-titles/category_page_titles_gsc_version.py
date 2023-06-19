"""
Search Console Version - @LeeFootSEO - 19/06/2023

Find opportunities to optimise eCommerce category page titles.

What Does This Script Do?
----------------

This script splits out keywords in category page titles and checks to see how they are performing, and whether there
is opportunity for a better or additional keyword in the title.


How to Use:
----------------

1) Enter the domain to pull data from search console for. (NOTE: For domain properties use sc-domain - e.g sc-domain:example.com)
2) Point the script to your client
3) Crawl the same site using Screaming Frog and export the internal_html.csv report.
4) Update the script to read in the crawl file and pull the data from Search Console 

Setting Variables
----------------

1) delimiter - This is the character that separates keywords in the page title E.g. Keyword 1 | Keyword 2 would be a "|"
2) branding - Removes branded keywords - Set this exactly as it appears in the page title.
3) max_kw_suggestions - how many keywords to suggest (Default of 10 is fine and a sane default)
4) url_filter - This filters urls in the crawl file. e.g. /category/
5) country_filter filter on traffic from a specific country
6) rowcap - Restrict the number of results to be pulled from Search Console (Useful for very large sites!)

"""

import pandas as pd
import searchconsole  # pip3 install git+https://github.com/joshcarty/google-searchconsole

# set the variables
domain = "sc-domain:diy.com"
branding = "b&q"
# country_filter = 'gbr'
rowcap = 1_000_000
days = 90
max_kw_suggestions = 10
delimiter = "|"
url_filter = "category"
# import crawl file and rename columns
df = pd.read_csv('/python_scripts/internal_html.csv',
                 usecols=["Address", "Title 1", "Indexability"])

print("Domain is:", domain)
print("Delimiter is:", delimiter)
print("Pulling GSC data for the last:", days, "days")
print("URL Filter is set to:", url_filter)



df = df[df["Address"].str.contains(url_filter, na=False)]

df = df[["Address", "Title 1"]]
df.rename(columns={"Address": "page", "Title 1": "title"}, inplace=True)

# gsc import credentials
account = searchconsole.authenticate(
    client_config="/python_scripts/client_secrets.json",
    credentials="/python_scripts/credentials.json",
)

webproperty = account[domain]

# pull the data from gsc and filter on the data country
df_gsc = webproperty.query.range('today', days=-days).dimension('query', 'page', 'country').limit(rowcap).get().to_dataframe()  # with rowcap

# df_gsc = df_gsc[df_gsc["country"].str.contains(country_filter)].reset_index(drop=True)  # enable this to filter country specific traffic
df_gsc = df_gsc[~df_gsc["query"].str.contains(branding)].reset_index(drop=True)

df_gsc['kw_source'] = "gsc"
# drop any rows which are missing page titles and pages
df = df[df["title"].notna()]
df = df[df["page"].notna()]

# split the queries out of the page title
df = df.join(df['title'].str.split(delimiter, expand=True).add_prefix('title_'))

# creates a list to be exploded to a tall dataframe
df['query'] = df.to_numpy().tolist()
df = df.explode("query")

# checks whether the title and address are found in the tall dataframe and flags as True
df['title_equal'] = df['query'] == df['title']
df['page_equal'] = df['query'] == df['page']
df.to_csv("/python_scripts/test60.csv")

# True values are dropped along with the branding
df = df[~df["title_equal"].isin([True])]
df = df[~df["page_equal"].isin([True])]
df .to_csv("/python_scripts/test.csv")
df = df[~df["query"].str.contains(branding, na=False)]

# reindex, remove, whitespace, drop to lower case and remove nans
df = df[["query", "page", "title"]]
df['query'] = (df['query'].str.split()).str.join(' ')  # removes whitespace after delimiter split
df['query'] = df['query'].str.lower()
df = df[df["query"].notna()]  # drop nans from query column

# count the number of keywords in the page title and set the data source
df['kw_source'] = "page_title"
df['kws_in_title'] = df['page'].map(df.groupby('page')['page'].count())
df = df[~df["query"].str.contains(branding)].reset_index(drop=True)  # remove branding from page titles

# VLOOKUP gsc stats and create a dataframe for single keyword page titles
df_merged = pd.merge(df, df_gsc[['query', 'page', 'clicks']], on=['query', 'page'], how='left')
df_merged = pd.merge(df_merged, df_gsc[['query', 'page', 'impressions']], on=['query', 'page'], how='left')
df_merged = pd.merge(df_merged, df_gsc[['query', 'page', 'ctr']], on=['query', 'page'], how='left')
# df_single_kw_titles = df[df['kws_in_title'] == 1]  # make df of single keyword page titles

# reset the column order
cols = 'page', 'query', 'kw_source', 'clicks', 'impressions', 'ctr',
df_merged = df_merged.reindex(columns=cols)

# filter the gsc dataframe
df_gsc = df_gsc.reindex(columns=cols)
df_gsc = df_gsc[df_gsc["page"].str.contains(url_filter, na=False)]

# keep the top x keywords by clicks
df_gsc = df_gsc.sort_values(by="clicks", ascending=False)
df_gsc = df_gsc[df_gsc.clicks != 0]

df_gsc = df_gsc.groupby(['page']).head(max_kw_suggestions)

df_merged = pd.concat([df_merged, df_gsc])

# cleanup the formatting, fillna, round and drop branded queries
df_merged['ctr'] = df_merged['ctr'].round(2)
df_merged.fillna({"clicks": 0, "impressions": 0, "ctr": 0}, inplace=True)
df_merged.drop_duplicates(subset=["query", "page"], keep="first", inplace=True)
df_merged.sort_values(["page", "clicks"], ascending=[True, False], inplace=True)

# merge the page title back in
df_merged = pd.merge(df_merged, df[['page', 'title']], on='page', how='left')
df_merged.drop_duplicates(subset=["page", "query"], keep="first", inplace=True)  # drop dupes created at merge

df_merged = df_merged[df_merged["title"].notna()]

df_merged['total_clicks'] = df_merged.groupby('page')['clicks'].transform('sum')
df_merged['total_impressions'] = df_merged.groupby('page')['impressions'].transform('sum')

# export csvs
df_merged.to_csv("/python_scripts/page_title_refresh_output.csv", index=False)
