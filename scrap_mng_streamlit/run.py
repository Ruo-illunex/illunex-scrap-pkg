import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from streamlit_timeline import timeline

from core.utils import get_scrap_managers, get_scraper_logs, convert_to_timelinejs_format_with_colors, convert_to_timelinejs_format_with_alerts, convert_error_logs_to_timelinejs_format, create_color_map
from core.functions import create_form, update_form, delete_form, check_html, scrap_test_beautiful_soup


st.set_page_config(
   page_title="Scrap Manager",
   page_icon="🧊",
   layout="wide",
   initial_sidebar_state="expanded",
)


# option = st.sidebar.selectbox(
#     'Menu',
#     ('Scrap Manager', 'Scrap Test', 'Scraper Logs')
# )

with st.sidebar:
    option = option_menu(
        "Menu", ['Scrap Manager', 'Scrap Test', 'Scraper Logs'],
        icons=['house', 'kanban', 'bi bi-robot'],
        menu_icon="app-indicator",
        default_index=0,
        styles={
            "container": {"padding": "4!important", "background-color": "#fafafa"},
            "icon": {"color": "black", "font-size": "25px"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#fafafa"},
            "nav-link-selected": {"background-color": "#08c7b4"},
            }
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
    session_logs_filter = st.selectbox(
        'Filter',
        ('Timeline By Portal', 'Timeline By Status', 'Table'),
        index=1
    )
    if session_logs_filter == 'Timeline By Status':
        timelinejs_json = convert_to_timelinejs_format_with_alerts(scrap_session_logs_df)
    elif session_logs_filter == 'Timeline By Portal':
        timelinejs_json = convert_to_timelinejs_format_with_colors(scrap_session_logs_df)
    elif session_logs_filter == 'Table':
        timelinejs_json = None
        st.dataframe(scrap_session_logs_df)

    if timelinejs_json:
        timeline(timelinejs_json, height=500)

    st.header("Scrap Error Logs")
    error_logs_filter = st.selectbox(
        'Filter',
        ('Timeline', 'Table'),
        index=0
    )

    color_map = create_color_map(scrap_error_logs_df)
    default_color = '#808080'

    if error_logs_filter == 'Timeline':
        timelinejs_json = convert_error_logs_to_timelinejs_format(scrap_error_logs_df, color_map, default_color)
        timeline(timelinejs_json, height=500)
    elif error_logs_filter == 'Table':
        st.dataframe(scrap_error_logs_df)
