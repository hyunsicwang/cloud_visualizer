import streamlit as st
from models.project import get_project_names, get_project_info, get_projects_from_db
from config.database import get_db_connection

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
from utils.aws_session import create_aws_session
from utils.diagram_generator import load_drawio_with_xml, generate_aws_drawio_xml
from services.aws_ec2 import get_ec2_instances, get_ec2_reserved_instances
from services.aws_database import get_rds_instances, get_rds_reserved_instances, get_elasticache_clusters
from services.aws_storage import get_s3_buckets, get_efs_filesystems
from services.aws_network import get_load_balancers, get_cloudfront_distributions
from services.aws_security import get_waf_webacls, get_acm_certificates
from services.aws_vpc import (
    get_vpcs, get_subnets, get_internet_gateways, get_nat_gateways,
    get_vpn_gateways, get_transit_gateways, get_vpc_peering_connections
)
from psycopg2 import Error

# VPC 구성도를 위한 전체 AWS 리소스 조회
def get_full_aws_resources(project_name):
    project_info = get_project_info(project_name)
    if not project_info:
        return {}
    
    # 실제 access_key 값 사용 (마스킹되지 않은)
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM project WHERE project_name = %s", (project_name,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                project_info = dict(zip(columns, row))
        except Error as e:
            st.error(f"프로젝트 정보 조회 오류: {e}")
            return {}
        finally:
            connection.close()
    
    session = create_aws_session(
        project_info['access_key'],
        project_info['secret_key'],
        project_info['region']
    )
    
    if not session:
        return {}
    
    # 기본 리소스 + VPC 관련 리소스
    resources = {
        'VPC': get_vpcs(session),
        'Subnet': get_subnets(session),
        'Internet Gateway': get_internet_gateways(session),
        'NAT Gateway': get_nat_gateways(session),
        'VPN Gateway': get_vpn_gateways(session),
        'Transit Gateway': get_transit_gateways(session),
        'VPC Peering': get_vpc_peering_connections(session),
        'EC2': get_ec2_instances(session),
        'RDS': get_rds_instances(session),
        'S3': get_s3_buckets(session),
        'ELB': get_load_balancers(session),
        'ElastiCache': get_elasticache_clusters(session),
        'EFS': get_efs_filesystems(session),
        'CloudFront': get_cloudfront_distributions(session),
        'AWS WAF': get_waf_webacls(session),
        'ACM': get_acm_certificates(session),
        'EC2 RI': get_ec2_reserved_instances(session),
        'RDS RI': get_rds_reserved_instances(session)
    }
    
    return resources

# 구성도 페이지
def diagram_page():
    st.title("🗺️ 구성도")
    
    # 프로젝트 선택
    all_project_names = get_project_names()
    project_names = filter_project_names_by_permission(all_project_names)
    
    if project_names:
        # 선택된 프로젝트가 있으면 기본값으로 설정
        default_index = 0
        if 'selected_project' in st.session_state and st.session_state.selected_project:
            if st.session_state.selected_project in project_names:
                default_index = project_names.index(st.session_state.selected_project) + 1
        
        selected_project = st.selectbox(
            "프로젝트 선택",
            ["프로젝트 선택"] + project_names,
            index=default_index
        )
        
        # 선택된 프로젝트 표시 및 구성도 생성
        if selected_project != "프로젝트 선택":
            st.info(f"선택된 프로젝트: **{selected_project}**")
            
            # 프로젝트 선택 시 전체 AWS 리소스 조회 및 구성도 생성
            with st.spinner(f"{selected_project} 프로젝트의 AWS 구성도를 생성하고 있습니다..."):
                full_aws_data = get_full_aws_resources(selected_project)
            
            # 구성도그리기 페이지로 데이터 전달
            st.session_state.diagram_project = selected_project
            st.session_state.diagram_data = full_aws_data
            
            # Draw.io XML 구성도 생성
            with st.spinner(f"{selected_project} 프로젝트의 AWS 구성도를 생성하고 있습니다..."):
                xml_content = generate_aws_drawio_xml(selected_project, full_aws_data)
                
                if xml_content:
                    # Draw.io 임베드
                    iframe_html = load_drawio_with_xml(xml_content)
                    st.components.v1.html(iframe_html, height=800)
                    
                    # XML 다운로드
                    st.download_button(
                        label="💾 Draw.io XML 다운로드",
                        data=xml_content,
                        file_name=f"{selected_project}_architecture.drawio",
                        mime="application/xml"
                    )
                else:
                    st.error("구성도 생성에 실패했습니다.")
        else:
            st.info("프로젝트를 선택하여 AWS 구성도를 생성하세요.")
    else:
        if not all_project_names:
            st.warning("등록된 프로젝트가 없습니다. 프로젝트를 먼저 추가해주세요.")
        else:
            st.warning("접근 가능한 프로젝트가 없습니다. 관리자에게 문의하세요.")