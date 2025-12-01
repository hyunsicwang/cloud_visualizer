import streamlit as st
from config.database import create_projects_table, create_member_table, authenticate_user, create_user
from components.dashboard import dashboard_page
from components.projects import project_page
from components.inventory import inventory_page
from components.workload import workload_page
from components.diagram import diagram_page
from components.security import security_page
from components.admin import admin_page

# 로그인 페이지
def login_page():
    # 상단 여백
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["로그인", "회원가입"])
        
        with tab1:
            with st.form("로그인_폼"):
                user_id = st.text_input("아이디")
                password = st.text_input("비밀번호", type="password")
                login_btn = st.form_submit_button("로그인", use_container_width=True)
                
                if login_btn:
                    if user_id and password:
                        user = authenticate_user(user_id, password)
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.user_id = user['id']
                            st.session_state.permission = user['permission']
                            st.session_state.user_projects = user['projects']
                            st.success("로그인 성공!")
                            st.rerun()
                        else:
                            st.error("아이디 또는 비밀번호가 잘못되었습니다.")
                    else:
                        st.error("아이디와 비밀번호를 입력해주세요.")
        
        with tab2:
            with st.form("회원가입_폼"):
                new_user_id = st.text_input("새 아이디")
                new_password = st.text_input("새 비밀번호", type="password")
                signup_btn = st.form_submit_button("회원가입", use_container_width=True)
                
                if signup_btn:
                    if new_user_id and new_password:
                        if create_user(new_user_id, new_password):
                            st.success("회원가입이 완료되었습니다. 로그인해주세요.")
                        # 오류는 create_user 함수에서 처리
                    else:
                        st.error("아이디와 비밀번호를 입력해주세요.")
    
    # 하단에 Cloud Visualizer 아이콘 및 설명
    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
    
    st.markdown(
        """
        <div style="
            text-align: center;
            padding: 40px;
        ">
            <h1 style="
                color: #333; 
                margin-bottom: 10px;
                font-size: 48px;
            ">☁️ Cloud Visualizer</h1>
            <p style="
                color: #666; 
                font-size: 18px;
                margin: 0;
            ">AWS 클라우드 관리 시스템</p>
        </div>
        """,
        unsafe_allow_html=True
    )

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
/* 검은색-은색 색상 변화 애니메이션 */
@keyframes colorShift {
    0% { color: #000000; }
    50% { color: #c0c0c0; }
    100% { color: #000000; }
}

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
st.sidebar.markdown(
    f"""
    <h1 style="
        font-size: 32px;
        font-weight: bold;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        margin-bottom: 0;
        animation: colorShift 2s ease-in-out infinite;
    ">
        ☁️ Cloud Visualizer
    </h1>
    <p style="text-align: center; color: #666; margin: 5px 0;">환영합니다, {st.session_state.get('user_id', '')}님!</p>
    """,
    unsafe_allow_html=True
)

# 로그아웃 버튼
if st.sidebar.button("🚪 로그아웃", use_container_width=True):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
st.sidebar.markdown(
    """
    <div style="
        text-align: center;
        padding: 10px;
        margin: 15px 0;
        background: linear-gradient(135deg, #e3f2fd, #f3e5f5);
        border-radius: 10px;
        border-left: 4px solid #2196f3;
    ">
        <p style="
            margin: 0;
            font-size: 14px;
            color: #1976d2;
            font-weight: 500;
            line-height: 1.4;
        ">
            ✨ 신속한 인프라 현황 파악을 위한<br>솔루션
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
st.sidebar.markdown("---")

# 로그인 체크
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    login_page()
    st.stop()

# 세션 상태 초기화
if 'current_page' not in st.session_state:
    st.session_state.current_page = "대시보드"

# 메뉴 버튼 렌더링
menus = [
    ("대시보드", "📊 대시보드", "dashboard_btn"),
    ("프로젝트", "📁 프로젝트", "project_btn"),
    ("인벤토리", "📋 인벤토리", "inventory_btn"),
    ("워크로드", "💼 워크로드", "workload_btn"),
    ("구성도", "🗺️ 구성도", "diagram_btn"),
    ("보안점검", "🔒 보안점검", "security_btn")
]

# admin 계정일 때 관리자 메뉴 추가
if st.session_state.get('permission') == 'admin':
    menus.append(("관리자 페이지", "👨💼 관리자 페이지", "admin_btn"))

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
create_member_table()

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
elif menu == "보안점검":
    security_page()
elif menu == "관리자 페이지":
    admin_page()

# 푸터
st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="text-align: center; color: #666;">
        <strong>Cloud Visualizer v1.0</strong><br>
        <small>AWS 인프라 관리 도구</small>
    </div>
    """,
    unsafe_allow_html=True
)