import streamlit as st
import pandas as pd
from models.project import get_project_names, get_project_info, get_projects_from_db
from utils.aws_session import create_aws_session

def filter_project_names_by_permission(project_names):
    """사용자 권한에 따라 프로젝트명 필터링"""
    user_projects = st.session_state.get('user_projects', '')
    if user_projects == 'all':
        return project_names
    elif not user_projects:
        return []
    else:
        allowed_ids = [int(pid) for pid in user_projects.split(',') if pid.strip()]
        all_projects = get_projects_from_db()
        allowed_project_names = [p['project_name'] for p in all_projects if p['id'] in allowed_ids]
        return [name for name in project_names if name in allowed_project_names]
from config.database import update_security_score
from services.aws_security_check import (
    check_s3_public_access, check_sg_open_to_world, check_iam_mfa,
    check_root_account, check_cloudtrail_logging
)

# 보안점검 페이지
def security_page():
    st.title("🔒 보안점검")
    
    # 선택된 프로젝트 표시
    if 'selected_project' in st.session_state and st.session_state.selected_project:
        st.info(f"프로젝트: **{st.session_state.selected_project}**")
        if st.button("← 프로젝트 목록으로 돌아가기", key="back_to_projects_security"):
            st.session_state.selected_project = None
            st.session_state.current_page = "프로젝트"
            st.rerun()
    
    # 프로젝트 선택
    all_project_names = get_project_names()
    project_names = filter_project_names_by_permission(all_project_names)
    
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
            
            # AWS 보안점검 수행
            with st.spinner(f"{selected_project} 프로젝트의 보안점검을 수행하고 있습니다..."):
                project_info = get_project_info(selected_project)
                if project_info:
                    session = create_aws_session(
                        project_info['access_key'],
                        project_info['secret_key'],
                        project_info['region']
                    )
                    
                    if session:
                        # 보안점검 항목들
                        st.subheader("AWS 보안점검 결과")
                        
                        # 1. S3 Public 여부
                        st.markdown("### 1. S3 Public Access 점검")
                        s3_results = check_s3_public_access(session)
                        if not s3_results.empty:
                            # 취약함 항목을 빨간색으로 표시
                            def highlight_vulnerable(row):
                                if row['취약성여부'] == '취약함':
                                    return ['color: red'] * len(row)
                                elif row['취약성여부'] == '양호함':
                                    return ['color: blue'] * len(row)
                                return [''] * len(row)
                            
                            styled_s3 = s3_results.style.apply(highlight_vulnerable, axis=1)
                            st.dataframe(styled_s3, use_container_width=True)
                        else:
                            st.info("S3 버킷이 없습니다.")
                        
                        # 2. Security Group Inbound 0.0.0.0/0
                        st.markdown("### 2. Security Group Inbound 0.0.0.0/0 점검")
                        sg_results = check_sg_open_to_world(session)
                        if not sg_results.empty:
                            def highlight_vulnerable_sg(row):
                                if row['취약성여부'] == '취약함':
                                    return ['color: red'] * len(row)
                                elif row['취약성여부'] == '양호함':
                                    return ['color: blue'] * len(row)
                                return [''] * len(row)
                            
                            styled_sg = sg_results.style.apply(highlight_vulnerable_sg, axis=1)
                            st.dataframe(styled_sg, use_container_width=True)
                        else:
                            st.info("Security Group이 없습니다.")
                        
                        # 3. IAM 사용자 MFA
                        st.markdown("### 3. IAM 사용자 MFA 활성화 점검")
                        iam_results = check_iam_mfa(session)
                        if not iam_results.empty:
                            def highlight_vulnerable_iam(row):
                                if row['취약성여부'] == '취약함':
                                    return ['color: red'] * len(row)
                                elif row['취약성여부'] == '양호함':
                                    return ['color: blue'] * len(row)
                                return [''] * len(row)
                            
                            styled_iam = iam_results.style.apply(highlight_vulnerable_iam, axis=1)
                            st.dataframe(styled_iam, use_container_width=True)
                        else:
                            st.info("IAM 사용자가 없습니다.")
                        
                        # 4. Root 계정 사용 및 액세스키
                        st.markdown("### 4. Root 계정 사용 및 액세스키 점검")
                        root_results = check_root_account(session)
                        if not root_results.empty:
                            def highlight_vulnerable_root(row):
                                if row['취약성여부'] == '취약함':
                                    return ['color: red'] * len(row)
                                elif row['취약성여부'] == '양호함':
                                    return ['color: blue'] * len(row)
                                elif row['취약성여부'] == '확인불가':
                                    return ['color: orange'] * len(row)
                                return [''] * len(row)
                            
                            styled_root = root_results.style.apply(highlight_vulnerable_root, axis=1)
                            st.dataframe(styled_root, use_container_width=True)
                        else:
                            st.info("Root 계정 정보를 확인할 수 없습니다.")
                        
                        # 5. CloudTrail 로그 활성화
                        st.markdown("### 5. CloudTrail 로그 활성화 점검")
                        cloudtrail_results = check_cloudtrail_logging(session)
                        if not cloudtrail_results.empty:
                            def highlight_vulnerable_cloudtrail(row):
                                if row['취약성여부'] == '취약함':
                                    return ['color: red'] * len(row)
                                elif row['취약성여부'] == '양호함':
                                    return ['color: blue'] * len(row)
                                elif row['취약성여부'] == '확인불가':
                                    return ['color: orange'] * len(row)
                                return [''] * len(row)
                            
                            styled_cloudtrail = cloudtrail_results.style.apply(highlight_vulnerable_cloudtrail, axis=1)
                            st.dataframe(styled_cloudtrail, use_container_width=True)
                        else:
                            st.info("CloudTrail 정보를 확인할 수 없습니다.")
                        
                        # 전체 요약
                        st.markdown("---")
                        st.subheader("보안점검 요약")
                        
                        total_vulnerable = 0
                        total_good = 0
                        
                        for df in [s3_results, sg_results, iam_results, root_results, cloudtrail_results]:
                            if not df.empty and '취약성여부' in df.columns:
                                total_vulnerable += len(df[df['취약성여부'] == '취약함'])
                                total_good += len(df[df['취약성여부'] == '양호함'])
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("취약한 항목", total_vulnerable)
                        with col2:
                            st.metric("양호한 항목", total_good)
                        with col3:
                            total_items = total_vulnerable + total_good
                            if total_items > 0:
                                security_score = round((total_good / total_items) * 100, 1)
                                st.metric("보안 점수", f"{security_score}%")
                                
                                # 보안점수를 DB에 저장
                                if update_security_score(selected_project, security_score):
                                    st.success(f"보안점수 {security_score}%가 저장되었습니다.")
                            else:
                                st.warning("보안점검 항목이 없습니다.")
                    else:
                        st.error("AWS 세션 생성에 실패했습니다.")
                else:
                    st.error("프로젝트 정보를 찾을 수 없습니다.")
        else:
            st.info("프로젝트를 선택하여 보안점검을 수행하세요.")
    else:
        if not all_project_names:
            st.warning("등록된 프로젝트가 없습니다. 프로젝트를 먼저 추가해주세요.")
        else:
            st.warning("접근 가능한 프로젝트가 없습니다. 관리자에게 문의하세요.")