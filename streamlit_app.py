import os
import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="MSF 고위험 지역 2026", page_icon="🆘", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@300;400;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap');
  html,body,[class*="css"]{font-family:'IBM Plex Sans KR',sans-serif;background:#0f1117;color:#e8e8e8;}
  .msf-header{background:linear-gradient(135deg,#1a0a0a,#1e1e2e);border-left:5px solid #e63946;padding:24px 32px 18px;margin-bottom:20px;border-radius:0 8px 8px 0;}
  .msf-header h1{font-size:2rem;font-weight:700;color:#fff;margin:0 0 4px;letter-spacing:-0.5px;}
  .msf-header p{color:#9a9ab0;font-size:0.82rem;font-family:'IBM Plex Mono',monospace;margin:0;}
  .kpi-card{background:linear-gradient(135deg,#1e293b,#0f172a);border:1px solid #334155;border-radius:10px;padding:16px 18px;text-align:center;}
  .kpi-label{color:#94a3b8;font-size:0.72rem;letter-spacing:.5px;text-transform:uppercase;}
  .kpi-value{color:#e63946;font-size:1.8rem;font-weight:700;font-family:'IBM Plex Mono',monospace;}
  .kpi-unit{color:#64748b;font-size:0.78rem;margin-top:2px;}
  .detail-panel{background:#16213e;border:1px solid #e63946;border-radius:10px;padding:24px;margin-top:8px;}
  .detail-panel h2{font-size:1.4rem;font-weight:700;color:#fff;margin:0 0 4px;}
  .crisis-type{font-size:0.78rem;color:#e63946;font-family:'IBM Plex Mono',monospace;letter-spacing:1px;text-transform:uppercase;margin-bottom:16px;}
  .stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:16px;}
  .stat-box{background:#0f1117;border-radius:8px;padding:12px;text-align:center;border:1px solid #2a2a4a;}
  .stat-box .number{font-size:1.2rem;font-weight:700;color:#e63946;font-family:'IBM Plex Mono',monospace;}
  .stat-box .label{font-size:0.68rem;color:#9a9ab0;margin-top:3px;}
  .risk-factors{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px;}
  .risk-tag-pill{background:#1e1e2e;border:1px solid #3a3a5a;border-radius:20px;padding:3px 10px;font-size:0.72rem;color:#c0c0d8;}
  .source-note{font-size:0.7rem;color:#5a5a7a;font-family:'IBM Plex Mono',monospace;margin-top:10px;padding-top:10px;border-top:1px solid #2a2a4a;}
  .legend-box{background:#16213e;border:1px solid #2a2a4a;border-radius:8px;padding:12px 16px;margin-bottom:14px;font-size:0.78rem;color:#9a9ab0;}
  .legend-box span{color:#e63946;font-weight:700;}
  .section-title{font-size:1rem;font-weight:700;color:#e2e8f0;border-left:4px solid #e63946;padding-left:10px;margin:18px 0 10px;}
  #MainMenu,footer,header{visibility:hidden;}
  .block-container{padding-top:1rem;}
</style>
""", unsafe_allow_html=True)

BASE = os.path.dirname(__file__)

@st.cache_data
def load_csvs():
    country_df = pd.read_csv(os.path.join(BASE, "msf_dashboard_country_summary.csv"))
    events_df  = pd.read_csv(os.path.join(BASE, "msf_dashboard_events.csv"))
    risk_df    = pd.read_csv(os.path.join(BASE, "msf_dashboard_risk_factors.csv"))
    for col in ["cases_reported","deaths_reported","injuries_reported","fatality_rate_pct","risk_score"]:
        country_df[col] = pd.to_numeric(country_df[col], errors="coerce")
    events_df["start_date"] = pd.to_datetime(events_df["start_date"])
    events_df["end_date"]   = pd.to_datetime(events_df["end_date"])
    return country_df, events_df, risk_df

country_df, events_df, risk_df = load_csvs()

COUNTRIES = {
    "Sudan":{"kr":"수단","lat":15.5,"lon":32.5,"crisis":"콜레라 대유행","icon":"💊",
      "stats":[{"number":"124,418명","label":"감염자"},{"number":"3,573명","label":"사망자"},{"number":"2.87%","label":"치명률"}],
      "risks":["상하수도 붕괴","대규모 이동","홍수","의료 접근 제한"],
      "desc":"수단은 2024년 8월 이후 대규모 콜레라 유행이 지속됐습니다. 내전으로 인한 인프라 붕괴와 의료 시스템 마비가 상황을 악화시켰으며, 2026년 3월 공식 종식이 선언됐습니다.",
      "source":"WHO Sudan Cholera Update (2026-03-08)"},
    "Democratic Republic of the Congo":{"kr":"DR콩고","lat":-4.0,"lon":21.8,"crisis":"다중 전염병 동시 발생","icon":"🦠",
      "stats":[{"number":"450,000+","label":"유행 건수"},{"number":"8,700+명","label":"사망자"},{"number":"5종+","label":"동시 질병"}],
      "risks":["콜레라","mpox","홍역","에볼라","폴리오"],
      "desc":"WHO 2026 긴급호소 대상국으로, 5개 이상의 전염병이 동시에 유행 중입니다. 분쟁과 극빈, 보건 인프라 부재가 복합적으로 작용하고 있습니다.",
      "source":"WHO DRC Health Emergency Appeal 2026"},
    "South Sudan":{"kr":"남수단","lat":6.9,"lon":31.3,"crisis":"사상 최대 콜레라 확산","icon":"🌊",
      "stats":[{"number":"96,000+건","label":"콜레라 케이스"},{"number":"~1,600명","label":"사망자"},{"number":"역대 최대","label":"규모"}],
      "risks":["홍수","국경 유입","취약 보건체계","mpox 동시 부담","간염 E"],
      "desc":"2025년 11월 말 기준 역대 최대 규모 콜레라 유행입니다. 홍수로 인한 인프라 피해와 국경을 통한 지속적 유입이 상황을 심화시키고 있습니다.",
      "source":"South Sudan HNRP 2026"},
    "Gaza Strip":{"kr":"가자지구","lat":31.5,"lon":34.47,"crisis":"전쟁·기아·감염병 위험 중첩","icon":"⚔️",
      "stats":[{"number":"63,000+명","label":"사망자"},{"number":"161,000+명","label":"부상자"},{"number":"2.1M명","label":"지원 필요"}],
      "risks":["오염수","하수시설 파괴","극심한 과밀","폐기물 축적","낮은 예방접종률"],
      "desc":"지속되는 군사 충돌로 의료 인프라가 거의 전멸 상태입니다. 기아, 오염수, 파괴된 하수 시스템이 감염병 대규모 확산의 직접 위험 요인입니다.",
      "source":"WHO Gaza PHSA (2025-09-10)"},
    "Haiti":{"kr":"아이티","lat":18.97,"lon":-72.3,"crisis":"치안붕괴 속 콜레라 재확산","icon":"🚨",
      "stats":[{"number":"4,864명","label":"갱 폭력 사망"},{"number":"17명","label":"콜레라 사망"},{"number":"복합위기","label":"보건·치안"}],
      "risks":["갱 폭력","성폭력","대규모 이동","병원 운영 중단","불안정한 식수·위생"],
      "desc":"갱단의 수도권 장악으로 치안이 붕괴된 가운데, 2025년 페티옹빌에서 콜레라가 재확산됐습니다. 병원 운영 중단으로 인도주의 접근이 극도로 어렵습니다.",
      "source":"UN 2025 / PAHO Haiti Cholera Story (2025-11)"},
}

PD = dict(template="plotly_dark", paper_bgcolor="#0f1117", plot_bgcolor="#1e293b")
RED = "#e63946"

if "selected" not in st.session_state:
    st.session_state.selected = None

st.markdown("""
<div class="msf-header">
  <h1>🆘 MSF 활동 고위험 지역 2026</h1>
  <p>전염병 · 위험요소 · 사망 통계 | 출처: WHO / PAHO / OHCHR / OCHA / ReliefWeb</p>
</div>
""", unsafe_allow_html=True)

k1,k2,k3,k4 = st.columns(4)
for col,label,value,unit in [
    (k1,"총 감염·케이스", f"{int(country_df['cases_reported'].sum()):,}","건"),
    (k2,"총 사망자",      f"{int(country_df['deaths_reported'].sum()):,}","명"),
    (k3,"총 부상자",      f"{int(country_df['injuries_reported'].fillna(0).sum()):,}","명"),
    (k4,"평균 위험 점수", str(round(country_df['risk_score'].mean(),1)),"/ 10"),
]:
    col.markdown(f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-unit">{unit}</div></div>', unsafe_allow_html=True)

st.markdown("")

tab_map,tab_charts,tab_risk,tab_timeline,tab_data = st.tabs(
    ["🗺️ 지역 지도","📊 통계 그래프","⚠️ 위험요인","📅 타임라인","📄 원시 데이터"])

# ── TAB 1: 지도 ──────────────────────────────────────────────────────────────
with tab_map:
    col_map,col_panel = st.columns([3,2],gap="large")
    with col_map:
        st.markdown('<div class="legend-box"><span>● 빨간 마커</span> = MSF 의료 개입 필요성이 큰 복합위기 지역 &nbsp;|&nbsp; 마커 클릭 또는 우측 버튼으로 상세 정보 확인</div>', unsafe_allow_html=True)
        m = folium.Map(location=[10,20],zoom_start=2,tiles="CartoDB dark_matter",prefer_canvas=True)
        for en,info in COUNTRIES.items():
            hi = f'<div style="background:#e63946;border-radius:50%;width:36px;height:36px;display:flex;align-items:center;justify-content:center;font-size:16px;box-shadow:0 0 12px rgba(230,57,70,0.8);border:2px solid #fff;">{info["icon"]}</div>'
            icon = folium.DivIcon(html=hi,icon_size=(36,36),icon_anchor=(18,18))
            rows = "".join(f'<span style="font-size:0.8rem;color:#ccc;">• {s["label"]}: <b style="color:#e63946">{s["number"]}</b></span><br>' for s in info["stats"])
            ph = f'<div style="font-family:sans-serif;background:#16213e;color:#fff;padding:14px;border-radius:8px;min-width:200px;border:1px solid #e63946;"><b style="font-size:1rem">{info["kr"]}</b><br><span style="color:#e63946;font-size:0.78rem">{info["crisis"]}</span><br><br>{rows}</div>'
            popup = folium.Popup(folium.IFrame(ph,width=230,height=165),max_width=250)
            folium.Marker(location=[info["lat"],info["lon"]],popup=popup,
                tooltip=f"<b style='color:#e63946'>{info['kr']}</b> — {info['crisis']}",icon=icon).add_to(m)
            folium.CircleMarker(location=[info["lat"],info["lon"]],radius=22,color=RED,weight=1,fill=True,fill_color=RED,fill_opacity=0.08).add_to(m)
        map_data = st_folium(m,width="100%",height=460,returned_objects=["last_object_clicked_tooltip"])
        if map_data and map_data.get("last_object_clicked_tooltip"):
            tip = map_data["last_object_clicked_tooltip"]
            for en,info in COUNTRIES.items():
                if info["kr"] in tip:
                    st.session_state.selected = en
                    break

    with col_panel:
        st.markdown("### 국가 선택")
        for en,info in COUNTRIES.items():
            if st.button(f"{info['icon']}  {info['kr']}  |  {info['crisis']}",key=f"btn_{en}",use_container_width=True):
                st.session_state.selected = en
        sel = st.session_state.selected
        if sel and sel in COUNTRIES:
            info = COUNTRIES[sel]
            st.markdown("---")
            stat_boxes = "".join(f'<div class="stat-box"><div class="number">{s["number"]}</div><div class="label">{s["label"]}</div></div>' for s in info["stats"])
            risk_pills = "".join(f'<span class="risk-tag-pill">{r}</span>' for r in info["risks"])
            st.markdown(f'<div class="detail-panel"><h2>{info["icon"]} {info["kr"]}</h2><div class="crisis-type">⚠ {info["crisis"]}</div><div class="stat-grid">{stat_boxes}</div><p style="font-size:0.86rem;color:#c0c0d8;line-height:1.65;margin-bottom:14px;">{info["desc"]}</p><div style="font-size:0.76rem;color:#9a9ab0;font-weight:600;margin-bottom:8px;">주요 위험요인</div><div class="risk-factors">{risk_pills}</div><div class="source-note">📎 {info["source"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="background:#16213e;border:1px dashed #2a2a4a;border-radius:10px;padding:32px;text-align:center;color:#5a5a7a;margin-top:8px;">← 지도 마커 또는 위 버튼을 클릭하면<br>상세 정보가 표시됩니다</div>', unsafe_allow_html=True)

# ── TAB 2: 통계 그래프 ────────────────────────────────────────────────────────
LAYOUT = dict(template="plotly_dark", paper_bgcolor="#0f1117", plot_bgcolor="#1e293b",
              margin=dict(l=10,r=10,t=10,b=10), height=300,
              xaxis=dict(gridcolor="#334155"), yaxis=dict(gridcolor="#334155"))

with tab_charts:
    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-title">1️⃣ 국가별 사망자 수</div>', unsafe_allow_html=True)
        df_d = country_df[["country","deaths_reported"]].dropna().sort_values("deaths_reported")
        fig1 = px.bar(df_d,x="deaths_reported",y="country",orientation="h",color="deaths_reported",
            color_continuous_scale="Reds",labels={"deaths_reported":"사망자 수","country":"국가"})
        fig1.update_layout(**LAYOUT, coloraxis_showscale=False)
        fig1.update_traces(hovertemplate="%{y}<br>사망자: %{x:,}명<extra></extra>")
        st.plotly_chart(fig1,use_container_width=True)
    with c2:
        st.markdown('<div class="section-title">2️⃣ 국가별 감염·케이스 수</div>', unsafe_allow_html=True)
        df_c = country_df[["country","cases_reported"]].dropna().sort_values("cases_reported")
        fig2 = px.bar(df_c,x="cases_reported",y="country",orientation="h",color="cases_reported",
            color_continuous_scale="OrRd",labels={"cases_reported":"케이스 수","country":"국가"})
        fig2.update_layout(**LAYOUT, coloraxis_showscale=False)
        fig2.update_traces(hovertemplate="%{y}<br>케이스: %{x:,}건<extra></extra>")
        st.plotly_chart(fig2,use_container_width=True)
    c3,c4 = st.columns(2)
    with c3:
        st.markdown('<div class="section-title">3️⃣ 감염 vs 사망 (버블: 위험점수)</div>', unsafe_allow_html=True)
        df_s = country_df.dropna(subset=["cases_reported","deaths_reported","risk_score"])
        fig3 = px.scatter(df_s,x="cases_reported",y="deaths_reported",size="risk_score",
            color="region_group",hover_name="country",
            labels={"cases_reported":"감염·케이스","deaths_reported":"사망자","region_group":"지역"})
        fig3.update_layout(**LAYOUT, legend=dict(orientation="h",y=1.1))
        st.plotly_chart(fig3,use_container_width=True)
    with c4:
        st.markdown('<div class="section-title">4️⃣ 국가별 치명률 (%)</div>', unsafe_allow_html=True)
        df_f = country_df[["country","fatality_rate_pct"]].dropna().sort_values("fatality_rate_pct")
        fig4 = px.bar(df_f,x="fatality_rate_pct",y="country",orientation="h",color="fatality_rate_pct",
            color_continuous_scale="YlOrRd",labels={"fatality_rate_pct":"치명률 (%)","country":"국가"})
        fig4.update_layout(**LAYOUT, coloraxis_showscale=False)
        fig4.update_traces(hovertemplate="%{y}<br>치명률: %{x:.2f}%<extra></extra>")
        st.plotly_chart(fig4,use_container_width=True)

# ── TAB 3: 위험요인 ──────────────────────────────────────────────────────────
with tab_risk:
    st.markdown('<div class="section-title">5️⃣ 국가 × 위험요인 히트맵</div>', unsafe_allow_html=True)
    RISK_LABEL = {"conflict":"분쟁·전쟁","displacement":"대규모 이동","flooding":"홍수",
        "wash_breakdown":"상하수도 붕괴","health_system_strain":"보건체계 붕괴",
        "food_insecurity":"식량 불안","overcrowding":"과밀","low_vaccination":"낮은 예방접종"}
    risk_df2 = risk_df.copy()
    risk_df2["risk_label"] = risk_df2["risk_factor"].map(lambda x: RISK_LABEL.get(x,x))
    heatmap = risk_df2.pivot_table(index="risk_label",columns="country",values="present",aggfunc="max").fillna(0)
    hover = [[f"{heatmap.index[r]} | {heatmap.columns[c]}<br>{'존재 ✓' if heatmap.values[r,c]==1 else '해당 없음'}" for c in range(len(heatmap.columns))] for r in range(len(heatmap.index))]
    fig5 = go.Figure(data=go.Heatmap(
        z=heatmap.values,x=heatmap.columns.tolist(),y=heatmap.index.tolist(),
        colorscale=[[0,"#1e293b"],[1,"#e63946"]],showscale=False,
        text=[["✓" if v==1 else "" for v in row] for row in heatmap.values],
        texttemplate="%{text}",textfont=dict(size=16,color="white"),
        hovertext=hover,hovertemplate="%{hovertext}<extra></extra>"))
    fig5.update_layout(paper_bgcolor="#0f1117",plot_bgcolor="#1e293b",height=360,
        margin=dict(l=10,r=10,t=10,b=10),
        xaxis=dict(tickangle=-20,tickfont=dict(size=11)),yaxis=dict(tickfont=dict(size=11)))
    st.plotly_chart(fig5,use_container_width=True)

    st.markdown('<div class="section-title">국가별 위험요인 레이더</div>', unsafe_allow_html=True)
    risk_cols = [c for c in country_df.columns if c.startswith("risk_") and c!="risk_score"]
    risk_labels = [RISK_LABEL.get(c.replace("risk_",""),c) for c in risk_cols]
    fig_r = go.Figure()
    colors = ["#e63946","#f4a261","#e9c46a","#2a9d8f","#457b9d"]
    for i,row in country_df.iterrows():
        vals = [row[c] for c in risk_cols]+[row[risk_cols[0]]]
        fig_r.add_trace(go.Scatterpolar(r=vals,theta=risk_labels+risk_labels[:1],
            fill="toself",name=row["country"],line_color=colors[i%len(colors)],opacity=0.7))
    fig_r.update_layout(polar=dict(bgcolor="#1e293b",radialaxis=dict(visible=True,range=[0,1],showticklabels=False)),
        paper_bgcolor="#0f1117",height=380,margin=dict(l=20,r=20,t=20,b=20),
        legend=dict(orientation="h",y=-0.1,font=dict(size=11)),template="plotly_dark")
    st.plotly_chart(fig_r,use_container_width=True)

# ── TAB 4: 타임라인 ──────────────────────────────────────────────────────────
with tab_timeline:
    st.markdown('<div class="section-title">6️⃣ 위기 이벤트 타임라인</div>', unsafe_allow_html=True)
    COLOR_MAP = {"disease_outbreak":"#e63946","multi_epidemic":"#f4a261","conflict_health_crisis":"#457b9d"}
    LABEL_MAP = {"disease_outbreak":"전염병 발생","multi_epidemic":"복합 전염병","conflict_health_crisis":"분쟁·보건 위기"}
    events_df["event_label"] = events_df["event_type"].map(LABEL_MAP)
    fig6 = px.timeline(events_df,x_start="start_date",x_end="end_date",y="country",
        color="event_label",color_discrete_map={v:COLOR_MAP[k] for k,v in LABEL_MAP.items()},
        hover_name="event_name",hover_data={"metric_cases":True,"metric_deaths":True,"event_label":False},
        labels={"event_label":"이벤트 유형","country":"국가","metric_cases":"케이스","metric_deaths":"사망자"})
    fig6.update_yaxes(autorange="reversed")
    fig6.update_layout(template="plotly_dark",paper_bgcolor="#0f1117",plot_bgcolor="#1e293b",height=380,margin=dict(l=10,r=10,t=10,b=10),
        xaxis=dict(gridcolor="#334155",title=""),yaxis=dict(gridcolor="#334155"),
        legend=dict(orientation="h",y=1.08))
    st.plotly_chart(fig6,use_container_width=True)

# ── TAB 5: 데이터 ────────────────────────────────────────────────────────────
with tab_data:
    st.markdown('<div class="section-title">📄 국가 요약 데이터</div>', unsafe_allow_html=True)
    show_cols = ["country","region_group","primary_crisis","cases_reported","deaths_reported","injuries_reported","fatality_rate_pct","risk_score","data_as_of","source_org"]
    st.dataframe(country_df[show_cols].style.format({"cases_reported":"{:,.0f}","deaths_reported":"{:,.0f}","injuries_reported":"{:,.0f}","fatality_rate_pct":"{:.2f}%","risk_score":"{:.0f}"},na_rep="—"),use_container_width=True,height=280)
    st.markdown('<div class="section-title">📄 이벤트 데이터</div>', unsafe_allow_html=True)
    st.dataframe(events_df[["country","event_type","event_name","disease","metric_cases","metric_deaths","start_date","end_date"]],use_container_width=True,height=240)
    st.markdown('<div class="section-title">📄 위험요인 데이터</div>', unsafe_allow_html=True)
    st.dataframe(risk_df,use_container_width=True,height=240)

st.markdown("---")
st.markdown('<div style="font-size:0.7rem;color:#5a5a7a;font-family:IBM Plex Mono,monospace;line-height:1.8;">📎 WHO Sudan Cholera Update (2026-03-08) | WHO DRC Health Emergency Appeal 2026 | South Sudan HNRP 2026 | WHO Gaza PHSA (2025-09-10) | PAHO Haiti Cholera Story (2025-11) | OHCHR Haiti Violence Update (2025-07)</div>', unsafe_allow_html=True)
