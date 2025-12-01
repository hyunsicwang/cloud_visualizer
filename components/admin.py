import streamlit as st
import pandas as pd
from config.database import get_db_connection
from models.project import get_projects_from_db
from psycopg2 import Error

def get_all_users():
    """모든 사용자 목록 조회"""
    connection = get_db_connection()
    users = []
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT id, permission, projects FROM member ORDER BY id")
            rows = cursor.fetchall()
            users = [{'id': row[0], 'permission': row[1], 'projects': row[2]} for row in rows]
        except Error as e:
            st.error(f"사용자 목록 조회 오류: {e}")
        finally:
            connection.close()
    return users

def update_user_project_permissions(user_id, project_ids):
    """사용자 프로젝트 권한 업데이트"""
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            projects_str = ','.join(map(str, project_ids)) if project_ids else ''
            cursor.execute("UPDATE member SET projects = %s WHERE id = %s", (projects_str, user_id))
            connection.commit()
            return True
        except Error as e:
            st.error(f"권한 업데이트 오류: {e}")
            return False
        finally:
            connection.close()
    return False

def admin_page():
    st.title("👨‍💼 관리자 페이지")
    
    # admin 권한 체크
    if st.session_state.get('permission') != 'admin':
        st.error("관리자 권한이 필요합니다.")
        return
    
    # 사용자 목록 조회
    users = get_all_users()
    all_projects = get_projects_from_db()
    
    if not users:
        st.warning("등록된 사용자가 없습니다.")
        return
    
    if not all_projects:
        st.warning("등록된 프로젝트가 없습니다.")
        return
    
    st.subheader("사용자 권한 관리")
    
    # 사용자 선택
    user_options = [f"{user['id']} ({user['permission']})" for user in users if user['id'] != 'admin']
    if not user_options:
        st.info("관리할 일반 사용자가 없습니다.")
        return
    
    selected_user_display = st.selectbox("사용자 선택", ["사용자 선택"] + user_options)
    
    if selected_user_display != "사용자 선택":
        selected_user_id = selected_user_display.split(' (')[0]
        selected_user = next(user for user in users if user['id'] == selected_user_id)
        
        st.info(f"선택된 사용자: **{selected_user_id}**")
        
        # 현재 사용자의 프로젝트 권한 표시
        current_projects = selected_user['projects']
        if current_projects:
            if current_projects == 'all':
                st.success("현재 권한: 모든 프로젝트 접근 가능")
            else:
                current_project_ids = [int(pid) for pid in current_projects.split(',') if pid.strip()]
                current_project_names = [p['project_name'] for p in all_projects if p['id'] in current_project_ids]
                st.info(f"현재 접근 가능한 프로젝트: {', '.join(current_project_names)}")
        else:
            st.warning("현재 접근 가능한 프로젝트가 없습니다.")
        
        st.markdown("---")
        
        # 프로젝트 선택 (체크박스)
        st.subheader("프로젝트 권한 설정")
        
        # 현재 권한 기반으로 체크박스 초기값 설정
        current_project_ids = []
        if current_projects and current_projects != 'all':
            current_project_ids = [int(pid) for pid in current_projects.split(',') if pid.strip()]
        
        selected_projects = []
        
        # 모든 프로젝트 체크박스
        for project in all_projects:
            is_checked = project['id'] in current_project_ids
            if st.checkbox(
                f"{project['project_name']} (ID: {project['id']})", 
                value=is_checked,
                key=f"project_{project['id']}"
            ):
                selected_projects.append(project['id'])
        
        # 적용 버튼
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔄 적용", type="primary"):
                if update_user_project_permissions(selected_user_id, selected_projects):
                    if selected_projects:
                        project_names = [p['project_name'] for p in all_projects if p['id'] in selected_projects]
                        st.success(f"✅ {selected_user_id} 사용자의 권한이 업데이트되었습니다!")
                        st.success(f"접근 가능한 프로젝트: {', '.join(project_names)}")
                    else:
                        st.success(f"✅ {selected_user_id} 사용자의 모든 프로젝트 권한이 제거되었습니다.")
                    st.rerun()
                else:
                    st.error("권한 업데이트에 실패했습니다.")
        
        # 현재 사용자 목록 표시
        st.markdown("---")
        st.subheader("전체 사용자 현황")
        
        user_status = []
        for user in users:
            if user['projects'] == 'all':
                project_info = "모든 프로젝트"
            elif user['projects']:
                user_project_ids = [int(pid) for pid in user['projects'].split(',') if pid.strip()]
                project_names = [p['project_name'] for p in all_projects if p['id'] in user_project_ids]
                project_info = ', '.join(project_names) if project_names else "없음"
            else:
                project_info = "없음"
            
            user_status.append({
                '사용자 ID': user['id'],
                '권한': user['permission'],
                '접근 가능한 프로젝트': project_info
            })
        
        df = pd.DataFrame(user_status)
        st.dataframe(df, use_container_width=True, hide_index=True)