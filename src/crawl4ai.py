from serpapi import GoogleSearch

params = {
  "engine": "google_trends",
  "q": "coffee,milk,bread,pasta,steak",
  "data_type": "TIMESERIES",
  "api_key": "f6a5fad91ad00a424888561941d8232426fcedf2bb3af3f30ae19577a3c14a45"
}

search = GoogleSearch(params)
results = search.get_dict()
interest_over_time = results["interest_over_time"]