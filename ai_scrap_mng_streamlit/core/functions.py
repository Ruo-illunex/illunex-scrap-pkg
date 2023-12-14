import html
import json

import streamlit as st
import streamlit.components.v1 as components
from bs4 import BeautifulSoup

from core.utils import create_scrap_manager, get_scrap_manager_by_id, update_scrap_manager, delete_scrap_manager, get_html, safe_extract

import streamlit as st
import json


def create_form():
    portal = st.text_input("Portal")
    parsing_target_name = st.selectbox("Parsing Target Name", ["title", "content", "create_date", "image_url", "media", "kind"])
    parsing_method = st.selectbox("Parsing Method", ["bs", "trafilatura"])

    next_button = st.button("Parsing Rule 입력")

    if next_button:
        # 파싱 메소드에 따라 입력 필드 표시
        if parsing_method == "bs":
            with st.expander("Parsing Rule", expanded=True):
                default = st.text_input("Default", help="파싱 실패시 기본 반환 값을 입력하세요.")
                find_option = st.radio("Find Options", ('Select One', 'Find', 'Find All'), help="특정 태그를 찾거나 모든 일치하는 요소를 찾을지 선택하세요.")
                selector = ""
                attribute_name = ""
                tag = ""
                find_attributes = None
                st.markdown('- 둘 중 하나만 선택하세요.')
                col_1, col_2 = st.columns(2)
                with col_1:
                    st.markdown("### Selector")
                    selector = st.text_input("Selector", help="CSS 선택자를 입력하세요.")
                    attribute_name_selector = st.text_input("Attribute Name", help="속성 이름을 입력하세요.", key="attribute_name_selector")

                with col_2:
                    st.markdown("### Find or Find All")
                    tag = st.text_input("Tag", help="찾을 HTML 태그의 이름입니다.")
                    find_attributes_key = st.text_input("Find Attributes Key", help="찾을 속성의 키를 입력하세요.")
                    find_attributes_value = st.text_input("Find Attributes Value", help="찾을 속성의 값을 입력하세요.")
                    find_attributes = {find_attributes_key: find_attributes_value} if find_attributes_key else None
                    attribute_name_find = st.text_input("Attribute Name", help="속성 이름을 입력하세요.", key="attribute_name_find_or_find_all")

                attribute_name = attribute_name_selector if find_option == 'Select One' else attribute_name_find
                parsing_rule = {
                    "selector": selector,
                    "attribute_name": attribute_name,
                    "default": default,
                    "find": find_option == 'Find',
                    "find_all": find_option == 'Find All',
                    "tag": tag,
                    "find_attributes": find_attributes,
                }

        elif parsing_method == "trafilatura":
            path1 = st.text_input("Path1")
            parsing_rule = {
                "path1": path1,
            }

    submit_button = st.form_submit_button("Create")
    if submit_button:

        scrap_manager_data = {
            "portal": portal,
            "parsing_target_name": parsing_target_name,
            "parsing_method": parsing_method,
            "parsing_rule": parsing_rule
        }

        if create_scrap_manager(scrap_manager_data):
            st.success("Scrap Manager created successfully!")
        else:
            st.error("Failed to create Scrap Manager.")


def update_form():
    scrap_manager_id = st.number_input("Enter Scrap Manager ID to Update", min_value=1, step=1)
    
    if st.button("Load Scrap Manager"):
        scrap_manager = get_scrap_manager_by_id(scrap_manager_id)
        if scrap_manager:
            st.session_state.scrap_manager = scrap_manager
        else:
            st.error("Scrap Manager not found.")

    if 'scrap_manager' in st.session_state:
        portal = st.text_input("Portal", value=st.session_state.scrap_manager["portal"])
        parsing_target_name = st.text_input("Parsing Target Name", value=st.session_state.scrap_manager["parsing_target_name"])
        parsing_method = st.selectbox("Parsing Method", ("bs", "trafilatura"), index=0 if st.session_state.scrap_manager["parsing_method"] == "BeautifulSoup" else 1)

        # 파싱 메소드에 따라 입력 필드 표시
        next_button = st.button("Parsing Rule 입력")

        if next_button:
            if parsing_method == "bs":
                # 파싱 규칙 관련 필드
                selector = st.text_input("Selector", value=st.session_state.scrap_manager["parsing_rule"]["selector"])
                attribute_name = st.text_input("Attribute Name", value=st.session_state.scrap_manager["parsing_rule"]["attribute_name"])
                default = st.text_input("Default", value=st.session_state.scrap_manager["parsing_rule"]["default"])
                find = st.checkbox("Find", value=st.session_state.scrap_manager["parsing_rule"]["find"])
                tag = st.text_input("Tag", value=st.session_state.scrap_manager["parsing_rule"]["tag"])
                find_attributes = st.text_input("Find Attributes", value=json.dumps(st.session_state.scrap_manager["parsing_rule"]["find_attributes"]))
                find_all = st.checkbox("Find All", value=st.session_state.scrap_manager["parsing_rule"]["find_all"])

                parsing_rule = {
                    "selector": selector,
                    "attribute_name": attribute_name,
                    "default": default,
                    "find": find,
                    "tag": tag,
                    "find_attributes": json.loads(find_attributes) if find_attributes else None,
                    "find_all": find_all
                }
            
            elif parsing_method == "trafilatura":
                path1 = st.text_input("Path1", value=st.session_state.scrap_manager["parsing_rule"]["path1"])
                parsing_rule = {
                    "path1": path1,
                }

        submitted = st.button("Update")
        if submitted:
            updated_data = {
                "portal": portal,
                "parsing_target_name": parsing_target_name,
                "parsing_method": parsing_method,
                "parsing_rule": parsing_rule
            }
            if update_scrap_manager(scrap_manager_id, updated_data):
                st.success("Scrap Manager updated successfully!")
            else:
                st.error("Failed to update Scrap Manager.")
    
    else:
        st.warning("Please load Scrap Manager first.")


def delete_form():
    scrap_manager_id = st.number_input("Enter Scrap Manager ID to Delete", min_value=1, step=1)

    if st.button("Delete Scrap Manager"):
        if delete_scrap_manager(scrap_manager_id):
            st.success("Scrap Manager deleted successfully!")
        else:
            st.error("Failed to delete Scrap Manager.")


def check_html(test_url):
    if st.button("Check HTML"):
        # streamlit 변수설정
        st.session_state.html = get_html(test_url)
        # 접을 수 있도록 펼침
        code_col, preview_col = st.columns(2)
        height = 600
        with code_col:
                with st.expander("HTML Code Result"):
                    # 사용자 정의 스타일을 적용한 코드 블록
                    components.html(f"""
                        <style>
                            .code-container {{
                                height: 600px; /* 높이 제한 */
                                overflow-y: scroll; /* 세로 스크롤 */
                                background-color: #f0f0f0; /* 밝은 배경색 */
                                color: #333; /* 어두운 글씨 색 */
                            }}
                            pre {{
                                white-space: pre-wrap; /* 코드 줄바꿈 */
                            }}
                        </style>
                        <div class="code-container">
                            <pre>{html.escape(st.session_state.html)}</pre>
                        </div>
                    """, height=height)

        with preview_col:
            components.iframe(test_url, width=800, height=height, scrolling=True)


def scrap_test_beautiful_soup(html):
    with st.container():
        soup = BeautifulSoup(html, 'html.parser')
        selector = st.text_input(label="Enter selector to scrape:", value=None)
        attribute_name = st.text_input(label="Enter attribute to scrape:", value=None)
        default = st.text_input(label="Enter default value to scrape:", value=None)
        find = st.checkbox("Find")
        tag = st.text_input(label="Enter tag to scrape:", value=None)
        # attributes는 dict 형태로 입력
        attributes_key = st.text_input(label="Enter attributes key to scrape:", value=None)
        attributes_value = st.text_input(label="Enter attributes value to scrape:", value=None)
        find_attributes = {attributes_key: attributes_value} if attributes_key else None
        find_all = st.checkbox("Find All")

    if st.button("Scrap"):
        st.session_state.result = safe_extract(
            soup,
            selector=selector,
            attribute_name=attribute_name,
            default=default,
            find=find,
            tag=tag,
            find_attributes=find_attributes,
            find_all=find_all
        )
        if not st.session_state.result:
            st.error("Failed to scrape.", icon="❌")
        else:
            st.success("Scraped successfully!", icon="✅")
            st.write(st.session_state.result)
