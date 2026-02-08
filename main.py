import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Load S&P 500
print("Downloading S&P 500 data...")
sp500 = yf.download("^GSPC", start="2023-01-01", progress=False)

# Fix multi-level columns
if isinstance(sp500.columns, pd.MultiIndex):
    sp500.columns = sp500.columns.get_level_values(0)

sp500.reset_index(inplace=True)

# Convert to date-only
sp500["Date"] = pd.to_datetime(sp500["Date"]).dt.date

# Load VIX
print("Downloading VIX data...")
vix = yf.download("^VIX", start="2023-01-01", progress=False)

if isinstance(vix.columns, pd.MultiIndex):
    vix.columns = vix.columns.get_level_values(0)

vix.reset_index(inplace=True)
vix["Date"] = pd.to_datetime(vix["Date"]).dt.date

# Load news from CSV 
print("Loading news.csv...")
try:
    # skipinitialspace=True fixes errors if there are spaces after commas
    news_events = pd.read_csv("news.csv", skipinitialspace=True)

    # 1. Force column names to lower case and strip spaces (handles " Date" vs "date")
    news_events.columns = news_events.columns.str.lower().str.strip()

    # 2. Convert date column to string and strip whitespace
    news_events["date"] = news_events["date"].astype(str).str.strip()

    # 3. Convert to datetime objects using specific format
    news_events["date"] = pd.to_datetime(news_events["date"], format="%Y-%m-%d", errors="coerce").dt.date

    # 4. Drop invalid rows
    news_events = news_events.dropna(subset=["date", "headline"])

    print(f"Successfully loaded {len(news_events)} news events.")

except Exception as e:
    print(f"Error loading CSV: {e}")
    news_events = pd.DataFrame(columns=["date", "headline", "description", "source", "url"])

# Align news dates to nearest trading day
if not news_events.empty:
    def nearest_trading_day(d, trading_days):
        trading_days = pd.Series(trading_days)
        delta = (trading_days - d).abs()
        return trading_days.iloc[delta.argmin()]

    # Apply function to find nearest trading day for plotting
    news_events["plot_date"] = news_events["date"].apply(lambda d: nearest_trading_day(d, sp500["Date"]))

    price_map = dict(zip(sp500["Date"], sp500["Close"]))
    news_events["price"] = news_events["plot_date"].map(price_map)
else:
    print("Warning: No valid news events found to plot.")

# Build chart

fig = go.Figure()

# S&P 500 Line
fig.add_trace(go.Scatter(
    x=sp500["Date"],
    y=sp500["Close"],
    mode="lines",
    name="S&P 500",
    line=dict(width=2),
    hovertemplate="Date: %{x}<br>S&P 500: %{y:.2f}<extra></extra>"
))

# VIX Line
fig.add_trace(go.Scatter(
    x=vix["Date"],
    y=vix["Close"],
    mode="lines",
    name="VIX",
    yaxis="y2",
    line=dict(dash="dot", color="gray"),
    hovertemplate="Date: %{x}<br>VIX: %{y:.2f}<extra></extra>"
))

# News markers
if not news_events.empty:
    fig.add_trace(go.Scatter(
        x=news_events["plot_date"],
        y=news_events["price"],
        mode="markers",
        name="News Events",
        marker=dict(size=12, symbol="circle", line=dict(width=1, color="black")),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Date: %{x}<br>"
            "Price: %{y:.2f}<br>"
            "Source: %{customdata[1]}<br>"
            "<i>%{customdata[2]}</i><extra></extra>"
        ),
        customdata=news_events[["headline", "source", "description"]].values
    ))

# Layout
fig.update_layout(
    title="S&P 500 with News Events and VIX",
    xaxis_title="Date",
    yaxis=dict(title="S&P 500 Price"),
    yaxis2=dict(
        title="VIX",
        overlaying="y",
        side="right",
        showgrid=False
    ),
    hovermode="closest",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

fig.show()