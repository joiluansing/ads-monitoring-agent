import requests
import json
from datetime import date, timedelta

ACCESS_TOKEN = "30d4777968406ecabd9da3b6636531c1f01dbc9e"
ADVERTISER_ID = "7475226930304794640"
STORE_ID = "7494967026872191592"
ROI_THRESHOLD = 5
LARK_WEBHOOK = os.environ.get("LARK_WEBHOOK")

headers = {"Access-Token": ACCESS_TOKEN}
today = date.today().strftime("%Y-%m-%d")
yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
seven_days_ago = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")

# Step 1: Active campaigns
campaign_names = {}
for promo_type in ["PRODUCT_GMV_MAX", "LIVE_GMV_MAX"]:
    for page in range(1, 4):
        r = requests.get(
            "https://business-api.tiktok.com/open_api/v1.3/gmv_max/campaign/get/",
            headers=headers,
            params={
                "advertiser_id": ADVERTISER_ID,
                "filtering": json.dumps({"gmv_max_promotion_types": [promo_type]}),
                "page": page,
                "page_size": 20
            }
        )
        data = r.json().get("data", {}).get("list", [])
        if not data:
            break
        for c in data:
            if c.get("operation_status") == "ENABLE" and c.get("secondary_status") == "CAMPAIGN_STATUS_ENABLE":
                campaign_names[c["campaign_id"]] = c["campaign_name"]

# Step 2: Fetch summary
def get_summary(start, end):
    r = requests.get(
        "https://business-api.tiktok.com/open_api/v1.3/gmv_max/report/get/",
        headers=headers,
        params={
            "advertiser_id": ADVERTISER_ID,
            "store_ids": json.dumps([STORE_ID]),
            "start_date": start,
            "end_date": end,
            "dimensions": json.dumps(["campaign_id"]),
            "metrics": json.dumps(["cost", "gross_revenue", "roi"]),
            "page": 1,
            "page_size": 50
        }
    )
    items = r.json().get("data", {}).get("list", [])
    total_cost = sum(float(i["metrics"]["cost"]) for i in items)
    total_revenue = sum(float(i["metrics"]["gross_revenue"]) for i in items)
    roi = round(total_revenue / total_cost, 2) if total_cost > 0 else 0
    return total_cost, total_revenue, roi, items

today_cost, today_rev, today_roi, today_items = get_summary(today, today)
yest_cost, yest_rev, yest_roi, _ = get_summary(yesterday, yesterday)
week_cost, week_rev, week_roi, _ = get_summary(seven_days_ago, today)

# Step 3: Build alerts
alerts = []
for item in today_items:
    cid = item["dimensions"]["campaign_id"]
    if cid not in campaign_names:
        continue
    name = campaign_names[cid]
    cost = float(item["metrics"]["cost"])
    roi = float(item["metrics"]["roi"])
    if cost > 0 and roi < ROI_THRESHOLD:
        alerts.append(f"⚠️ {name} — ROI: {roi}")

# Step 4: Build campaign breakdown
breakdown = []
for item in today_items:
    cid = item["dimensions"]["campaign_id"]
    if cid not in campaign_names:
        continue
    name = campaign_names[cid]
    cost = float(item["metrics"]["cost"])
    revenue = float(item["metrics"]["gross_revenue"])
    roi = float(item["metrics"]["roi"])
    if cost > 0:
        icon = "⚠️" if roi < ROI_THRESHOLD else "✅"
        breakdown.append(f"{icon} {name}\n   Cost: ₱{cost:,.2f} | Revenue: ₱{revenue:,.2f} | ROI: {roi}")

# Step 5: Build message
alert_text = "\n".join(alerts) if alerts else "✅ All campaigns performing well!"
breakdown_text = "\n\n".join(breakdown)

message = f"""📊 NewMoon GMV Max Report
📅 {today}

🗓 TODAY
Cost: ₱{today_cost:,.2f}
Gross Revenue: ₱{today_rev:,.2f}
ROI: {today_roi}

🗓 YESTERDAY
Cost: ₱{yest_cost:,.2f}
Gross Revenue: ₱{yest_rev:,.2f}
ROI: {yest_roi}

📆 LAST 7 DAYS
Cost: ₱{week_cost:,.2f}
Gross Revenue: ₱{week_rev:,.2f}
ROI: {week_roi}

⚠️ ALERTS
{alert_text}

📊 CAMPAIGN BREAKDOWN (Today)
{breakdown_text}"""

# Step 6: Send to Lark
r = requests.post(LARK_WEBHOOK, json={
    "msg_type": "text",
    "content": {"text": message}
})
print("Lark response:", r.json())
print("\n--- MESSAGE PREVIEW ---")
print(message)
