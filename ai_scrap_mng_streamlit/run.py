import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from streamlit_timeline import timeline

from core.utils import (
    get_scrap_managers,
    get_scraper_logs,
    convert_to_timelinejs_format_with_colors,
    convert_to_timelinejs_format_with_alerts,
    convert_error_logs_to_timelinejs_format,
    create_color_map, get_data_from_api,
    scrape_missing_news,
    get_token,
    trocr
)
from core.functions import (
    create_form, update_form,
    delete_form, check_html,
    scrap_test_beautiful_soup
)


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
        "Menu",
        ['Scrap Manager', 'Scrap Test', 'Scraper Logs', 'ESG Finance Hub Scraper', 'Missing News Scraper', 'OCR'],
        icons=['house', 'kanban', 'bi bi-robot', 'bi bi-robot', 'bi bi-robot', 'bi bi-robot'],
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
        'esg_economy',
        'greenpost_korea'
        ))
    if st.button("Search"):
        scrap_managers = get_scrap_managers(portal)
        df = pd.DataFrame(scrap_managers)

        # 'parsing_rule' 열이 이미 dict 타입이므로 바로 json_normalize를 사용
        parsing_rules_df = pd.json_normalize(df['parsing_rule'])

        # 원본 데이터프레임에 새 열 추가
        df = df.join(parsing_rules_df)

        # 원래 'parsing_rule' 열 제거
        df.drop(columns=['parsing_rule'], inplace=True)

        # NULL 값을 Python의 None으로 변환
        df.fillna(value=pd.NA, inplace=True)

        # id 칼럼을 인덱스로 사용
        df.set_index('id', inplace=True)

        # 스타일 적용
        styled_df = df.style.set_properties(**{'text-align': 'left'})

        # Streamlit을 사용하여 웹 앱에 DataFrame 표시
        st.dataframe(styled_df)

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
    if len(scrap_session_logs_df) > 20:
        scrap_session_logs_df = scrap_session_logs_df[-20:]
    if len(scrap_error_logs_df) > 100:
        scrap_error_logs_df = scrap_error_logs_df[-100:]

    st.header("Scrap Session Logs(Recent 20)")
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

    st.header("Scrap Error Logs(Recent 100)")
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

# ESG Finance Hub Scraper
elif option == 'ESG Finance Hub Scraper':
    st.title("ESG Finance Hub Scraper")

    # 데이터 조회
    st.session_state.portal_for_data = st.selectbox('Portal', (
        'Select',
        'esg_finance_hub'
        ), index=1)

    st.session_state.data_page_no = st.number_input(
        'Page No',
        min_value=1,
        max_value=100000,
        value=1
        )

    search_button = st.button("Search", key='search_button_for_data_esg_finance_hub')
    if search_button:
        if st.session_state.portal_for_data == 'esg_finance_hub':
            st.session_state.esg_finance_hub_data_df = get_data_from_api(st.session_state.portal_for_data)
            st.session_state.esg_finance_hub_data_df.columns = ['page', 'news_url']
            st.session_state.esg_finance_hub_data_df['domain'] = st.session_state.esg_finance_hub_data_df['news_url'].apply(lambda x: pd.Series(x.split('/')[2]))
            unique_domains = st.session_state.esg_finance_hub_data_df['domain'].unique()

            st.session_state.data_df = st.session_state.esg_finance_hub_data_df[st.session_state.esg_finance_hub_data_df['page'] == st.session_state.data_page_no]

        st.dataframe(st.session_state.data_df)
        st.write(f"Total: {len(st.session_state.esg_finance_hub_data_df)}")

        # 도메인별로 뉴스 개수를 세어봅니다.
        st.write("Number of news by domain:")
        st.bar_chart(st.session_state.esg_finance_hub_data_df['domain'].value_counts())
        st.write("Total domains:", len(unique_domains))

elif option == 'Missing News Scraper':
    st.title("Missing News Scraper")

    # csv 파일 업로드
    st.header("Upload CSV File")
    csv_file = st.file_uploader("Upload CSV File", type=['csv'])
    if csv_file:
        st.write("File Uploaded Successfully")
        st.write("File Name:", csv_file.name)
        st.write("File Type:", csv_file.type)
        st.write("File Size:", csv_file.size, "bytes")

    # 로그인
    if 'token' not in st.session_state:
        st.session_state.token = None
    if st.session_state.token:
        st.success(f"Logged in as {st.session_state.user_id}")
    else:
        st.warning("You need authorized UserID and Password to start scraping.")
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        if st.button('Login', key='login'):
            result = get_token(username, password)
            if result["status"] == "success":
                st.session_state.token = result["token"]
                st.session_state.user_id = username
                st.success("Login successful.")
            else:
                st.error(result["message"])

    # 스크래핑 시작 버튼 (로그인이 되어있어야 활성화)
    if st.button('Start Scraping', key='start_scraping'):
        # 스크래핑 함수 호출 및 응답 처리
        with st.spinner('Scraping... This may take a while.'):
            if st.session_state.token:
                response = scrape_missing_news(csv_file, st.session_state.token)
                if response.status_code == 200:
                    st.success('Scraping completed successfully.')
                    st.json(response.json())
                else:
                    st.error(f'An error occurred: {response.text}')
            else:
                st.error('Login required.')

elif option == 'OCR':
    st.title("OCR")

    # 이미지 파일 업로드
    st.header("Upload Image File")
    image_file = st.file_uploader("Upload Image File", type=['jpg', 'jpeg', 'png'])
    if image_file:
        st.write("File Uploaded Successfully")
        st.image(image_file, caption='Uploaded Image', use_column_width=True)
        st.write("File Name:", image_file.name)
        st.write("File Type:", image_file.type)
        st.write("File Size:", image_file.size, "bytes")

    # OCR 시작 버튼
    if st.button('Start OCR', key='start_ocr'):
        # OCR 함수 호출 및 응답 처리
        with st.spinner('OCR... This may take a while.'):
            response = trocr(image_file)
        if response.status_code == 200:
            st.success('OCR completed successfully.')
            ocr_data = response.json()
            st.write(ocr_data['text'])
        else:
            st.error(f'An error occurred: {response.text}')
