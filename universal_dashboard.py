import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# 1. 인증 정보 로드 (하이브리드 패턴)
load_dotenv()

def get_naver_credentials():
    # Streamlit Secrets 우선 확인 (try-except로 파일 부재 시 예외 처리)
    try:
        if "NAVER_CLIENT_ID" in st.secrets:
            return st.secrets["NAVER_CLIENT_ID"], st.secrets["NAVER_CLIENT_SECRET"]
    except:
        pass # secrets.toml 파일이 없으면 무시하고 환경 변수 확인으로 넘어감
    
    # OS 환경 변수 확인
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    
    return client_id, client_secret

CLIENT_ID, CLIENT_SECRET = get_naver_credentials()

# 2. 페이지 설정
st.set_page_config(
    page_title="범용 네이버 트렌드 대시보드",
    page_icon="🔍",
    layout="wide"
)

# 3. API 호출 함수들
def fetch_search_trend(keyword):
    url = "https://openapi.naver.com/v1/datalab/search"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
        "Content-Type": "application/json"
    }
    
    # 최근 1년 데이터 조회
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    # 검색어 유효성 검사
    if not keyword or not keyword.strip():
        return None

    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": "date",
        "keywordGroups": [
            {"groupName": keyword, "keywords": [keyword]}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=body)
        if response.status_code == 200:
            data = response.json()
            if not data.get('results'):
                 return pd.DataFrame(columns=['period', 'ratio'])
            
            results = data['results'][0]['data']
            df = pd.DataFrame(results)
            df['period'] = pd.to_datetime(df['period'])
            return df
        else:
            st.error(f"데이터랩 API 호출 실패: {response.status_code} - {response.text}")
            return None
        else:
            st.error(f"데이터랩 API 호출 실패: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"에러 발생: {e}")
        return None

def fetch_blog_search(keyword):
    url = "https://openapi.naver.com/v1/search/blog"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }
    params = {"query": keyword, "display": 10, "sort": "sim"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return pd.DataFrame(response.json()['items'])
        return None
    except:
        return None

def fetch_shopping_search(keyword):
    url = "https://openapi.naver.com/v1/search/shop"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }
    params = {"query": keyword, "display": 10, "sort": "sim"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return pd.DataFrame(response.json()['items'])
        return None
    except:
        return None

# 4. 메인 UI
st.title("🚀 범용 네이버 API 트렌드 대시보드")
st.markdown("하나의 검색어로 트렌드, 블로그, 쇼핑 데이터를 즉시 분석합니다.")

# 사이드바 검색
st.sidebar.header("🔍 검색 설정")
search_keyword = st.sidebar.text_input("검색어를 입력하세요", placeholder="예: 오메가3, 전기자전거 등")

if not CLIENT_ID or not CLIENT_SECRET:
    st.error("⚠️ API 키가 설정되지 않았습니다. .env 파일이나 Streamlit Secrets를 확인하세요.")
    st.stop()

if search_keyword:
    with st.spinner(f"'{search_keyword}' 데이터 수집 중..."):
        trend_df = fetch_search_trend(search_keyword)
        blog_df = fetch_blog_search(search_keyword)
        shop_df = fetch_shopping_search(search_keyword)
    
    if trend_df is not None:
        tab1, tab2, tab3 = st.tabs(["📊 트렌드 분석", "🔍 상세 검색 결과", "📈 기초 EDA"])
        
        with tab1:
            st.subheader(f"📈 '{search_keyword}' 쇼핑 클릭 트렌드 (최근 1년)")
            fig = px.line(trend_df, x='period', y='ratio', title=f"{search_keyword} 일별 클릭 추이", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("최고 클릭 지수", f"{trend_df['ratio'].max():.2f}")
            with col2:
                st.metric("평균 클릭 지수", f"{trend_df['ratio'].mean():.2f}")

        with tab2:
            st.subheader("📝 관련 블로그 및 쇼핑 상품")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 인기 블로그")
                if blog_df is not None and not blog_df.empty:
                    for idx, row in blog_df.iterrows():
                        st.markdown(f"- [{row['title']}]({row['link']})")
                else:
                    st.write("블로그 데이터가 없습니다.")
            with c2:
                st.markdown("#### 추천 쇼핑 상품")
                if shop_df is not None and not shop_df.empty:
                    for idx, row in shop_df.iterrows():
                        price = format(int(row['lprice']), ',')
                        st.markdown(f"- **{row['title']}** : {price}원")
                else:
                    st.write("쇼핑 데이터가 없습니다.")

        with tab3:
            st.subheader("📋 데이터 요약 통계")
            st.dataframe(trend_df.describe().T, use_container_width=True)
            
            st.subheader("📅 최근 7일 데이터")
            st.table(trend_df.tail(7))
    else:
        st.warning("데이터를 불러오지 못했습니다. 검색어나 API 설정을 확인하세요.")
else:
    st.info("왼쪽 사이드바에서 검색어를 입력하여 분석을 시작하세요.")
