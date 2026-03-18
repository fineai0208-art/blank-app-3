import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── 페이지 설정 ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="2025년 1월 대기질 대시보드",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 스타일 ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=JetBrains+Mono:wght@400;600&display=swap');

  html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }

  .main-header {
    background: linear-gradient(135deg, #0a1628 0%, #1a2744 50%, #0d2137 100%);
    padding: 24px 32px 18px;
    border-radius: 12px;
    margin-bottom: 20px;
    border-bottom: 3px solid #3b82f6;
  }
  .main-header h1 { color:#fff; font-size:1.8rem; font-weight:700; margin:0 0 4px; }
  .main-header p  { color:#94a3b8; font-size:0.85rem; margin:0; font-family:'JetBrains Mono',monospace; }

  .kpi-card {
    background: linear-gradient(135deg, #1e293b, #0f172a);
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 16px 20px;
    text-align: center;
  }
  .kpi-card .kpi-label { color:#94a3b8; font-size:0.75rem; letter-spacing:.5px; text-transform:uppercase; }
  .kpi-card .kpi-value { color:#e2e8f0; font-size:1.7rem; font-weight:700; font-family:'JetBrains Mono',monospace; }
  .kpi-card .kpi-unit  { color:#64748b; font-size:0.8rem; }

  .grade-good    { color:#22c55e !important; }
  .grade-normal  { color:#3b82f6 !important; }
  .grade-bad     { color:#f59e0b !important; }
  .grade-verybad { color:#ef4444 !important; }

  .section-title {
    font-size:1.05rem; font-weight:700; color:#e2e8f0;
    border-left:4px solid #3b82f6; padding-left:12px; margin:20px 0 12px;
  }
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# ── 상수 정의 ────────────────────────────────────────────────────────────────
POLLUTANTS = {
    "PM25":  {"label": "PM2.5 (초미세먼지)", "unit": "㎍/㎥", "color": "#f59e0b",
              "grades": [(0,15,"좋음","#22c55e"),(15,35,"보통","#3b82f6"),(35,75,"나쁨","#f59e0b"),(75,999,"매우나쁨","#ef4444")]},
    "PM10":  {"label": "PM10 (미세먼지)",    "unit": "㎍/㎥", "color": "#fb923c",
              "grades": [(0,30,"좋음","#22c55e"),(30,80,"보통","#3b82f6"),(80,150,"나쁨","#f59e0b"),(150,999,"매우나쁨","#ef4444")]},
    "O3":    {"label": "O₃ (오존)",         "unit": "ppm",   "color": "#a78bfa",
              "grades": [(0,0.03,"좋음","#22c55e"),(0.03,0.09,"보통","#3b82f6"),(0.09,0.15,"나쁨","#f59e0b"),(0.15,999,"매우나쁨","#ef4444")]},
    "NO2":   {"label": "NO₂ (이산화질소)",   "unit": "ppm",   "color": "#34d399",
              "grades": [(0,0.03,"좋음","#22c55e"),(0.03,0.06,"보통","#3b82f6"),(0.06,0.2,"나쁨","#f59e0b"),(0.2,999,"매우나쁨","#ef4444")]},
    "SO2":   {"label": "SO₂ (아황산가스)",   "unit": "ppm",   "color": "#60a5fa",
              "grades": [(0,0.02,"좋음","#22c55e"),(0.02,0.05,"보통","#3b82f6"),(0.05,0.15,"나쁨","#f59e0b"),(0.15,999,"매우나쁨","#ef4444")]},
    "CO":    {"label": "CO (일산화탄소)",    "unit": "ppm",   "color": "#f87171",
              "grades": [(0,2,"좋음","#22c55e"),(2,9,"보통","#3b82f6"),(9,15,"나쁨","#f59e0b"),(15,999,"매우나쁨","#ef4444")]},
}

PLOTLY_TEMPLATE = "plotly_dark"
PLOTLY_PAPER_BG = "#0f172a"
PLOTLY_PLOT_BG  = "#1e293b"

# ── 데이터 로드 ───────────────────────────────────────────────────────────────
import os
DATA_PATH = os.path.join(os.path.dirname(__file__), '202501-air.csv')

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df['시도'] = df['지역'].str.split(' ').str[0]
    ts = df['측정일시'].astype(str).str.zfill(10)
    df['날짜']  = pd.to_datetime(ts.str[:8], format='%Y%m%d')
    df['시간']  = ts.str[8:10].astype(int)
    df['날짜시간'] = df['날짜'] + pd.to_timedelta(df['시간'] - 1, unit='h')
    for p in POLLUTANTS:
        df[p] = pd.to_numeric(df[p], errors='coerce')
    return df

df = load_data()

def get_grade(val, grades):
    for lo, hi, name, color in grades:
        if lo <= val < hi:
            return name, color
    return "측정불가", "#64748b"

# ── 사이드바 필터 ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 필터")
    sido_list = sorted(df['시도'].unique())
    sel_sido = st.multiselect("시·도 선택", sido_list, default=sido_list[:3])
    if not sel_sido:
        sel_sido = sido_list

    mang_list = sorted(df['망'].unique())
    sel_mang = st.multiselect("측정망 유형", mang_list, default=['도시대기'])
    if not sel_mang:
        sel_mang = mang_list

    sel_poll = st.selectbox(
        "대표 오염물질 (지도·시계열 기준)",
        list(POLLUTANTS.keys()),
        format_func=lambda x: POLLUTANTS[x]['label']
    )

    date_min = df['날짜'].min().date()
    date_max = df['날짜'].max().date()
    sel_dates = st.date_input("날짜 범위", value=(date_min, date_max),
                               min_value=date_min, max_value=date_max)
    if len(sel_dates) == 2:
        d1, d2 = pd.Timestamp(sel_dates[0]), pd.Timestamp(sel_dates[1])
    else:
        d1, d2 = pd.Timestamp(date_min), pd.Timestamp(date_max)

    st.markdown("---")
    st.markdown("""
    <div style='font-size:0.72rem; color:#64748b; line-height:1.7;'>
    📎 출처: 한국환경공단 에어코리아<br>
    📅 기간: 2025년 1월<br>
    🏷️ 단위: ㎍/㎥ (PM), ppm (기타)
    </div>
    """, unsafe_allow_html=True)

# ── 데이터 필터링 ─────────────────────────────────────────────────────────────
dff = df[
    df['시도'].isin(sel_sido) &
    df['망'].isin(sel_mang) &
    (df['날짜'] >= d1) &
    (df['날짜'] <= d2)
].copy()

# ── 헤더 ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="main-header">
  <h1>🌫️ 2025년 1월 대기질 현황 대시보드</h1>
  <p>측정 기간: 2025.01.01 ~ 2025.01.31 &nbsp;|&nbsp; 측정소 {dff['측정소명'].nunique()}개소 &nbsp;|&nbsp;
     레코드 {len(dff):,}건 &nbsp;|&nbsp; 시·도: {', '.join(sel_sido)}</p>
</div>
""", unsafe_allow_html=True)

# ── KPI 카드 ─────────────────────────────────────────────────────────────────
kpi_cols = st.columns(6)
for i, (p, meta) in enumerate(POLLUTANTS.items()):
    mean_val = dff[p].mean()
    g_name, g_color = get_grade(mean_val, meta['grades']) if not np.isnan(mean_val) else ("N/A","#64748b")
    mean_str = f"{mean_val:.3f}" if mean_val < 1 else f"{mean_val:.1f}"
    with kpi_cols[i]:
        st.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-label">{meta['label'].split('(')[0].strip()}</div>
          <div class="kpi-value" style="color:{g_color}">
            {mean_str}
          </div>
          <div class="kpi-unit">{meta['unit']} · {g_name}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("")

# ── 탭 구성 ──────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📈 시계열·일별 추이", "🗺️ 지역별 비교", "⏱️ 시간대 패턴", "📊 오염물질 분포", "🔍 측정소 상세"]
)

# ════════════════════════════════════════════════════════════════════════════
# TAB 1: 시계열 & 일별 추이
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    c1, c2 = st.columns([2, 1])

    with c1:
        st.markdown('<div class="section-title">일별 평균 농도 추이</div>', unsafe_allow_html=True)
        daily = dff.groupby(['날짜','시도'])[sel_poll].mean().reset_index()

        fig = px.line(
            daily, x='날짜', y=sel_poll, color='시도',
            labels={'날짜':'날짜', sel_poll: POLLUTANTS[sel_poll]['label']},
            template=PLOTLY_TEMPLATE,
            line_shape='spline',
        )
        fig.update_layout(
            paper_bgcolor=PLOTLY_PAPER_BG, plot_bgcolor=PLOTLY_PLOT_BG,
            height=340, margin=dict(l=10,r=10,t=10,b=10),
            legend=dict(orientation='h', y=1.08, x=0),
            xaxis=dict(showgrid=True, gridcolor='#1e293b'),
            yaxis=dict(showgrid=True, gridcolor='#334155',
                       title=POLLUTANTS[sel_poll]['unit']),
            hovermode='x unified',
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<div class="section-title">주간별 박스플롯</div>', unsafe_allow_html=True)
        dff2 = dff.copy()
        dff2['주차'] = '주' + dff2['날짜'].dt.isocalendar().week.astype(str)

        fig2 = px.box(
            dff2, x='주차', y=sel_poll, color='주차',
            template=PLOTLY_TEMPLATE,
            labels={sel_poll: POLLUTANTS[sel_poll]['unit']},
        )
        fig2.update_layout(
            paper_bgcolor=PLOTLY_PAPER_BG, plot_bgcolor=PLOTLY_PLOT_BG,
            height=340, margin=dict(l=10,r=10,t=10,b=10),
            showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True)

    # 6개 오염물질 히트맵 (일별 × 시도)
    st.markdown('<div class="section-title">6개 오염물질 일별 히트맵 (전체 평균)</div>', unsafe_allow_html=True)
    daily_all = dff.groupby('날짜')[list(POLLUTANTS.keys())].mean().reset_index()

    # 정규화 (0~1)
    normalized = daily_all.copy()
    for p in POLLUTANTS:
        mn, mx = normalized[p].min(), normalized[p].max()
        normalized[p] = (normalized[p] - mn) / (mx - mn + 1e-9)

    fig3 = go.Figure(data=go.Heatmap(
        z=normalized[list(POLLUTANTS.keys())].T.values,
        x=daily_all['날짜'].dt.strftime('%m/%d'),
        y=[POLLUTANTS[p]['label'] for p in POLLUTANTS],
        colorscale='RdYlGn_r',
        hovertemplate='날짜: %{x}<br>항목: %{y}<br>정규화값: %{z:.2f}<extra></extra>',
    ))
    fig3.update_layout(
        paper_bgcolor=PLOTLY_PAPER_BG, plot_bgcolor=PLOTLY_PLOT_BG,
        height=220, margin=dict(l=10,r=10,t=10,b=10),
        xaxis=dict(tickangle=-45, tickfont=dict(size=9)),
    )
    st.plotly_chart(fig3, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 2: 지역별 비교
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="section-title">시·도별 평균 (선택 오염물질)</div>', unsafe_allow_html=True)
        by_sido = dff.groupby('시도')[sel_poll].mean().reset_index().sort_values(sel_poll, ascending=True)
        grade_colors = []
        for v in by_sido[sel_poll]:
            _, gc = get_grade(v, POLLUTANTS[sel_poll]['grades'])
            grade_colors.append(gc)

        fig4 = go.Figure(go.Bar(
            x=by_sido[sel_poll], y=by_sido['시도'],
            orientation='h',
            marker_color=grade_colors,
            text=by_sido[sel_poll].round(2),
            textposition='outside',
            hovertemplate='%{y}: %{x:.3f} ' + POLLUTANTS[sel_poll]['unit'] + '<extra></extra>',
        ))
        fig4.update_layout(
            paper_bgcolor=PLOTLY_PAPER_BG, plot_bgcolor=PLOTLY_PLOT_BG,
            height=320, margin=dict(l=10,r=60,t=10,b=10),
            xaxis_title=POLLUTANTS[sel_poll]['unit'],
        )
        st.plotly_chart(fig4, use_container_width=True)

    with c2:
        st.markdown('<div class="section-title">시·도별 레이더 차트</div>', unsafe_allow_html=True)
        # 각 오염물질을 0~1 정규화해서 레이더 표시
        radar_data = dff.groupby('시도')[list(POLLUTANTS.keys())].mean()
        radar_norm = (radar_data - radar_data.min()) / (radar_data.max() - radar_data.min() + 1e-9)

        fig5 = go.Figure()
        colors = px.colors.qualitative.Plotly
        labels = [POLLUTANTS[p]['label'].split('(')[0].strip() for p in POLLUTANTS]
        for i, sido in enumerate(radar_norm.index):
            vals = radar_norm.loc[sido].tolist()
            vals += vals[:1]  # 닫기
            fig5.add_trace(go.Scatterpolar(
                r=vals, theta=labels + labels[:1],
                fill='toself', name=sido,
                line_color=colors[i % len(colors)],
                opacity=0.7,
            ))
        fig5.update_layout(
            polar=dict(
                bgcolor=PLOTLY_PLOT_BG,
                radialaxis=dict(visible=True, range=[0,1], showticklabels=False),
            ),
            paper_bgcolor=PLOTLY_PAPER_BG,
            height=320, margin=dict(l=30,r=30,t=30,b=30),
            legend=dict(orientation='h', y=-0.1),
            showlegend=True,
            template=PLOTLY_TEMPLATE,
        )
        st.plotly_chart(fig5, use_container_width=True)

    # 시도 × 오염물질 히트맵
    st.markdown('<div class="section-title">시·도 × 오염물질 평균 히트맵</div>', unsafe_allow_html=True)
    pivot = dff.groupby('시도')[list(POLLUTANTS.keys())].mean()
    pivot_norm = (pivot - pivot.min()) / (pivot.max() - pivot.min() + 1e-9)

    hover_texts = []
    for sido in pivot.index:
        row = []
        for p in POLLUTANTS:
            row.append(f"{sido} | {POLLUTANTS[p]['label']}<br>평균: {pivot.loc[sido,p]:.3f} {POLLUTANTS[p]['unit']}")
        hover_texts.append(row)

    fig6 = go.Figure(data=go.Heatmap(
        z=pivot_norm.values,
        x=[POLLUTANTS[p]['label'].split('(')[0].strip() for p in POLLUTANTS],
        y=pivot.index.tolist(),
        colorscale='RdYlGn_r',
        text=[[f"{pivot.loc[s,p]:.3f}" for p in POLLUTANTS] for s in pivot.index],
        texttemplate="%{text}",
        hovertext=hover_texts,
        hovertemplate="%{hovertext}<extra></extra>",
    ))
    fig6.update_layout(
        paper_bgcolor=PLOTLY_PAPER_BG, plot_bgcolor=PLOTLY_PLOT_BG,
        height=240, margin=dict(l=10,r=10,t=10,b=10),
    )
    st.plotly_chart(fig6, use_container_width=True)

    # 측정망 유형별 비교
    st.markdown('<div class="section-title">측정망 유형별 오염물질 평균 비교</div>', unsafe_allow_html=True)
    by_mang = dff.groupby('망')[list(POLLUTANTS.keys())].mean().reset_index()
    fig7 = px.bar(
        by_mang.melt(id_vars='망', value_vars=list(POLLUTANTS.keys()),
                     var_name='오염물질', value_name='평균농도'),
        x='오염물질', y='평균농도', color='망', barmode='group',
        template=PLOTLY_TEMPLATE,
        labels={'오염물질':'오염물질','평균농도':'정규화 평균'},
    )
    fig7.update_layout(
        paper_bgcolor=PLOTLY_PAPER_BG, plot_bgcolor=PLOTLY_PLOT_BG,
        height=300, margin=dict(l=10,r=10,t=10,b=10),
        legend=dict(orientation='h', y=1.1),
    )
    st.plotly_chart(fig7, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 3: 시간대 패턴
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="section-title">시간대별 평균 농도 (24h)</div>', unsafe_allow_html=True)
        hourly = dff.groupby('시간')[list(POLLUTANTS.keys())].mean().reset_index()
        fig8 = go.Figure()
        for p, meta in POLLUTANTS.items():
            # 정규화
            mn, mx = hourly[p].min(), hourly[p].max()
            norm_vals = (hourly[p] - mn) / (mx - mn + 1e-9)
            fig8.add_trace(go.Scatter(
                x=hourly['시간'], y=norm_vals,
                mode='lines+markers', name=meta['label'].split('(')[0].strip(),
                line=dict(color=meta['color'], width=2),
                marker=dict(size=4),
                hovertemplate=f"{meta['label']}<br>시간: %{{x}}시<br>정규화값: %{{y:.2f}}<extra></extra>",
            ))
        fig8.update_layout(
            paper_bgcolor=PLOTLY_PAPER_BG, plot_bgcolor=PLOTLY_PLOT_BG,
            height=340, margin=dict(l=10,r=10,t=10,b=10),
            xaxis=dict(tickvals=list(range(1,25)), ticktext=[f"{h}시" for h in range(1,25)]),
            yaxis_title='정규화 평균 (0~1)',
            legend=dict(orientation='h', y=1.08),
            hovermode='x unified',
        )
        st.plotly_chart(fig8, use_container_width=True)

    with c2:
        st.markdown('<div class="section-title">요일별 PM2.5 / PM10 패턴</div>', unsafe_allow_html=True)
        dff3 = dff.copy()
        dff3['요일'] = dff3['날짜'].dt.day_name()
        dow_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
        dow_kr    = ['월','화','수','목','금','토','일']
        dow_map   = dict(zip(dow_order, dow_kr))
        dff3['요일_kr'] = dff3['요일'].map(dow_map)

        dow_avg = dff3.groupby('요일')[['PM25','PM10']].mean().reindex(dow_order).reset_index()
        dow_avg['요일_kr'] = dow_kr

        fig9 = go.Figure()
        fig9.add_trace(go.Bar(x=dow_avg['요일_kr'], y=dow_avg['PM25'],
                              name='PM2.5', marker_color='#f59e0b'))
        fig9.add_trace(go.Bar(x=dow_avg['요일_kr'], y=dow_avg['PM10'],
                              name='PM10', marker_color='#fb923c'))
        fig9.update_layout(
            paper_bgcolor=PLOTLY_PAPER_BG, plot_bgcolor=PLOTLY_PLOT_BG,
            height=340, margin=dict(l=10,r=10,t=10,b=10),
            barmode='group', yaxis_title='㎍/㎥',
            legend=dict(orientation='h', y=1.08),
        )
        st.plotly_chart(fig9, use_container_width=True)

    # 시간대 × 날짜 히트맵
    st.markdown('<div class="section-title">시간대 × 날짜 PM2.5 히트맵</div>', unsafe_allow_html=True)
    pivot2 = dff.groupby(['날짜','시간'])['PM25'].mean().reset_index()
    pivot2['날짜_str'] = pivot2['날짜'].dt.strftime('%m/%d')
    pivot2_table = pivot2.pivot(index='시간', columns='날짜_str', values='PM25')

    fig10 = go.Figure(data=go.Heatmap(
        z=pivot2_table.values,
        x=pivot2_table.columns.tolist(),
        y=[f"{h}시" for h in pivot2_table.index],
        colorscale='YlOrRd',
        colorbar=dict(title='PM2.5<br>(㎍/㎥)'),
        hovertemplate='날짜: %{x}<br>시간: %{y}<br>PM2.5: %{z:.1f} ㎍/㎥<extra></extra>',
    ))
    fig10.update_layout(
        paper_bgcolor=PLOTLY_PAPER_BG, plot_bgcolor=PLOTLY_PLOT_BG,
        height=380, margin=dict(l=10,r=10,t=10,b=10),
        xaxis=dict(tickangle=-45, tickfont=dict(size=8)),
    )
    st.plotly_chart(fig10, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 4: 오염물질 분포
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="section-title">오염물질별 분포 (바이올린)</div>', unsafe_allow_html=True)
        p_sel2 = st.selectbox("오염물질", list(POLLUTANTS.keys()),
                               format_func=lambda x: POLLUTANTS[x]['label'], key='dist_p')
        fig11 = px.violin(
            dff, x='시도', y=p_sel2, color='시도',
            box=True, points=False,
            template=PLOTLY_TEMPLATE,
            labels={p_sel2: POLLUTANTS[p_sel2]['unit']},
        )
        fig11.update_layout(
            paper_bgcolor=PLOTLY_PAPER_BG, plot_bgcolor=PLOTLY_PLOT_BG,
            height=360, margin=dict(l=10,r=10,t=10,b=10),
            showlegend=False,
        )
        st.plotly_chart(fig11, use_container_width=True)

    with c2:
        st.markdown('<div class="section-title">등급 분포 파이차트</div>', unsafe_allow_html=True)
        p_sel3 = st.selectbox("오염물질", list(POLLUTANTS.keys()),
                               format_func=lambda x: POLLUTANTS[x]['label'], key='pie_p')
        grades_cfg = POLLUTANTS[p_sel3]['grades']
        def classify(v):
            for lo, hi, name, _ in grades_cfg:
                if lo <= v < hi:
                    return name
            return "측정불가"
        grade_series = dff[p_sel3].dropna().apply(classify)
        grade_counts = grade_series.value_counts().reset_index()
        grade_counts.columns = ['등급','건수']
        grade_color_map = {name: color for _, _, name, color in grades_cfg}
        fig12 = px.pie(
            grade_counts, names='등급', values='건수',
            color='등급', color_discrete_map=grade_color_map,
            hole=0.4, template=PLOTLY_TEMPLATE,
        )
        fig12.update_layout(
            paper_bgcolor=PLOTLY_PAPER_BG,
            height=360, margin=dict(l=10,r=10,t=10,b=10),
        )
        st.plotly_chart(fig12, use_container_width=True)

    # 상관관계 히트맵
    st.markdown('<div class="section-title">오염물질 간 상관관계</div>', unsafe_allow_html=True)
    corr = dff[list(POLLUTANTS.keys())].corr()
    labels_corr = [POLLUTANTS[p]['label'].split('(')[0].strip() for p in POLLUTANTS]

    fig13 = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=labels_corr, y=labels_corr,
        colorscale='RdBu_r',
        zmin=-1, zmax=1,
        text=corr.round(2).values,
        texttemplate="%{text}",
        hovertemplate='%{y} ↔ %{x}<br>상관계수: %{z:.2f}<extra></extra>',
    ))
    fig13.update_layout(
        paper_bgcolor=PLOTLY_PAPER_BG, plot_bgcolor=PLOTLY_PLOT_BG,
        height=280, margin=dict(l=10,r=10,t=10,b=10),
    )
    st.plotly_chart(fig13, use_container_width=True)

    # 산점도
    st.markdown('<div class="section-title">오염물질 산점도</div>', unsafe_allow_html=True)
    cc1, cc2 = st.columns(2)
    with cc1:
        x_p = st.selectbox("X축", list(POLLUTANTS.keys()), index=0,
                            format_func=lambda x: POLLUTANTS[x]['label'], key='scat_x')
    with cc2:
        y_p = st.selectbox("Y축", list(POLLUTANTS.keys()), index=1,
                            format_func=lambda x: POLLUTANTS[x]['label'], key='scat_y')

    sample = dff[[x_p, y_p, '시도']].dropna().sample(min(3000, len(dff)), random_state=42)
    fig14 = px.scatter(
        sample, x=x_p, y=y_p, color='시도',
        opacity=0.5, template=PLOTLY_TEMPLATE,
        trendline='ols',
        labels={x_p: POLLUTANTS[x_p]['unit'], y_p: POLLUTANTS[y_p]['unit']},
    )
    fig14.update_layout(
        paper_bgcolor=PLOTLY_PAPER_BG, plot_bgcolor=PLOTLY_PLOT_BG,
        height=320, margin=dict(l=10,r=10,t=10,b=10),
    )
    st.plotly_chart(fig14, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 5: 측정소 상세
# ════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-title">측정소별 상세 조회</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 3])

    with c1:
        sel_sido2 = st.selectbox("시·도", sorted(dff['시도'].unique()), key='detail_sido')
        stations = sorted(dff[dff['시도']==sel_sido2]['측정소명'].unique())
        sel_station = st.selectbox("측정소", stations, key='detail_station')

    station_df = dff[(dff['시도']==sel_sido2) & (dff['측정소명']==sel_station)].sort_values('날짜시간')

    with c2:
        # 측정소 KPI
        kk = st.columns(6)
        for i, (p, meta) in enumerate(POLLUTANTS.items()):
            mv = station_df[p].mean()
            g_name, g_color = get_grade(mv, meta['grades']) if not np.isnan(mv) else ("N/A","#64748b")
            mv_str = f"{mv:.3f}" if mv < 1 else f"{mv:.1f}"
            with kk[i]:
                st.markdown(f"""
                <div class="kpi-card">
                  <div class="kpi-label">{meta['label'].split('(')[0].strip()}</div>
                  <div class="kpi-value" style="color:{g_color}">
                    {mv_str}
                  </div>
                  <div class="kpi-unit">{g_name}</div>
                </div>
                """, unsafe_allow_html=True)

    # 측정소 시계열
    st.markdown(f'<div class="section-title">{sel_station} — 시간별 오염물질 추이</div>', unsafe_allow_html=True)

    fig15 = make_subplots(rows=3, cols=2, subplot_titles=[
        POLLUTANTS[p]['label'] for p in POLLUTANTS
    ], vertical_spacing=0.12, horizontal_spacing=0.08)

    positions = [(1,1),(1,2),(2,1),(2,2),(3,1),(3,2)]
    for idx, (p, meta) in enumerate(POLLUTANTS.items()):
        r, c = positions[idx]
        data_p = station_df[['날짜시간', p]].dropna()
        fig15.add_trace(
            go.Scatter(x=data_p['날짜시간'], y=data_p[p],
                       mode='lines', name=meta['label'].split('(')[0].strip(),
                       line=dict(color=meta['color'], width=1.5),
                       hovertemplate=f"{meta['label']}<br>%{{x}}<br>%{{y:.4f}} {meta['unit']}<extra></extra>"),
            row=r, col=c
        )
        fig15.update_yaxes(title_text=meta['unit'], row=r, col=c)

    fig15.update_layout(
        paper_bgcolor=PLOTLY_PAPER_BG, plot_bgcolor=PLOTLY_PLOT_BG,
        height=680, margin=dict(l=10,r=10,t=40,b=10),
        showlegend=False, template=PLOTLY_TEMPLATE,
    )
    for i in fig15['layout']['annotations']:
        i['font'] = dict(size=11, color='#94a3b8')

    st.plotly_chart(fig15, use_container_width=True)

    # 원시 데이터 테이블
    with st.expander("📋 원시 데이터 보기"):
        show_cols = ['날짜시간','측정소명','망'] + list(POLLUTANTS.keys())
        st.dataframe(
            station_df[show_cols].reset_index(drop=True).style.format({
                p: ("{:.4f}" if dff[p].mean() < 1 else "{:.1f}") for p in POLLUTANTS
            }),
            height=300,
            use_container_width=True,
        )
