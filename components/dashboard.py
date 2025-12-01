import streamlit as st
import pandas as pd
from models.project import get_project_names, get_project_info, get_projects_from_db
from config.database import get_all_security_scores
from utils.aws_session import create_aws_session

def filter_project_names_by_permission(project_names):
    """사용자 권한에 따라 프로젝트명 필터링"""
    user_projects = st.session_state.get('user_projects', '')
    if user_projects == 'all':
        return project_names
    elif not user_projects:
        return []
    else:
        # 프로젝트 ID로 프로젝트명 필터링
        allowed_ids = [int(pid) for pid in user_projects.split(',') if pid.strip()]
        all_projects = get_projects_from_db()
        allowed_project_names = [p['project_name'] for p in all_projects if p['id'] in allowed_ids]
        return [name for name in project_names if name in allowed_project_names]

# 프로젝트별 서비스 현황 조회
def get_project_services_count(project_name):
    project_info = get_project_info(project_name)
    if not project_info:
        return {}
    
    session = create_aws_session(
        project_info['access_key'],
        project_info['secret_key'],
        project_info['region']
    )
    
    if not session:
        return {}
    
    services_count = {}
    
    try:
        # EC2 인스턴스 수
        ec2 = session.client('ec2')
        instances = ec2.describe_instances()
        ec2_count = sum(len(reservation['Instances']) for reservation in instances['Reservations'])
        services_count['EC2'] = ec2_count
    except:
        services_count['EC2'] = 0
    
    try:
        # RDS 인스턴스 수
        rds = session.client('rds')
        db_instances = rds.describe_db_instances()
        services_count['RDS'] = len(db_instances['DBInstances'])
    except:
        services_count['RDS'] = 0
    
    try:
        # S3 버킷 수
        s3 = session.client('s3')
        buckets = s3.list_buckets()
        services_count['S3'] = len(buckets['Buckets'])
    except:
        services_count['S3'] = 0
    
    try:
        # ELB 수
        elb = session.client('elbv2')
        load_balancers = elb.describe_load_balancers()
        services_count['ELB'] = len(load_balancers['LoadBalancers'])
    except:
        services_count['ELB'] = 0
    
    return services_count

# 대시보드 페이지
def dashboard_page():
    st.title("📊 대시보드")
    
    # 프로젝트별 서비스 현황
    st.subheader("🏗️ 프로젝트별 서비스 현황")
    
    all_project_names = get_project_names()
    project_names = filter_project_names_by_permission(all_project_names)
    
    if project_names:
        project_services_list = []
        
        with st.spinner("프로젝트별 서비스 현황을 조회하고 있습니다..."):
            for project_name in project_names:
                services_count = get_project_services_count(project_name)
                
                # 서비스 현황 문자열 생성
                service_summary = []
                for service, count in services_count.items():
                    if count > 0:
                        service_summary.append(f"{service} {count}")
                
                project_services_list.append({
                    '프로젝트명': project_name,
                    '서비스 현황': ', '.join(service_summary) if service_summary else '서비스 없음',
                    'EC2': services_count.get('EC2', 0),
                    'RDS': services_count.get('RDS', 0),
                    'S3': services_count.get('S3', 0),
                    'ELB': services_count.get('ELB', 0)
                })
        
        # DataFrame으로 표시
        if project_services_list:
            services_df = pd.DataFrame(project_services_list)
            st.dataframe(services_df, use_container_width=True, hide_index=True)
            
            # 전체 서비스 요약
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_ec2 = sum(p['EC2'] for p in project_services_list)
                st.metric("전체 EC2", total_ec2)
            with col2:
                total_rds = sum(p['RDS'] for p in project_services_list)
                st.metric("전체 RDS", total_rds)
            with col3:
                total_s3 = sum(p['S3'] for p in project_services_list)
                st.metric("전체 S3", total_s3)
            with col4:
                total_elb = sum(p['ELB'] for p in project_services_list)
                st.metric("전체 ELB", total_elb)
    else:
        if not all_project_names:
            st.info("등록된 프로젝트가 없습니다. 프로젝트를 먼저 추가해주세요.")
        else:
            st.info("접근 가능한 프로젝트가 없습니다. 관리자에게 문의하세요.")
    
    st.markdown("---")
    
    # 보안상태 현황
    st.markdown("---")
    st.subheader("🔒 보안상태 현황")
    
    # DB에서 보안점수 조회 및 권한 필터링
    all_security_data = get_all_security_scores()
    user_projects = st.session_state.get('user_projects', '')
    
    if user_projects == 'all':
        security_data = all_security_data
    elif user_projects:
        # 프로젝트 ID로 필터링
        allowed_ids = [int(pid) for pid in user_projects.split(',') if pid.strip()]
        all_projects = get_projects_from_db()
        allowed_project_names = [p['project_name'] for p in all_projects if p['id'] in allowed_ids]
        security_data = [data for data in all_security_data if data['project'] in allowed_project_names]
    else:
        security_data = []
    
    if security_data:
        # 보안점수별로 정렬 (높은 점수부터)
        security_data.sort(key=lambda x: x['score'], reverse=True)
        
        # 리스트 형식으로 표시
        security_list = []
        for data in security_data:
            project_name = data['project']
            score = data['score']
            
            # 점수에 따른 상태 결정
            if score >= 75:
                status = "양호"
                status_icon = "🟢"
            elif score >= 60:
                status = "주의"
                status_icon = "🟡"
            else:
                status = "위험"
                status_icon = "🔴"
            
            security_list.append({
                '순위': len(security_list) + 1,
                '프로젝트명': project_name,
                '보안점수': f"{score}%",
                '상태': f"{status_icon} {status}"
            })
        
        # DataFrame으로 변환하여 표시
        security_df = pd.DataFrame(security_list)
        st.dataframe(security_df, use_container_width=True, hide_index=True)
        
        # 전체 평균 보안점수
        avg_score = round(sum(data['score'] for data in security_data) / len(security_data), 1)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("전체 프로젝트 수", len(security_data))
        with col2:
            st.metric("평균 보안점수", f"{avg_score}%")
        with col3:
            # 위험 상태 프로젝트 수
            risk_count = len([d for d in security_data if d['score'] < 60])
            st.metric("위험 프로젝트", risk_count)
    else:
        st.info("보안점검을 수행한 프로젝트가 없습니다. 보안점검 메뉴에서 먼저 점검을 수행해주세요.")