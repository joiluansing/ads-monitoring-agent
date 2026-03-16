import requests
import os

ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN")

advertisers = [
    {"name": "Newmoon", "id": "7475226930304794640"}
]

url = "https://business-api.tiktok.com/open_api/v1.3/report/integrated/get/"

for adv in advertisers:

    headers = {
        "Access-Token": ACCESS_TOKEN
    }

    params = {
        "advertiser_id": adv["id"],
        "report_type": "BASIC",
        "data_level": "CAMPAIGN",
        "dimensions": ["campaign_name"],
        "metrics": ["spend","impressions","clicks"],
        "page": 1,
        "page_size": 50
    }

    response = requests.get(url, headers=headers, params=params)

    print("Checking account:", adv["name"])
    print(response.json())
