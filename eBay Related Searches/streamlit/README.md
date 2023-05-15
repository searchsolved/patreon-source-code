eBay Related Search Scraper
This Python code implements a web scraping tool to retrieve related search keywords from eBay. It provides a user-friendly web interface using the Streamlit library. The scraper allows you to search for related keywords on eBay and visualize the results in an interactive tree format.

Usage
Install the required dependencies listed in the requirements.txt file by running the following command:

Copy code
pip install -r requirements.txt
Run the Python script using the following command:

arduino
Copy code
streamlit run scraper.py
The Streamlit app will launch in your default web browser.

Enter the keyword you want to search for on eBay in the text input field.

Select the country code top-level domain (ccTLD) from the dropdown menu to specify the country.

Click the "Submit" button to start the scraping process.

Wait for the scraper to retrieve the related search keywords from eBay. The progress will be displayed.

Once the scraping is complete, an interactive tree visualization of the related search keywords will be displayed.

To download the scraped data as a CSV file, click the "Download your report!" button.

requirements.txt:

makefile
Copy code
streamlit==0.84.1
streamlit_echarts==0.1.1
stqdm==0.2.2
pandas==1.3.0
beautifulsoup4==4.9.3
requests==2.26.0
user_agent2==2.3.0
To install the dependencies, run the following command:

Copy code
pip install -r requirements.txt
Make sure to have the correct Python environment activated before installing the dependencies.

Note: It's recommended to use a virtual environment to keep the project dependencies isolated.