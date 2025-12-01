import streamlit as st
from models.project import (
    add_project_to_db, get_projects_from_db, update_project_in_db,
    get_project_original_info, delete_project_from_db
)

# 프로젝트 페이지
def project_page():
    st.title("📁 프로젝트")
    
    # 세션 상태 초기화
    if 'show_add_modal' not in st.session_state:
        st.session_state.show_add_modal = False
    
    if 'show_edit_modal' not in st.session_state:
        st.session_state.show_edit_modal = False
        
    if 'edit_project_id' not in st.session_state:
        st.session_state.edit_project_id = None
    
    if 'selected_project' not in st.session_state:
        st.session_state.selected_project = None
    
    # 프로젝트 추가 버튼
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("➕ 프로젝트 추가", type="primary"):
            st.session_state.show_add_modal = True
    
    # 프로젝트 추가 모달
    if st.session_state.show_add_modal:
        with st.container():
            st.markdown("### 새 프로젝트 추가")
            
            with st.form("add_project_form"):
                project_name = st.text_input("프로젝트 명", placeholder="프로젝트 이름을 입력하세요")
                account_id = st.text_input("Account ID", placeholder="AWS Account ID를 입력하세요")
                region = st.selectbox("리전", [
                    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
                    "ap-northeast-1", "ap-northeast-2", "ap-southeast-1", "ap-southeast-2",
                    "eu-west-1", "eu-west-2", "eu-central-1"
                ])
                access_key = st.text_input("Access Key", placeholder="AWS Access Key를 입력하세요", type="password")
                secret_key = st.text_input("Secret Key", placeholder="AWS Secret Key를 입력하세요", type="password")
                
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    submitted = st.form_submit_button("추가", type="primary")
                with col2:
                    cancelled = st.form_submit_button("취소")
                
                if submitted:
                    if project_name and account_id and region and access_key and secret_key:
                        if add_project_to_db(project_name, account_id, region, access_key, secret_key):
                            st.session_state.show_add_modal = False
                            st.success(f"프로젝트 '{project_name}'이(가) 추가되었습니다!")
                            st.rerun()
                        else:
                            st.error("프로젝트 추가에 실패했습니다.")
                    else:
                        st.error("모든 필드를 입력해주세요.")
                
                if cancelled:
                    st.session_state.show_add_modal = False
                    st.rerun()
    
    # 프로젝트 수정 모달
    if st.session_state.show_edit_modal and st.session_state.edit_project_id:
        project_info = get_project_original_info(st.session_state.edit_project_id)
        if project_info:
            with st.container():
                st.markdown("### 프로젝트 수정")
                
                with st.form("edit_project_form"):
                    edit_project_name = st.text_input("프로젝트 명", value=project_info['project_name'])
                    edit_account_id = st.text_input("Account ID", value=project_info['account_id'])
                    regions = ["us-east-1", "us-east-2", "us-west-1", "us-west-2", "ap-northeast-1", "ap-northeast-2", "ap-southeast-1", "ap-southeast-2", "eu-west-1", "eu-west-2", "eu-central-1"]
                    region_index = regions.index(project_info['region']) if project_info['region'] in regions else 0
                    edit_region = st.selectbox("리전", regions, index=region_index)
                    edit_access_key = st.text_input("Access Key", value=project_info['access_key'], type="password")
                    edit_secret_key = st.text_input("Secret Key", value=project_info['secret_key'], type="password")
                    
                    col1, col2, col3 = st.columns([1, 1, 2])
                    with col1:
                        edit_submitted = st.form_submit_button("수정", type="primary")
                    with col2:
                        edit_cancelled = st.form_submit_button("취소")
                    
                    if edit_submitted:
                        if edit_project_name and edit_account_id and edit_region and edit_access_key and edit_secret_key:
                            if update_project_in_db(st.session_state.edit_project_id, edit_project_name, edit_account_id, edit_region, edit_access_key, edit_secret_key):
                                st.session_state.show_edit_modal = False
                                st.session_state.edit_project_id = None
                                st.success(f"프로젝트 '{edit_project_name}'이(가) 수정되었습니다!")
                                st.rerun()
                            else:
                                st.error("프로젝트 수정에 실패했습니다.")
                        else:
                            st.error("모든 필드를 입력해주세요.")
                    
                    if edit_cancelled:
                        st.session_state.show_edit_modal = False
                        st.session_state.edit_project_id = None
                        st.rerun()
    
    # 프로젝트 목록
    st.markdown("### 프로젝트 목록")
    projects = get_projects_from_db()
    
    if not projects:
        st.info("등록된 프로젝트가 없습니다. 새 프로젝트를 추가해주세요.")
    else:
        for project in projects:
            with st.expander(f"{project['project_name']} - {project['region']}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**프로젝트 명:** {project['project_name']}")
                    st.write(f"**Account ID:** {project['account_id']}")
                    st.write(f"**리전:** {project['region']}")
                with col2:
                    st.write(f"**Access Key:** {project['access_key']}")
                    st.write(f"**Secret Key:** {project['secret_key']}")
                with col3:
                    col3_1, col3_2, col3_3, col3_4, col3_5, col3_6 = st.columns(6)
                    with col3_1:
                        if st.button(f"🗺️ 구성도", key=f"diagram_{project['id']}"):
                            st.session_state.selected_project = project['project_name']
                            st.session_state.current_page = "구성도"
                            st.rerun()
                    with col3_2:
                        if st.button(f"📋 인벤토리", key=f"inventory_{project['id']}"):
                            st.session_state.selected_project = project['project_name']
                            st.session_state.selected_project_for_inventory = project['project_name']
                            st.session_state.current_page = "인벤토리"
                            st.rerun()
                    with col3_3:
                        if st.button(f"💼 워크로드", key=f"workload_{project['id']}"):
                            st.session_state.selected_project = project['project_name']
                            st.session_state.current_page = "워크로드"
                            st.rerun()
                    with col3_4:
                        if st.button(f"🔒 보안점검", key=f"security_{project['id']}"):
                            st.session_state.selected_project = project['project_name']
                            st.session_state.current_page = "보안점검"
                            st.rerun()
                    with col3_5:
                        if st.button(f"✏️ 수정", key=f"edit_{project['id']}"):
                            st.session_state.show_edit_modal = True
                            st.session_state.edit_project_id = project['id']
                            st.rerun()
                    with col3_6:
                        if st.button(f"🗑️ 삭제", key=f"delete_{project['id']}"):
                            if delete_project_from_db(project['id']):
                                st.success("프로젝트가 삭제되었습니다.")
                                st.rerun()
                            else:
                                st.error("프로젝트 삭제에 실패했습니다.")