import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="건강기능식품 트렌드 분석 대시보드",
    page_icon="💊",
    layout="wide"
)

# 데이터 로드 함수
@st.cache_data
def load_data():
    data_dir = "data"
    keywords = ["오메가3", "루테인", "프로바이오틱스", "마그네슘", "밀크씨슬", "유산균"]
    
    trend_dfs = {}
    blog_dfs = {}
    shopping_dfs = {}
    
    for kw in keywords:
        # 트렌드 데이터
        trend_file = f"2025_shopping_trend_{kw}_20260117.csv"
        trend_path = os.path.join(data_dir, trend_file)
        if os.path.exists(trend_path):
            df = pd.read_csv(trend_path)
            df['period'] = pd.to_datetime(df['period'])
            df['keyword'] = kw
            trend_dfs[kw] = df
            
        # 블로그 데이터
        blog_file = f"2026_blog_search_{kw}_20260117.csv"
        blog_path = os.path.join(data_dir, blog_file)
        if os.path.exists(blog_path):
            blog_dfs[kw] = pd.read_csv(blog_path)
            
        # 쇼핑 검색 데이터
        shop_file = f"2026_shopping_search_{kw}_20260117.csv"
        shop_path = os.path.join(data_dir, shop_file)
        if os.path.exists(shop_path):
            shopping_dfs[kw] = pd.read_csv(shop_path)
            
    return trend_dfs, blog_dfs, shopping_dfs

# 메인 타이틀
st.title("💊 건강기능식품 트렌드 분석 대시보드")
st.markdown("네이버 쇼핑 인사이트 및 검색 데이터를 기반으로 한 트렌드 비교 분석 도구입니다.")

# 데이터 불러오기
trend_data, blog_data, shop_data = load_data()
all_keywords = list(trend_data.keys())

# 사이드바 설정
st.sidebar.header("🔍 분석 설정")
selected_keywords = st.sidebar.multiselect(
    "비교할 키워드를 선택하세요",
    all_keywords,
    default=all_keywords[:3]
)

if not selected_keywords:
    st.error("최소 하나 이상의 키워드를 선택해주세요.")
    st.stop()

# 탭 구성
tab1, tab2, tab3 = st.tabs(["📊 트렌드 비교", "🔍 키워드 상세 EDA", "💾 원본 데이터"])

# --- Tab 1: 트렌드 비교 ---
with tab1:
    st.header("📈 키워드별 쇼핑 클릭 트렌드 비교")
    
    # 선택된 키워드 데이터 병합
    combined_trend = pd.concat([trend_data[kw] for kw in selected_keywords])
    
    # 그래프 1: 일별 클릭 트렌드 (Line Chart)
    fig_line = px.line(
        combined_trend, 
        x='period', 
        y='ratio', 
        color='keyword',
        title="일별 클릭 트렌드 변화 (2025년)",
        template="plotly_dark"
    )
    st.plotly_chart(fig_line, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 그래프 2: 키워드별 총 클릭량 (Bar Chart)
        total_clicks = combined_trend.groupby('keyword')['ratio'].sum().reset_index()
        fig_bar = px.bar(
            total_clicks, 
            x='keyword', 
            y='ratio', 
            color='keyword',
            title="키워드별 누적 클릭 지수 합계",
            template="plotly_dark"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # 표 1: 요약 통계량
        st.subheader("📋 키워드별 요약 통계")
        stats_df = combined_trend.groupby('keyword')['ratio'].describe().T
        st.dataframe(stats_df, use_container_width=True)

    with col2:
        # 그래프 3: 클릭량 분포 (Box Plot)
        fig_box = px.box(
            combined_trend, 
            x='keyword', 
            y='ratio', 
            color='keyword',
            title="키워드별 클릭 지수 분포 및 이상치",
            template="plotly_dark"
        )
        st.plotly_chart(fig_box, use_container_width=True)
        
        # 표 2: 전월 대비 성장률 (MoM) - 간소화 버전
        st.subheader("📈 월간 평균 클릭 지수 변화")
        combined_trend['month'] = combined_trend['period'].dt.month
        monthly_avg = combined_trend.groupby(['keyword', 'month'])['ratio'].mean().unstack().T
        st.dataframe(monthly_avg, use_container_width=True)

    # 그래프 4: 요일별 클릭 패턴 (Heatmap)
    combined_trend['day_of_week'] = combined_trend['period'].dt.day_name()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekly_pattern = combined_trend.groupby(['keyword', 'day_of_week'])['ratio'].mean().reset_index()
    
    fig_heatmap = px.density_heatmap(
        weekly_pattern,
        x='day_of_week',
        y='keyword',
        z='ratio',
        category_orders={'day_of_week': day_order},
        title="요일별/키워드별 평균 클릭 강도",
        template="plotly_dark"
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

# --- Tab 2: 키워드 상세 EDA ---
with tab2:
    st.header("🔎 개별 키워드 심층 분석")
    
    detail_kw = st.selectbox("분석할 키워드를 선택하세요", selected_keywords)
    
    col3, col4 = st.columns(2)
    
    with col3:
        # 그래프 5: 월별 클릭 추이 (Area Chart)
        kw_trend = trend_data[detail_kw].copy()
        kw_trend['month'] = kw_trend['period'].dt.to_period('M').astype(str)
        monthly_trend = kw_trend.groupby('month')['ratio'].mean().reset_index()
        fig_area = px.area(
            monthly_trend, 
            x='month', 
            y='ratio', 
            title=f"[{detail_kw}] 월별 평균 클릭 추이",
            template="plotly_dark"
        )
        st.plotly_chart(fig_area, use_container_width=True)
        
        # 표 3: 상위 블로그 검색 결과
        st.subheader(f"📝 {detail_kw} 인기 블로그 (상위 10)")
        if detail_kw in blog_data:
            st.dataframe(blog_data[detail_kw][['title', 'bloggername', 'postdate']], use_container_width=True)
        else:
            st.info("블로그 데이터가 없습니다.")

    with col4:
        # 그래프 6: 히스토그램 (Distribution)
        fig_hist = px.histogram(
            kw_trend, 
            x='ratio', 
            nbins=30,
            title=f"[{detail_kw}] 클릭 지수 빈도 분포",
            template="plotly_dark"
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # 표 4: 상위 쇼핑 검색 결과
        st.subheader(f"🛒 {detail_kw} 네이버 쇼핑 상위 상품")
        if detail_kw in shop_data:
            st.dataframe(shop_data[detail_kw][['title', 'lprice', 'mallName']], use_container_width=True)
        else:
            st.info("쇼핑 데이터가 없습니다.")

    # 표 5: 데이터 무결성 체크
    st.subheader("🛡️ 데이터 품질 리포트")
    quality_info = {
        "총 데이터 수": len(kw_trend),
        "결측치 수": kw_trend['ratio'].isnull().sum(),
        "시작일": kw_trend['period'].min().strftime('%Y-%m-%d'),
        "종료일": kw_trend['period'].max().strftime('%Y-%m-%d'),
        "최대 클릭 지수": kw_trend['ratio'].max()
    }
    st.table(pd.DataFrame([quality_info]))

# --- Tab 3: 원본 데이터 ---
with tab3:
    st.header("🗄️ 수집 데이터 원본 확인")
    
    view_kw = st.radio("데이터를 확인할 키워드 선택", selected_keywords, horizontal=True)
    
    st.subheader(f"[{view_kw}] 쇼핑 트렌드 Raw Data")
    st.dataframe(trend_data[view_kw], use_container_width=True)
    
    # 다운로드 버튼
    csv = trend_data[view_kw].to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label=f"{view_kw} 데이터 CSV 다운로드",
        data=csv,
        file_name=f"{view_kw}_trend_2025.csv",
        mime='text/csv',
    )
