import streamlit as st
from config.database import create_projects_table
from components.dashboard import dashboard_page
from components.projects import project_page
from components.inventory import inventory_page
from components.workload import workload_page
from components.diagram import diagram_page

# 페이지 설정
st.set_page_config(
    page_title="Cloud Visualizer",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링
st.markdown("""
<style>
/* Streamlit 기본 네비게이션 숨기기 */
.stAppViewContainer > .main > div[data-testid="stSidebarNav"] {
    display: none;
}

/* 상단 메뉴바 숨기기 */
header[data-testid="stHeader"] {
    display: none;
}
/* 기본 버튼 스타일 */
.stButton > button {
    width: 100%;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
    background-color: white;
    color: #262730;
    transition: all 0.3s ease;
    outline: none !important;
    box-shadow: none !important;
}

/* 기본 버튼 호버 */
.stButton > button:hover {
    background-color: #e3f2fd !important;
    border-color: #2196f3 !important;
}

/* 기본 버튼 포커스 */
.stButton > button:focus {
    outline: none !important;
    box-shadow: none !important;
    border-color: #e0e0e0 !important;
}

/* 선택된 메뉴 - 모든 상태에서 빨간색 유지 */
.selected-menu .stButton > button,
.selected-menu .stButton > button:hover,
.selected-menu .stButton > button:focus,
.selected-menu .stButton > button:active,
.selected-menu .stButton > button:visited {
    background-color: #ffebee !important;
    border-color: #f44336 !important;
    color: #d32f2f !important;
    font-weight: 600 !important;
    outline: none !important;
    box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)

# 사이드바 메뉴
st.sidebar.title("☁️ Cloud Visualizer")
st.sidebar.markdown("---")

# 세션 상태 초기화
if 'current_page' not in st.session_state:
    st.session_state.current_page = "대시보드"

# 메뉴 버튼 렌더링
menus = [
    ("대시보드", "📊 대시보드", "dashboard_btn"),
    ("프로젝트", "📁 프로젝트", "project_btn"),
    ("인벤토리", "📋 인벤토리", "inventory_btn"),
    ("워크로드", "💼 워크로드", "workload_btn"),
    ("구성도", "🗺️ 구성도", "diagram_btn")
]

for page_name, button_text, button_key in menus:
    if st.session_state.current_page == page_name:
        st.sidebar.markdown('<div class="selected-menu">', unsafe_allow_html=True)
        if st.sidebar.button(button_text, use_container_width=True, key=button_key):
            # 세션 상태 초기화
            if 'selected_project' in st.session_state:
                del st.session_state.selected_project
            if 'selected_project_for_inventory' in st.session_state:
                del st.session_state.selected_project_for_inventory
            if 'current_inventory_project' in st.session_state:
                del st.session_state.current_inventory_project
            if 'show_add_modal' in st.session_state:
                del st.session_state.show_add_modal
            if 'diagram_xml' in st.session_state:
                del st.session_state.diagram_xml
            st.session_state.current_page = page_name
            st.rerun()
        st.sidebar.markdown('</div>', unsafe_allow_html=True)
    else:
        if st.sidebar.button(button_text, use_container_width=True, key=button_key):
            # 세션 상태 초기화
            if 'selected_project' in st.session_state:
                del st.session_state.selected_project
            if 'selected_project_for_inventory' in st.session_state:
                del st.session_state.selected_project_for_inventory
            if 'current_inventory_project' in st.session_state:
                del st.session_state.current_inventory_project
            if 'show_add_modal' in st.session_state:
                del st.session_state.show_add_modal
            if 'diagram_xml' in st.session_state:
                del st.session_state.diagram_xml
            st.session_state.current_page = page_name
            st.rerun()

menu = st.session_state.current_page

# 앱 시작 시 테이블 생성
create_projects_table()

# 메뉴에 따른 페이지 렌더링
if menu == "대시보드":
    dashboard_page()
elif menu == "프로젝트":
    project_page()
elif menu == "인벤토리":
    inventory_page()
elif menu == "워크로드":
    workload_page()
elif menu == "구성도":
    diagram_page()

# 푸터
st.sidebar.markdown("---")
st.sidebar.markdown("**Cloud Visualizer v1.0**")
st.sidebar.markdown("AWS 인프라 관리 도구")