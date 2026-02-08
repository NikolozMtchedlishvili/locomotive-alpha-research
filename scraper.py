import requests
import pandas as pd
from datetime import datetime, timedelta
import time


API_KEY = "YOUR_API_KEY"

QUERY = '"finance" OR "market" OR "stocks" OR "bond" OR "economy"'

SOURCES = "bloomberg,wsj,financial-times,cnbc,yahoo-finance"

# free-tier API of newsapi.org will only allow to scrape recent news. 
# to scrape recent news change START_DATE variable with START_DATE = datetime.today() - timedelta(days=30)
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime.today()

PAGE_SIZE = 100
MAX_PAGES = 5

all_articles = []

# Fetch articles

print(f"Fetching recent finance news ({START_DATE.strftime('%Y-%m-%d')} → {END_DATE.strftime('%Y-%m-%d')}) ...")

for page in range(1, MAX_PAGES + 1):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": QUERY,
        "sources": SOURCES,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": PAGE_SIZE,
        "page": page,
        "apiKey": API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data.get("status") != "ok":
        print("Error:", data)
        break

    articles = data.get("articles", [])
    if not articles:
        print("No more articles on this page.")
        break

    for a in articles:
        all_articles.append({
            "date": a.get("publishedAt"),
            "headline": a.get("title", ""),
            "description": a.get("description", ""),
            "source": a["source"]["name"],
            "url": a.get("url")
        })

    if len(articles) < PAGE_SIZE:
        break  
    time.sleep(1)  



df = pd.DataFrame(all_articles)

if df.empty:
    print("No articles fetched. Check API key or query.")
    exit()

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date","headline"])
df = df.drop_duplicates(subset=["headline","date"])
df = df.sort_values("date")

df.to_csv("news.csv", index=False)
print(f"Saved {len(df)} finance-relevant articles to news.csv")
