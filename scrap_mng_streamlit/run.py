import streamlit as st
import pandas as pd

from core.utils import get_scrap_managers, get_scraper_logs
from core.functions import create_form, update_form, delete_form, check_html, scrap_test_beautiful_soup


st.set_page_config(
   page_title="Scrap Manager",
   page_icon="🧊",
   layout="wide",
   initial_sidebar_state="expanded",
)

# 
option = st.sidebar.selectbox(
    'Menu',
    ('Scrap Manager', 'Scrap Test', 'Scraper Logs')
)

# 스크랩 매니저
if option == 'Scrap Manager':
    st.title("Scrap Manager")

    # 데이터 조회
    st.header("Search Scrap Manager")
    portal = st.selectbox('Portal', (
        'Select',
        'daum',
        'naver',
        'naver_sports',
        'zdnet',
        'venturesquare',
        'the bell',
        'platum',
        'startupn',
        'startuptoday',
        ))
    if st.button("Search"):
        scrap_managers = get_scrap_managers(portal)
        st.write(scrap_managers)


    # 데이터 삽입
    st.header("Create New Scrap Manager")
    create_form()


    # 데이터 업데이트
    st.header("Update Scrap Manager")
    update_form()


    # 데이터 삭제
    st.header("Delete Scrap Manager")
    delete_form()

# 스크랩 테스트
elif option == 'Scrap Test':
    st.title("Scrap Test")

    # 데이터 조회
    st.header("Scrap Test")
    test_url = st.text_input("Enter test url to scrape:")

    # url 입력 후 html 가져오기 및 페이지 렌더링
    check_html(test_url)
    
    # 스크래핑 라이브러리 선택
    scrap_library = st.selectbox(
        'Scrap Library',
        ('Select', 'BeautifulSoup', 'Selenium(Not Supported Yet)')
    )

    if scrap_library == 'BeautifulSoup':
        scrap_test_beautiful_soup(st.session_state.html)

# 스크래퍼 로그
elif option == 'Scraper Logs':
    st.title("Scraper Logs")

    # 데이터 조회
    scraper_logs = get_scraper_logs()
    st.session_state.scrap_session_logs = scraper_logs['scrap_session_logs']
    st.session_state.scrap_error_logs = scraper_logs['scrap_error_logs']

    # pandas 데이터프레임으로 변환
    scrap_session_logs_df = pd.DataFrame(st.session_state.scrap_session_logs)
    scrap_error_logs_df = pd.DataFrame(st.session_state.scrap_error_logs)

    st.header("Scrap Session Logs")
    st.dataframe(scrap_session_logs_df)

    st.header("Scrap Error Logs")
    st.dataframe(scrap_error_logs_df)
