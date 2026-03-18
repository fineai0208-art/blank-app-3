import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="MSF Dashboard", layout="wide")

st.title("🌍 MSF High-Risk Region Dashboard")

# 데이터 불러오기
country_df = pd.read_csv("msf_dashboard_country_summary.csv")
events_df = pd.read_csv("msf_dashboard_events.csv")
risk_df = pd.read_csv("msf_dashboard_risk_factors.csv")

# 숫자형 변환
for col in ["cases_reported", "deaths_reported", "injuries_reported", "fatality_rate_pct", "risk_score"]:
    country_df[col] = pd.to_numeric(country_df[col], errors="coerce")

# KPI
st.subheader("📊 Key Indicators")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Cases", int(country_df["cases_reported"].sum()))
col2.metric("Total Deaths", int(country_df["deaths_reported"].sum()))
col3.metric("Total Injuries", int(country_df["injuries_reported"].fillna(0).sum()))
col4.metric("Avg Risk Score", round(country_df["risk_score"].mean(), 1))

st.divider()

# 1. 사망자 그래프
st.subheader("1️⃣ Deaths by Country")
fig1 = px.bar(country_df, x="deaths_reported", y="country", orientation="h")
st.plotly_chart(fig1, use_container_width=True)

# 2. 감염자 그래프
st.subheader("2️⃣ Cases by Country")
fig2 = px.bar(country_df, x="cases_reported", y="country", orientation="h")
st.plotly_chart(fig2, use_container_width=True)

# 3. 감염 vs 사망
st.subheader("3️⃣ Cases vs Deaths")
fig3 = px.scatter(
    country_df,
    x="cases_reported",
    y="deaths_reported",
    size="risk_score",
    color="region_group",
    hover_name="country"
)
st.plotly_chart(fig3, use_container_width=True)

# 4. 치명률
st.subheader("4️⃣ Fatality Rate (%)")
fig4 = px.bar(country_df, x="fatality_rate_pct", y="country", orientation="h")
st.plotly_chart(fig4, use_container_width=True)

# 5. 위험요소 히트맵
st.subheader("5️⃣ Risk Factor Heatmap")
heatmap = risk_df.pivot(index="risk_factor", columns="country", values="present")
fig5 = px.imshow(heatmap, text_auto=True)
st.plotly_chart(fig5, use_container_width=True)

# 6. 타임라인
st.subheader("6️⃣ Event Timeline")
events_df["start_date"] = pd.to_datetime(events_df["start_date"])
events_df["end_date"] = pd.to_datetime(events_df["end_date"])

fig6 = px.timeline(
    events_df,
    x_start="start_date",
    x_end="end_date",
    y="country",
    color="event_type"
)
fig6.update_yaxes(autorange="reversed")
st.plotly_chart(fig6, use_container_width=True)

# 데이터 테이블
st.subheader("📄 Raw Data")
st.dataframe(country_df)
