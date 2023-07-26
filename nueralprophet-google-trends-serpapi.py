from serpapi import GoogleSearch
from neuralprophet import NeuralProphet
import pandas as pd
import datetime

params = {
  "engine": "google_trends",
  "q": "coffee",
  "data_type": "TIMESERIES",
  "api_key": "YOUR KEY HERE",
  "geo": "US",
  "date": "today 5-y"
}

search = GoogleSearch(params)
results = search.get_dict()
print(results)
interest_over_time = results["interest_over_time"]

# Extract timestamps and corresponding values into separate lists
timestamps = [item['timestamp'] for item in interest_over_time['timeline_data']]
values = [item['values'][0]['extracted_value'] for item in interest_over_time['timeline_data']]

# Convert timestamps to datetime objects
dates = [datetime.datetime.fromtimestamp(int(ts)) for ts in timestamps]

# Create a DataFrame suitable for NeuralProphet
df = pd.DataFrame({'ds': dates, 'y': values})

# Instantiate and fit the model
model = NeuralProphet()
model.fit(df, freq='W')

# Make future predictions
future = model.make_future_dataframe(df, periods=30, n_historic_predictions=True)  # adjust periods as necessary
forecast = model.predict(future)

# Rename the columns
forecast.rename(columns={'ds': 'date', 'y': 'actual', 'yhat1': 'predicted'}, inplace=True)

# Keep only the three columns and remove the rest
forecast = forecast[['date', 'actual', 'predicted']]

print(forecast)
forecast.to_csv("/python_scripts/test.csv", index=False)
