import streamlit as st
import pandas as pd
import io
from datetime import datetime
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
from services.aws_ec2 import get_ec2_instances, get_ec2_reserved_instances
from services.aws_database import get_rds_instances, get_rds_reserved_instances, get_elasticache_clusters
from services.aws_storage import get_s3_buckets, get_efs_filesystems
from services.aws_network import get_load_balancers, get_cloudfront_distributions
from services.aws_security import get_waf_webacls, get_acm_certificates
from services.aws_vpc import (
    get_vpcs, get_subnets, get_internet_gateways, get_nat_gateways,
    get_vpn_gateways, get_vpn_connections, get_transit_gateways,
    get_vpc_peering_connections, get_customer_gateways
)

# 인벤토리 페이지
def inventory_page():
    st.title("📋 인벤토리")
    
    # 선택된 프로젝트 표시
    if 'selected_project' in st.session_state and st.session_state.selected_project:
        st.info(f"프로젝트: **{st.session_state.selected_project}**")
        if st.button("← 프로젝트 목록으로 돌아가기", key="back_to_projects_inventory"):
            st.session_state.selected_project = None
            st.session_state.current_page = "프로젝트"
            st.rerun()
    
    # 프로젝트 선택
    all_project_names = get_project_names()
    project_names = filter_project_names_by_permission(all_project_names)
    
    if project_names:
        # 프로젝트에서 인벤토리 버튼을 눌렀을 때 자동 선택
        default_index = 0
        if 'selected_project_for_inventory' in st.session_state and st.session_state.selected_project_for_inventory:
            if st.session_state.selected_project_for_inventory in project_names:
                default_index = project_names.index(st.session_state.selected_project_for_inventory) + 1
        
        # 이전에 선택된 프로젝트가 있으면 유지
        if 'current_inventory_project' in st.session_state:
            if st.session_state.current_inventory_project in project_names:
                default_index = project_names.index(st.session_state.current_inventory_project) + 1
        
        selected_project = st.selectbox(
            "프로젝트",
            ["프로젝트 선택"] + project_names,
            index=default_index
        )
        
        # 선택된 프로젝트를 세션에 저장
        if selected_project != "프로젝트 선택":
            # 프로젝트 변경 시 경고창 상태 초기화
            if 'current_inventory_project' in st.session_state and st.session_state.current_inventory_project != selected_project:
                if f'expiry_warning_shown_{st.session_state.current_inventory_project}' in st.session_state:
                    del st.session_state[f'expiry_warning_shown_{st.session_state.current_inventory_project}']
            st.session_state.current_inventory_project = selected_project
        
    else:
        if not all_project_names:
            st.warning("등록된 프로젝트가 없습니다. 프로젝트를 먼저 추가해주세요.")
        else:
            st.warning("접근 가능한 프로젝트가 없습니다. 관리자에게 문의하세요.")
        selected_project = None
    
    # AWS 리소스 데이터 가져오기
    aws_data = {}
    vpc_data = {}
    if selected_project and selected_project != "프로젝트 선택":
        with st.spinner(f"{selected_project} 프로젝트의 AWS 리소스를 조회하고 있습니다..."):
            project_info = get_project_info(selected_project)
            if project_info:
                session = create_aws_session(
                    project_info['access_key'],
                    project_info['secret_key'],
                    project_info['region']
                )
                if session:
                    # EC2 관련 데이터
                    aws_data = {
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
                    
                    # VPC 관련 데이터
                    vpc_data = {
                        'VPC': get_vpcs(session),
                        'Subnet': get_subnets(session),
                        'Internet Gateway': get_internet_gateways(session),
                        'NAT Gateway': get_nat_gateways(session),
                        'VPN Gateway': get_vpn_gateways(session),
                        'Site-to-Site VPN': get_vpn_connections(session),
                        'Transit Gateway': get_transit_gateways(session),
                        'VPC Peering': get_vpc_peering_connections(session),
                        'Customer Gateway': get_customer_gateways(session)
                    }
        
        # 버튼 영역
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🎨 AWS 구성도 생성", type="primary"):
                st.session_state.selected_project = selected_project
                st.session_state.current_page = "구성도"
                st.rerun()
        with col2:
            if st.button("💼 워크로드 보기", type="secondary"):
                st.session_state.selected_project = selected_project
                st.session_state.current_page = "워크로드"
                st.rerun()
    else:
        # 기본적으로 빈 데이터 표시
        aws_data = {
            'EC2': pd.DataFrame(),
            'RDS': pd.DataFrame(),
            'S3': pd.DataFrame(),
            'ELB': pd.DataFrame(),
            'ElastiCache': pd.DataFrame(),
            'EFS': pd.DataFrame(),
            'CloudFront': pd.DataFrame(),
            'AWS WAF': pd.DataFrame(),
            'ACM': pd.DataFrame(),
            'EC2 RI': pd.DataFrame(),
            'RDS RI': pd.DataFrame()
        }
        vpc_data = {
            'VPC': pd.DataFrame(),
            'Subnet': pd.DataFrame(),
            'Internet Gateway': pd.DataFrame(),
            'NAT Gateway': pd.DataFrame(),
            'VPN Gateway': pd.DataFrame(),
            'Site-to-Site VPN': pd.DataFrame(),
            'Transit Gateway': pd.DataFrame(),
            'VPC Peering': pd.DataFrame(),
            'Customer Gateway': pd.DataFrame()
        }
    
    # 데이터 표시
    if selected_project and selected_project != "프로젝트 선택":
        # [EC2] 섹션 - 기존 리소스 표시
        st.markdown("## [EC2]")
        st.subheader(f"{selected_project} 프로젝트 리소스")
        
        # 만료 예정 항목 체크
        expiring_items = []
        
        for svc_name, df in aws_data.items():
            if not df.empty:
                st.subheader(f"{svc_name} ({len(df)}개)")
                
                # EC2 RI 약정 상태 처리
                if svc_name == 'EC2':
                    # RI 정보 가져오기
                    active_ri_types = set()
                    if 'EC2 RI' in aws_data and not aws_data['EC2 RI'].empty:
                        for _, ri in aws_data['EC2 RI'].iterrows():
                            if ri.get('State') == 'active':
                                active_ri_types.add(ri.get('Instance Type'))
                    
                    # RI 컴럼 추가
                    df_with_ri = df.copy()
                    df_with_ri['RI'] = df_with_ri['Type'].apply(
                        lambda x: 'RI 약정중' if x in active_ri_types else ''
                    )
                    
                    # RI 약정중인 EC2 파란색으로 표시
                    def highlight_ri_instances(row):
                        if row['RI'] == 'RI 약정중':
                            return ['color: blue'] * len(row)
                        return [''] * len(row)
                    
                    styled_df = df_with_ri.style.apply(highlight_ri_instances, axis=1)
                    st.dataframe(styled_df, use_container_width=True)
                
                # RDS RI 약정 상태 처리
                elif svc_name == 'RDS':
                    # RDS RI 정보 가져오기 (타입별 수량 계산)
                    ri_counts = {}
                    if 'RDS RI' in aws_data and not aws_data['RDS RI'].empty:
                        for _, ri in aws_data['RDS RI'].iterrows():
                            if ri.get('State') == 'active':
                                db_class = ri.get('DB Instance Class')
                                instance_count = ri.get('Instance Count', 1)
                                ri_counts[db_class] = ri_counts.get(db_class, 0) + instance_count
                    
                    # 실제 인스턴스 수량 계산
                    instance_counts = df['Class'].value_counts().to_dict()
                    
                    # RI 컴럼 추가
                    df_with_ri = df.copy()
                    ri_status_tracker = {}
                    
                    def get_ri_status(db_class):
                        if db_class not in ri_counts:
                            return ''
                        
                        if db_class not in ri_status_tracker:
                            ri_status_tracker[db_class] = 0
                        
                        ri_status_tracker[db_class] += 1
                        
                        if ri_status_tracker[db_class] <= ri_counts[db_class]:
                            return 'RI 약정중'
                        else:
                            return 'RI 확인필요'
                    
                    df_with_ri['RI'] = df_with_ri['Class'].apply(get_ri_status)
                    
                    # RI 상태에 따른 색상 표시
                    def highlight_rds_ri_instances(row):
                        if row['RI'] == 'RI 약정중':
                            return ['color: blue'] * len(row)
                        elif row['RI'] == 'RI 확인필요':
                            return ['color: orange'] * len(row)
                        return [''] * len(row)
                    
                    styled_df = df_with_ri.style.apply(highlight_rds_ri_instances, axis=1)
                    st.dataframe(styled_df, use_container_width=True)
                
                elif svc_name in ['ACM', 'EC2 RI', 'RDS RI'] and ('만료기간' in df.columns or '만료일시' in df.columns):
                    # 만료기간/만료일시 체크 및 색상 표시
                    def highlight_expiring_items(row):
                        try:
                            expiry_col = '만료기간' if '만료기간' in row.index else '만료일시'
                            if expiry_col in row.index and row[expiry_col] != 'N/A':
                                expire_date = datetime.strptime(row[expiry_col], '%Y-%m-%d')
                                current_date = datetime.now()
                                days_until_expiry = (expire_date - current_date).days
                                if days_until_expiry <= 30:
                                    if svc_name == 'ACM':
                                        expiring_items.append('인증서')
                                    else:
                                        expiring_items.append('RI')
                                    return ['color: red'] * len(row)
                        except:
                            pass
                        return [''] * len(row)
                    
                    styled_df = df.style.apply(highlight_expiring_items, axis=1)
                    st.dataframe(styled_df, use_container_width=True)
                else:
                    st.dataframe(df, use_container_width=True)
        
        # [VPC] 섹션 - VPC 관련 리소스 표시
        st.markdown("## [VPC]")
        st.subheader(f"{selected_project} 프로젝트 VPC 리소스")
        
        # VPC 관련 데이터 표시
        for svc_name, df in vpc_data.items():
            if not df.empty:
                st.subheader(f"{svc_name} ({len(df)}개)")
                st.dataframe(df, use_container_width=True)
        
        # 만료 예정 항목이 있으면 경고창 표시
        warning_key = f'expiry_warning_shown_{selected_project}'
        if expiring_items and warning_key not in st.session_state:
            expiring_types = list(set(expiring_items))
            expiry_text = ' 또는 '.join(expiring_types)
            
            st.error(f"⚠️ **[만료알림]** {expiry_text}가 만료 예정이니, 확인 해주세요!!!")
            if st.button("✅ 확인 완료", key=f"expiry_confirm_{selected_project}"):
                st.session_state[warning_key] = True
                st.rerun()
    else:
        # 프로젝트 선택 안내
        st.info("프로젝트를 선택하여 AWS 리소스를 조회하세요.")
    
    # Excel 다운로드
    if selected_project and selected_project != "프로젝트 선택" and (aws_data or vpc_data):
        # Excel 데이터 준비
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # EC2 관련 데이터
            for svc_name, df in aws_data.items():
                if not df.empty:
                    df.to_excel(writer, sheet_name=svc_name, index=False)
            # VPC 관련 데이터
            for svc_name, df in vpc_data.items():
                if not df.empty:
                    df.to_excel(writer, sheet_name=svc_name, index=False)
        
        st.download_button(
            label="📥 Excel 다운로드",
            data=output.getvalue(),
            file_name=f"aws_inventory_{selected_project}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )