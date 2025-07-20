import streamlit as st
from psycopg2 import Error
from models.project import get_project_names, get_project_info
from config.database import get_db_connection
from utils.aws_session import create_aws_session
from services.aws_network import get_elb_details

# 워크로드 페이지
def workload_page():
    st.title("💼 워크로드")
    
    # 선택된 프로젝트 표시
    if 'selected_project' in st.session_state and st.session_state.selected_project:
        st.info(f"프로젝트: **{st.session_state.selected_project}**")
        if st.button("← 프로젝트 목록으로 돌아가기", key="back_to_projects_workload"):
            st.session_state.selected_project = None
            st.session_state.current_page = "프로젝트"
            st.rerun()
    
    # 프로젝트 선택
    project_names = get_project_names()
    if project_names:
        default_index = 0
        if 'selected_project' in st.session_state and st.session_state.selected_project:
            if st.session_state.selected_project in project_names:
                default_index = project_names.index(st.session_state.selected_project) + 1
        
        selected_project = st.selectbox(
            "프로젝트",
            ["프로젝트 선택"] + project_names,
            index=default_index
        )
        
        if selected_project != "프로젝트 선택":
            st.session_state.selected_project = selected_project
            
            # ELB 상세 정보 조회
            with st.spinner(f"{selected_project} 프로젝트의 ELB 정보를 조회하고 있습니다..."):
                project_info = get_project_info(selected_project)
                if project_info:
                    # 마스킹되지 않은 실제 키 가져오기
                    connection = get_db_connection()
                    if connection:
                        try:
                            cursor = connection.cursor()
                            cursor.execute("SELECT * FROM project WHERE project_name = %s", (selected_project,))
                            row = cursor.fetchone()
                            if row:
                                columns = [desc[0] for desc in cursor.description]
                                project_info = dict(zip(columns, row))
                        except Error as e:
                            st.error(f"프로젝트 정보 조회 오류: {e}")
                        finally:
                            connection.close()
                    
                    session = create_aws_session(
                        project_info['access_key'],
                        project_info['secret_key'],
                        project_info['region']
                    )
                    
                    if session:
                        elb_details = get_elb_details(session)
                        
                        if not elb_details.empty:
                            # ELB 유형별 요약
                            clb_count = len(elb_details[elb_details['Type'] == 'classic'])
                            alb_count = len(elb_details[elb_details['Type'] == 'application'])
                            nlb_count = len(elb_details[elb_details['Type'] == 'network'])
                            
                            # 요약 카드
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("CLB (Classic)", clb_count)
                            with col2:
                                st.metric("ALB (Application)", alb_count)
                            with col3:
                                st.metric("NLB (Network)", nlb_count)
                            
                            st.markdown("---")
                            
                            # ELB 목록 및 상세 정보
                            st.subheader("Load Balancer 상세 정보")
                            
                            # 유형별로 그룹화
                            for elb_type in ['application', 'network', 'classic']:
                                type_data = elb_details[elb_details['Type'] == elb_type]
                                if not type_data.empty:
                                    type_name = {'application': 'ALB (Application Load Balancer)', 
                                                'network': 'NLB (Network Load Balancer)',
                                                'classic': 'CLB (Classic Load Balancer)'}[elb_type]
                                    
                                    st.markdown(f"### {type_name}")
                                    st.dataframe(type_data, use_container_width=True)
                        else:
                            st.info("등록된 Load Balancer가 없습니다.")
                    else:
                        st.error("AWS 세션 생성에 실패했습니다.")
                else:
                    st.error("프로젝트 정보를 찾을 수 없습니다.")
        else:
            st.info("프로젝트를 선택하여 Load Balancer 정보를 확인하세요.")
    else:
        st.warning("등록된 프로젝트가 없습니다. 프로젝트를 먼저 추가해주세요.")