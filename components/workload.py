import streamlit as st
import pandas as pd
from psycopg2 import Error
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
from services.aws_network import get_elb_details, get_route53_records

# 리스너별, 대상그룹별 상세 ELB 정보 조회
def get_detailed_elb_info(session):
    try:
        elb = session.client('elbv2')
        elb_classic = session.client('elb')
        detailed_rows = []
        
        # ALB/NLB 조회
        try:
            response = elb.describe_load_balancers()
            for lb in response['LoadBalancers']:
                lb_arn = lb['LoadBalancerArn']
                lb_name = lb['LoadBalancerName']
                lb_type = lb['Type']
                lb_scheme = lb['Scheme']
                
                # 리스너 조회
                try:
                    listeners = elb.describe_listeners(LoadBalancerArn=lb_arn)['Listeners']
                    for listener in listeners:
                        listener_port = listener['Port']
                        listener_protocol = listener['Protocol']
                        
                        # 대상 그룹 조회
                        target_groups_found = False
                        for action in listener.get('DefaultActions', []):
                            if action['Type'] == 'forward':
                                target_groups = []
                                if 'TargetGroupArn' in action:
                                    target_groups.append(action['TargetGroupArn'])
                                elif 'ForwardConfig' in action and action['ForwardConfig'].get('TargetGroups'):
                                    target_groups = [tg['TargetGroupArn'] for tg in action['ForwardConfig']['TargetGroups']]
                                
                                if target_groups:
                                    target_groups_found = True
                                    for tg_arn in target_groups:
                                        try:
                                            # 대상 그룹 상세 정보
                                            tg_info = elb.describe_target_groups(TargetGroupArns=[tg_arn])['TargetGroups'][0]
                                            tg_name = tg_info['TargetGroupName']
                                            
                                            # 대상 상태 확인 및 EC2 인스턴스 정보 수집
                                            ec2_instances = []
                                            target_health = elb.describe_target_health(TargetGroupArn=tg_arn)
                                            ec2_client = session.client('ec2')
                                            
                                            for target in target_health['TargetHealthDescriptions']:
                                                target_id = target['Target']['Id']
                                                if target_id.startswith('i-'):
                                                    instance_id = target_id
                                                    try:
                                                        ec2_response = ec2_client.describe_instances(InstanceIds=[instance_id])
                                                        for reservation in ec2_response['Reservations']:
                                                            for instance in reservation['Instances']:
                                                                instance_name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
                                                                private_ip = instance.get('PrivateIpAddress', 'N/A')
                                                                ec2_instances.append(f"{instance_name} ({instance_id}, {private_ip})")
                                                    except:
                                                        ec2_instances.append(f"Unknown ({instance_id})")
                                                else:
                                                    # IP 대상인 경우
                                                    ec2_instances.append(f"IP Target ({target_id})")
                                            
                                            detailed_rows.append({
                                                'ELB Name': lb_name,
                                                'Type': lb_type.upper(),
                                                'Scheme': lb_scheme,
                                                'Listener': f"{listener_protocol}:{listener_port}",
                                                'Target Group': tg_name,
                                                'EC2 Instances': ', '.join(ec2_instances) if ec2_instances else 'No Targets'
                                            })
                                        except Exception as tg_error:
                                            detailed_rows.append({
                                                'ELB Name': lb_name,
                                                'Type': lb_type.upper(),
                                                'Scheme': lb_scheme,
                                                'Listener': f"{listener_protocol}:{listener_port}",
                                                'Target Group': 'Error',
                                                'EC2 Instances': 'Error'
                                            })
                        
                        # 대상그룹이 없는 리스너의 경우 (NLB 등)
                        if not target_groups_found:
                            detailed_rows.append({
                                'ELB Name': lb_name,
                                'Type': lb_type.upper(),
                                'Scheme': lb_scheme,
                                'Listener': f"{listener_protocol}:{listener_port}",
                                'Target Group': 'No Target Group',
                                'EC2 Instances': 'N/A'
                            })
                except Exception as listener_error:
                    detailed_rows.append({
                        'ELB Name': lb_name,
                        'Type': lb_type.upper(),
                        'Scheme': lb_scheme,
                        'Listener': 'N/A',
                        'Target Group': 'N/A',
                        'EC2 Instances': 'N/A'
                    })
        except Exception as alb_error:
            pass
        
        # CLB 조회
        try:
            classic_response = elb_classic.describe_load_balancers()
            for clb in classic_response['LoadBalancerDescriptions']:
                clb_name = clb['LoadBalancerName']
                clb_scheme = clb['Scheme']
                
                # 리스너 정보 수집
                for listener in clb['ListenerDescriptions']:
                    listener_info = listener['Listener']
                    protocol = listener_info['Protocol']
                    port = listener_info['LoadBalancerPort']
                    
                    # CLB에 연결된 EC2 인스턴스 정보
                    ec2_instances = []
                    try:
                        instance_health = elb_classic.describe_instance_health(LoadBalancerName=clb_name)
                        ec2_client = session.client('ec2')
                        
                        for instance_state in instance_health['InstanceStates']:
                            instance_id = instance_state['InstanceId']
                            try:
                                ec2_response = ec2_client.describe_instances(InstanceIds=[instance_id])
                                for reservation in ec2_response['Reservations']:
                                    for instance in reservation['Instances']:
                                        instance_name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
                                        private_ip = instance.get('PrivateIpAddress', 'N/A')
                                        ec2_instances.append(f"{instance_name} ({instance_id}, {private_ip})")
                            except:
                                ec2_instances.append(f"Unknown ({instance_id})")
                    except:
                        pass
                    
                    detailed_rows.append({
                        'ELB Name': clb_name,
                        'Type': 'CLB',
                        'Scheme': clb_scheme,
                        'Listener': f"{protocol}:{port}",
                        'Target Group': 'Direct Instance',
                        'EC2 Instances': ', '.join(ec2_instances) if ec2_instances else 'No EC2 Instances'
                    })
        except Exception as clb_error:
            pass
        
        return pd.DataFrame(detailed_rows)
        
    except Exception as e:
        st.error(f"ELB 상세 정보 조회 오류: {e}")
        return pd.DataFrame()

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
                        # 리스너별, 대상그룹별 상세 데이터 생성
                        detailed_data = get_detailed_elb_info(session)
                        route53_data = get_route53_records(session)
                        
                        if not detailed_data.empty:
                            
                            # Load Balancer 상세 정보
                            st.subheader("Load Balancer 상세 정보")
                            st.dataframe(detailed_data, use_container_width=True)
                        else:
                            st.info("등록된 Load Balancer가 없습니다.")
                        
                        # Route53 정보 표시
                        st.markdown("---")
                        st.subheader("Route53 DNS 레코드")
                        
                        if not route53_data.empty:
                            # 영역별로 그룹화
                            zones = route53_data['Zone'].unique()
                            for zone in zones:
                                zone_data = route53_data[route53_data['Zone'] == zone]
                                st.markdown(f"### {zone}")
                                st.dataframe(zone_data.drop('Zone', axis=1), use_container_width=True)
                        else:
                            st.info("등록된 Route53 레코드가 없습니다.")
                    else:
                        st.error("AWS 세션 생성에 실패했습니다.")
                else:
                    st.error("프로젝트 정보를 찾을 수 없습니다.")
        else:
            st.info("프로젝트를 선택하여 Load Balancer 정보를 확인하세요.")
    else:
        if not all_project_names:
            st.warning("등록된 프로젝트가 없습니다. 프로젝트를 먼저 추가해주세요.")
        else:
            st.warning("접근 가능한 프로젝트가 없습니다. 관리자에게 문의하세요.")