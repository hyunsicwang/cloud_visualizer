import streamlit as st
import pandas as pd
from datetime import datetime
import io
import psycopg2
from psycopg2 import Error
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import subprocess
import re
import xml.etree.ElementTree as ET
import base64
import urllib.parse
import requests
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

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

# 데이터베이스 연결 함수
def get_db_connection():
    try:
        connection = psycopg2.connect(
            host=os.getenv('DB_HOST', 'aws-0-ap-northeast-2.pooler.supabase.com'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'postgres'),
            user=os.getenv('DB_USER', 'postgres.djbeuniqyujykksekysv'),
            password=os.getenv('DB_PASSWORD', 'gustlr25!@')
        )
        return connection
    except Error as e:
        st.error(f"데이터베이스 연결 오류: {e}")
        return None

# 프로젝트 테이블 생성
def create_projects_table():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project (
                    id SERIAL PRIMARY KEY,
                    project_name VARCHAR(255) NOT NULL,
                    account_id VARCHAR(255) NOT NULL,
                    region VARCHAR(100) NOT NULL,
                    access_key VARCHAR(255) NOT NULL,
                    secret_key VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            connection.commit()
        except Error as e:
            st.error(f"테이블 생성 오류: {e}")
        finally:
            connection.close()

# 프로젝트 추가
def add_project_to_db(project_name, account_id, region, access_key, secret_key):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO project (project_name, account_id, region, access_key, secret_key)
                VALUES (%s, %s, %s, %s, %s)
            """, (project_name, account_id, region, access_key, secret_key))
            connection.commit()
            return True
        except Error as e:
            st.error(f"프로젝트 추가 오류: {e}")
            return False
        finally:
            connection.close()
    return False

# 프로젝트 목록 조회
def get_projects_from_db():
    connection = get_db_connection()
    projects = []
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM project ORDER BY created_at DESC")
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            projects = [dict(zip(columns, row)) for row in rows]
            # access_key 마스킹 처리
            for project in projects:
                project['access_key'] = project['access_key'][:8] + "..."
                project['secret_key'] = "***"
        except Error as e:
            st.error(f"프로젝트 조회 오류: {e}")
        finally:
            connection.close()
    return projects

# 프로젝트 수정
def update_project_in_db(project_id, project_name, account_id, region, access_key, secret_key):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE project 
                SET project_name = %s, account_id = %s, region = %s, access_key = %s, secret_key = %s
                WHERE id = %s
            """, (project_name, account_id, region, access_key, secret_key, project_id))
            connection.commit()
            return True
        except Error as e:
            st.error(f"프로젝트 수정 오류: {e}")
            return False
        finally:
            connection.close()
    return False

# 프로젝트 원본 정보 조회 (마스킹 없이)
def get_project_original_info(project_id):
    connection = get_db_connection()
    project_info = None
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM project WHERE id = %s", (project_id,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                project_info = dict(zip(columns, row))
        except Error as e:
            st.error(f"프로젝트 정보 조회 오류: {e}")
        finally:
            connection.close()
    return project_info

# 프로젝트 삭제
def delete_project_from_db(project_id):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM project WHERE id = %s", (project_id,))
            connection.commit()
            return True
        except Error as e:
            st.error(f"프로젝트 삭제 오류: {e}")
            return False
        finally:
            connection.close()
    return False

# 프로젝트명 목록 조회
def get_project_names():
    connection = get_db_connection()
    project_names = []
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT project_name FROM project ORDER BY project_name")
            results = cursor.fetchall()
            project_names = [row[0] for row in results]
        except Error as e:
            st.error(f"프로젝트명 조회 오류: {e}")
        finally:
            connection.close()
    return project_names

# 프로젝트 정보 조회
def get_project_info(project_name):
    connection = get_db_connection()
    project_info = None
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
        finally:
            connection.close()
    return project_info

# AWS 세션 생성
def create_aws_session(access_key, secret_key, region):
    try:
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        return session
    except Exception as e:
        st.error(f"AWS 세션 생성 오류: {e}")
        return None

# EC2 인스턴스 조회
def get_ec2_instances(session):
    try:
        ec2 = session.client('ec2')
        response = ec2.describe_instances()
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
                instances.append({
                    'Instance ID': instance['InstanceId'],
                    'Name': name,
                    'Type': instance['InstanceType'],
                    'State': instance['State']['Name'],
                    'AZ': instance['Placement']['AvailabilityZone'],
                    'Subnet ID': instance.get('SubnetId', 'N/A')
                })
        return pd.DataFrame(instances)
    except Exception as e:
        st.error(f"EC2 조회 오류: {e}")
        return pd.DataFrame()

# RDS 인스턴스 조회
def get_rds_instances(session):
    try:
        rds = session.client('rds')
        response = rds.describe_db_instances()
        instances = []
        for db in response['DBInstances']:
            instances.append({
                'DB Instance': db['DBInstanceIdentifier'],
                'Engine': db['Engine'],
                'Class': db['DBInstanceClass'],
                'Status': db['DBInstanceStatus'],
                'AZ': db.get('AvailabilityZone', 'N/A')
            })
        return pd.DataFrame(instances)
    except Exception as e:
        st.error(f"RDS 조회 오류: {e}")
        return pd.DataFrame()

# S3 버킷 조회
def get_s3_buckets(session):
    try:
        s3 = session.client('s3')
        response = s3.list_buckets()
        buckets = []
        for bucket in response['Buckets']:
            try:
                location = s3.get_bucket_location(Bucket=bucket['Name'])['LocationConstraint'] or 'us-east-1'
            except:
                location = 'N/A'
            buckets.append({
                'Bucket Name': bucket['Name'],
                'Creation Date': bucket['CreationDate'].strftime('%Y-%m-%d'),
                'Region': location
            })
        return pd.DataFrame(buckets)
    except Exception as e:
        st.error(f"S3 조회 오류: {e}")
        return pd.DataFrame()

# ELB 로드밸런서 조회
def get_load_balancers(session):
    try:
        elb = session.client('elbv2')
        response = elb.describe_load_balancers()
        load_balancers = []
        for lb in response['LoadBalancers']:
            load_balancers.append({
                'Load Balancer': lb['LoadBalancerName'],
                'Type': lb['Type'],
                'Scheme': lb['Scheme'],
                'State': lb['State']['Code'],
                'AZ': ', '.join([az['ZoneName'] for az in lb['AvailabilityZones']])
            })
        return pd.DataFrame(load_balancers)
    except Exception as e:
        st.error(f"ELB 조회 오류: {e}")
        return pd.DataFrame()

# ELB 상세 정보 조회 (워크로드용)
def get_elb_details(session):
    try:
        elb = session.client('elbv2')
        elb_classic = session.client('elb')
        
        # ALB/NLB 조회
        response = elb.describe_load_balancers()
        elb_details = []
        
        for lb in response['LoadBalancers']:
            lb_arn = lb['LoadBalancerArn']
            lb_name = lb['LoadBalancerName']
            lb_type = lb['Type']
            lb_scheme = lb['Scheme']
            
            # 리스너 조회
            listeners = elb.describe_listeners(LoadBalancerArn=lb_arn)['Listeners']
            
            for listener in listeners:
                listener_port = listener['Port']
                listener_protocol = listener['Protocol']
                
                # 대상 그룹 조회
                for action in listener.get('DefaultActions', []):
                    if action['Type'] == 'forward':
                        if 'TargetGroupArn' in action:
                            tg_arn = action['TargetGroupArn']
                        elif 'ForwardConfig' in action:
                            tg_arn = action['ForwardConfig']['TargetGroups'][0]['TargetGroupArn']
                        else:
                            continue
                        
                        # 대상 그룹 상세 정보
                        tg_info = elb.describe_target_groups(TargetGroupArns=[tg_arn])['TargetGroups'][0]
                        tg_name = tg_info['TargetGroupName']
                        tg_port = tg_info['Port']
                        health_check = tg_info['HealthCheckPath'] if 'HealthCheckPath' in tg_info else 'N/A'
                        
                        # 대상 상태 확인 및 EC2 인스턴스 정보 수집
                        target_health = elb.describe_target_health(TargetGroupArn=tg_arn)
                        healthy_count = sum(1 for t in target_health['TargetHealthDescriptions'] if t['TargetHealth']['State'] == 'healthy')
                        total_count = len(target_health['TargetHealthDescriptions'])
                        health_status = f"{healthy_count}/{total_count} Healthy"
                        
                        # EC2 인스턴스 정보 수집
                        ec2_instances = []
                        ec2_client = session.client('ec2')
                        
                        for target in target_health['TargetHealthDescriptions']:
                            if target['Target']['Id'].startswith('i-'):  # EC2 인스턴스인 경우
                                instance_id = target['Target']['Id']
                                try:
                                    # EC2 인스턴스 정보 조회
                                    ec2_response = ec2_client.describe_instances(InstanceIds=[instance_id])
                                    for reservation in ec2_response['Reservations']:
                                        for instance in reservation['Instances']:
                                            instance_name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
                                            ec2_instances.append(f"{instance_name} ({instance_id})")
                                except:
                                    ec2_instances.append(f"Unknown ({instance_id})")
                        
                        ec2_list = ', '.join(ec2_instances) if ec2_instances else 'No EC2 Instances'
                        
                        elb_details.append({
                            'ELB Name': lb_name,
                            'Type': lb_type,
                            'Scheme': lb_scheme,
                            'Listener': f"{listener_protocol}:{listener_port}",
                            'Target Group': tg_name,
                            'Port': tg_port,
                            'Health Check': health_check,
                            'Health Status': health_status,
                            'EC2 Instances': ec2_list
                        })
        
        # CLB 조회
        try:
            classic_response = elb_classic.describe_load_balancers()
            for clb in classic_response['LoadBalancerDescriptions']:
                clb_name = clb['LoadBalancerName']
                clb_scheme = clb['Scheme']
                
                for listener in clb['ListenerDescriptions']:
                    listener_info = listener['Listener']
                    protocol = listener_info['Protocol']
                    port = listener_info['LoadBalancerPort']
                    
                    # CLB는 대상 그룹 대신 인스턴스 직접 연결
                    instance_health = elb_classic.describe_instance_health(LoadBalancerName=clb_name)
                    healthy_count = sum(1 for i in instance_health['InstanceStates'] if i['State'] == 'InService')
                    total_count = len(instance_health['InstanceStates'])
                    health_status = f"{healthy_count}/{total_count} InService"
                    
                    # CLB에 연결된 EC2 인스턴스 정보
                    ec2_instances = []
                    ec2_client = session.client('ec2')
                    
                    for instance_state in instance_health['InstanceStates']:
                        instance_id = instance_state['InstanceId']
                        try:
                            ec2_response = ec2_client.describe_instances(InstanceIds=[instance_id])
                            for reservation in ec2_response['Reservations']:
                                for instance in reservation['Instances']:
                                    instance_name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
                                    ec2_instances.append(f"{instance_name} ({instance_id})")
                        except:
                            ec2_instances.append(f"Unknown ({instance_id})")
                    
                    ec2_list = ', '.join(ec2_instances) if ec2_instances else 'No EC2 Instances'
                    
                    elb_details.append({
                        'ELB Name': clb_name,
                        'Type': 'classic',
                        'Scheme': clb_scheme,
                        'Listener': f"{protocol}:{port}",
                        'Target Group': 'Direct Instance',
                        'Port': 'N/A',
                        'Health Check': 'Instance Health',
                        'Health Status': health_status,
                        'EC2 Instances': ec2_list
                    })
        except:
            pass  # CLB가 없을 수 있음
        
        return pd.DataFrame(elb_details)
        
    except Exception as e:
        st.error(f"ELB 상세 정보 조회 오류: {e}")
        return pd.DataFrame()

# ElastiCache 클러스터 조회
def get_elasticache_clusters(session):
    try:
        elasticache = session.client('elasticache')
        response = elasticache.describe_cache_clusters()
        clusters = []
        for cluster in response['CacheClusters']:
            clusters.append({
                'Cluster ID': cluster['CacheClusterId'],
                'Engine': cluster['Engine'],
                'Node Type': cluster['CacheNodeType'],
                'Status': cluster['CacheClusterStatus'],
                'AZ': cluster.get('PreferredAvailabilityZone', 'N/A')
            })
        return pd.DataFrame(clusters)
    except Exception as e:
        st.error(f"ElastiCache 조회 오류: {e}")
        return pd.DataFrame()

# EFS 파일시스템 조회
def get_efs_filesystems(session):
    try:
        efs = session.client('efs')
        response = efs.describe_file_systems()
        filesystems = []
        for fs in response['FileSystems']:
            filesystems.append({
                'File System ID': fs['FileSystemId'],
                'Name': fs.get('Name', 'N/A'),
                'Creation Token': fs['CreationToken'],
                'Life Cycle State': fs['LifeCycleState'],
                'Performance Mode': fs['PerformanceMode'],
                'Throughput Mode': fs['ThroughputMode'],
                'Size (Bytes)': fs['SizeInBytes']['Value'],
                'Creation Time': fs['CreationTime'].strftime('%Y-%m-%d')
            })
        return pd.DataFrame(filesystems)
    except Exception as e:
        st.error(f"EFS 조회 오류: {e}")
        return pd.DataFrame()

# CloudFront 배포 조회
def get_cloudfront_distributions(session):
    try:
        cloudfront = session.client('cloudfront')
        response = cloudfront.list_distributions()
        distributions = []
        if 'DistributionList' in response and 'Items' in response['DistributionList']:
            for dist in response['DistributionList']['Items']:
                distributions.append({
                    'Distribution ID': dist['Id'],
                    'Domain': dist['DomainName'],
                    'Status': dist['Status'],
                    'Price Class': dist['PriceClass']
                })
        return pd.DataFrame(distributions)
    except Exception as e:
        st.error(f"CloudFront 조회 오류: {e}")
        return pd.DataFrame()

# AWS WAF Web ACLs 조회
def get_waf_webacls(session):
    try:
        wafv2 = session.client('wafv2')
        response = wafv2.list_web_acls(Scope='REGIONAL')
        webacls = []
        
        for webacl in response['WebACLs']:
            # 각 Web ACL의 상세 정보 조회
            detail_response = wafv2.get_web_acl(
                Name=webacl['Name'],
                Scope='REGIONAL',
                Id=webacl['Id']
            )
            
            # 연결된 리소스 조회
            resources_response = wafv2.list_resources_for_web_acl(
                WebACLArn=webacl['ARN']
            )
            
            # 규칙 이름 목록 생성
            rule_names = [rule['Name'] for rule in detail_response['WebACL']['Rules']]
            rules_str = ', '.join(rule_names) if rule_names else 'N/A'
            
            # 리소스 이름 목록 생성 (ARN에서 리소스 이름 추출)
            resource_names = []
            for arn in resources_response['ResourceArns']:
                # ARN에서 리소스 이름 추출
                resource_name = arn.split('/')[-1] if '/' in arn else arn.split(':')[-1]
                resource_names.append(resource_name)
            resources_str = ', '.join(resource_names) if resource_names else 'N/A'
            
            webacls.append({
                'WebACLs 명': webacl['Name'],
                'Rules': rules_str,
                'Associated AWS resources': resources_str
            })
        
        return pd.DataFrame(webacls)
    except Exception as e:
        st.error(f"AWS WAF 조회 오류: {e}")
        return pd.DataFrame()



# ACM 인증서 조회
def get_acm_certificates(session):
    try:
        from datetime import datetime
        acm = session.client('acm')
        response = acm.list_certificates()
        certificates = []
        for cert in response['CertificateSummaryList']:
            # 각 인증서의 상세 정보 조회
            detail_response = acm.describe_certificate(CertificateArn=cert['CertificateArn'])
            cert_detail = detail_response['Certificate']
            
            # 추가 도메인 이름 처리
            additional_names = cert_detail.get('SubjectAlternativeNames', [])
            if cert_detail['DomainName'] in additional_names:
                additional_names.remove(cert_detail['DomainName'])
            additional_names_str = ', '.join(additional_names) if additional_names else 'N/A'
            
            certificates.append({
                '도메인이름': cert_detail['DomainName'],
                '유형': cert_detail.get('Type', 'N/A'),
                '상태': cert_detail['Status'],
                '사용중': 'Yes' if cert_detail.get('InUseBy') else 'No',
                '갱신자격': cert_detail.get('RenewalEligibility', 'N/A'),
                '키알고리즘': cert_detail.get('KeyAlgorithm', 'N/A'),
                '추가도메인이름': additional_names_str,
                '만료기간': cert_detail.get('NotAfter', 'N/A').strftime('%Y-%m-%d') if cert_detail.get('NotAfter') else 'N/A'
            })
        return pd.DataFrame(certificates)
    except Exception as e:
        st.error(f"ACM 조회 오류: {e}")
        return pd.DataFrame()

# EC2 Reserved Instance 조회
def get_ec2_reserved_instances(session):
    try:
        from datetime import datetime, timedelta
        ec2 = session.client('ec2')
        response = ec2.describe_reserved_instances()
        reserved_instances = []
        for ri in response['ReservedInstances']:
            # 만료일시 계산 (End 필드가 없으면 Start + Duration으로 계산)
            if 'End' in ri:
                expiry_date = ri['End'].strftime('%Y-%m-%d')
            else:
                start_date = ri['Start']
                duration_seconds = ri['Duration']
                end_date = start_date + timedelta(seconds=duration_seconds)
                expiry_date = end_date.strftime('%Y-%m-%d')
            
            reserved_instances.append({
                'Reserved Instance ID': ri['ReservedInstancesId'],
                'Instance Type': ri['InstanceType'],
                'Instance Count': ri['InstanceCount'],
                'State': ri['State'],
                'Start': ri['Start'].strftime('%Y-%m-%d'),
                'Duration': f"{ri['Duration'] // (365*24*3600)} years",
                'Offering Class': ri.get('OfferingClass', 'N/A'),
                'Offering Type': ri.get('OfferingType', 'N/A'),
                '만료일시': expiry_date
            })
        return pd.DataFrame(reserved_instances)
    except Exception as e:
        st.error(f"EC2 RI 조회 오류: {e}")
        return pd.DataFrame()

# RDS Reserved Instance 조회
def get_rds_reserved_instances(session):
    try:
        from datetime import datetime, timedelta
        rds = session.client('rds')
        response = rds.describe_reserved_db_instances()
        reserved_instances = []
        for ri in response['ReservedDBInstances']:
            # 만료일시 계산
            start_date = ri['StartTime']
            duration_seconds = ri['Duration']
            end_date = start_date + timedelta(seconds=duration_seconds)
            expiry_date = end_date.strftime('%Y-%m-%d')
            
            reserved_instances.append({
                'Reserved DB Instance ID': ri['ReservedDBInstanceId'],
                'DB Instance Class': ri['DBInstanceClass'],
                'Engine': ri['ProductDescription'],
                'Multi-AZ': ri['MultiAZ'],
                'Instance Count': ri['DBInstanceCount'],
                'State': ri['State'],
                'Start Time': ri['StartTime'].strftime('%Y-%m-%d'),
                'Duration': f"{ri['Duration'] // (365*24*3600)} years",
                'Offering Type': ri.get('OfferingType', 'N/A'),
                '만료일시': expiry_date
            })
        return pd.DataFrame(reserved_instances)
    except Exception as e:
        st.error(f"RDS RI 조회 오류: {e}")
        return pd.DataFrame()

# VPC 조회
def get_vpcs(session):
    try:
        ec2 = session.client('ec2')
        response = ec2.describe_vpcs()
        vpcs = []
        for vpc in response['Vpcs']:
            name = next((tag['Value'] for tag in vpc.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            vpcs.append({
                'VPC ID': vpc['VpcId'],
                'Name': name,
                'CIDR Block': vpc['CidrBlock'],
                'State': vpc['State'],
                'Default': vpc['IsDefault']
            })
        return pd.DataFrame(vpcs)
    except Exception as e:
        st.error(f"VPC 조회 오류: {e}")
        return pd.DataFrame()

# Subnet 조회
def get_subnets(session):
    try:
        ec2 = session.client('ec2')
        response = ec2.describe_subnets()
        subnets = []
        for subnet in response['Subnets']:
            name = next((tag['Value'] for tag in subnet.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            subnets.append({
                'Subnet ID': subnet['SubnetId'],
                'Name': name,
                'VPC ID': subnet['VpcId'],
                'CIDR Block': subnet['CidrBlock'],
                'Availability Zone': subnet['AvailabilityZone'],
                'Available IPs': subnet['AvailableIpAddressCount'],
                'State': subnet['State']
            })
        return pd.DataFrame(subnets)
    except Exception as e:
        st.error(f"Subnet 조회 오류: {e}")
        return pd.DataFrame()

# Internet Gateway 조회
def get_internet_gateways(session):
    try:
        ec2 = session.client('ec2')
        response = ec2.describe_internet_gateways()
        igws = []
        for igw in response['InternetGateways']:
            name = next((tag['Value'] for tag in igw.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            attachments = ', '.join([att['VpcId'] for att in igw.get('Attachments', [])])
            igws.append({
                'IGW ID': igw['InternetGatewayId'],
                'Name': name,
                'State': igw['Attachments'][0]['State'] if igw.get('Attachments') else 'detached',
                'Attached VPCs': attachments or 'None'
            })
        return pd.DataFrame(igws)
    except Exception as e:
        st.error(f"Internet Gateway 조회 오류: {e}")
        return pd.DataFrame()

# NAT Gateway 조회
def get_nat_gateways(session):
    try:
        ec2 = session.client('ec2')
        response = ec2.describe_nat_gateways()
        nat_gws = []
        for nat in response['NatGateways']:
            name = next((tag['Value'] for tag in nat.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            nat_gws.append({
                'NAT Gateway ID': nat['NatGatewayId'],
                'Name': name,
                'VPC ID': nat['VpcId'],
                'Subnet ID': nat['SubnetId'],
                'State': nat['State'],
                'Type': nat.get('ConnectivityType', 'public')
            })
        return pd.DataFrame(nat_gws)
    except Exception as e:
        st.error(f"NAT Gateway 조회 오류: {e}")
        return pd.DataFrame()

# VPN Gateway 조회
def get_vpn_gateways(session):
    try:
        ec2 = session.client('ec2')
        response = ec2.describe_vpn_gateways()
        vpn_gws = []
        for vpn in response['VpnGateways']:
            name = next((tag['Value'] for tag in vpn.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            attachments = ', '.join([att['VpcId'] for att in vpn.get('VpcAttachments', [])])
            vpn_gws.append({
                'VPN Gateway ID': vpn['VpnGatewayId'],
                'Name': name,
                'Type': vpn['Type'],
                'State': vpn['State'],
                'Attached VPCs': attachments or 'None'
            })
        return pd.DataFrame(vpn_gws)
    except Exception as e:
        st.error(f"VPN Gateway 조회 오류: {e}")
        return pd.DataFrame()

# Transit Gateway 조회
def get_transit_gateways(session):
    try:
        ec2 = session.client('ec2')
        response = ec2.describe_transit_gateways()
        tgws = []
        for tgw in response['TransitGateways']:
            name = next((tag['Value'] for tag in tgw.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            tgws.append({
                'Transit Gateway ID': tgw['TransitGatewayId'],
                'Name': name,
                'State': tgw['State'],
                'Owner ID': tgw['OwnerId'],
                'Default Route Table': tgw.get('Options', {}).get('DefaultRouteTableAssociation', 'N/A')
            })
        return pd.DataFrame(tgws)
    except Exception as e:
        st.error(f"Transit Gateway 조회 오류: {e}")
        return pd.DataFrame()

# VPC Peering Connection 조회
def get_vpc_peering_connections(session):
    try:
        ec2 = session.client('ec2')
        response = ec2.describe_vpc_peering_connections()
        peerings = []
        for peer in response['VpcPeeringConnections']:
            name = next((tag['Value'] for tag in peer.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            peerings.append({
                'Peering Connection ID': peer['VpcPeeringConnectionId'],
                'Name': name,
                'Requester VPC': peer['RequesterVpcInfo']['VpcId'],
                'Accepter VPC': peer['AccepterVpcInfo']['VpcId'],
                'Status': peer['Status']['Code'],
                'Requester Region': peer['RequesterVpcInfo'].get('Region', 'N/A'),
                'Accepter Region': peer['AccepterVpcInfo'].get('Region', 'N/A')
            })
        return pd.DataFrame(peerings)
    except Exception as e:
        st.error(f"VPC Peering 조회 오류: {e}")
        return pd.DataFrame()

# AWS 리소스 전체 조회
def get_aws_resources(project_name):
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
    
    resources = {
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

# Q Developer CLI 호출 함수
def call_q_developer_cli(project_info):
    try:
        # Q Developer 서버에 HTTP POST 요청
        response = requests.post(
            "http://3.39.13.99:8005/chat",
            json={
                "access_key": project_info['access_key'],
                "secret_key": project_info['secret_key'],
                "region": project_info['region'],
                "account_id": project_info['account_id'],
                "prompt": "VPC, Subnet, Internet Gateway, NAT Gateway, VPN Gateway, Transit Gateway, VPC Peering, EC2, RDS, S3, ELB, ElastiCache, CloudFront, EFS, AWS WAF, ACM 등 모든 AWS 네트워크 및 서비스를 조회해서 구성도를 drawio(XML)형식으로 받아와줘"
            },
            timeout=1800
        )
        
        if response.status_code == 200:
            result = response.text
            # XML 코드만 추출
            xml_match = re.search(r'<mxfile[^>]*>.*?</mxfile>', result, re.DOTALL)
            if xml_match:
                return xml_match.group(0)
            else:
                # 다른 XML 패턴 시도
                xml_match = re.search(r'<\?xml.*?</.*?>', result, re.DOTALL)
                if xml_match:
                    return xml_match.group(0)
                else:
                    st.error("XML 코드를 찾을 수 없습니다.")
                    return None
        else:
            st.error(f"Q Developer 서버 오류: {response.status_code}")
            return None
            
    except Exception as e:
        st.error(f"Q Developer CLI 호출 오류: {e}")
        return None

# 기본 3-tier 구조 샘플 XML
def get_default_3tier_xml():
    return """
<mxfile host="embed.diagrams.net" modified="2024-01-01T00:00:00.000Z" agent="5.0" version="22.1.16" etag="sample" type="embed">
  <diagram name="3-Tier Architecture" id="sample-diagram">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        
        <!-- Presentation Tier -->
        <mxCell id="2" value="Presentation Tier" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=16;fontStyle=1" vertex="1" parent="1">
          <mxGeometry x="50" y="50" width="200" height="80" as="geometry" />
        </mxCell>
        
        <!-- Web Server -->
        <mxCell id="3" value="Web Server\n(Apache/Nginx)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6" vertex="1" parent="1">
          <mxGeometry x="300" y="50" width="120" height="80" as="geometry" />
        </mxCell>
        
        <!-- Application Tier -->
        <mxCell id="4" value="Application Tier" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=16;fontStyle=1" vertex="1" parent="1">
          <mxGeometry x="50" y="200" width="200" height="80" as="geometry" />
        </mxCell>
        
        <!-- App Server -->
        <mxCell id="5" value="Application Server\n(Tomcat/Node.js)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00" vertex="1" parent="1">
          <mxGeometry x="300" y="200" width="120" height="80" as="geometry" />
        </mxCell>
        
        <!-- Data Tier -->
        <mxCell id="6" value="Data Tier" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=16;fontStyle=1" vertex="1" parent="1">
          <mxGeometry x="50" y="350" width="200" height="80" as="geometry" />
        </mxCell>
        
        <!-- Database -->
        <mxCell id="7" value="Database\n(MySQL/PostgreSQL)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffcccc;strokeColor=#cc0000" vertex="1" parent="1">
          <mxGeometry x="300" y="350" width="120" height="80" as="geometry" />
        </mxCell>
        
        <!-- Connections -->
        <mxCell id="8" value="" style="endArrow=classic;html=1;rounded=0;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0" edge="1" parent="1" source="2" target="3">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="390" y="240" as="sourcePoint" />
            <mxPoint x="440" y="190" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        
        <mxCell id="9" value="" style="endArrow=classic;html=1;rounded=0;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0" edge="1" parent="1" source="3" target="5">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="390" y="240" as="sourcePoint" />
            <mxPoint x="440" y="190" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        
        <mxCell id="10" value="" style="endArrow=classic;html=1;rounded=0;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0" edge="1" parent="1" source="4" target="5">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="390" y="240" as="sourcePoint" />
            <mxPoint x="440" y="190" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        
        <mxCell id="11" value="" style="endArrow=classic;html=1;rounded=0;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0" edge="1" parent="1" source="5" target="7">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="390" y="240" as="sourcePoint" />
            <mxPoint x="440" y="190" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        
        <mxCell id="12" value="" style="endArrow=classic;html=1;rounded=0;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0" edge="1" parent="1" source="6" target="7">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="390" y="240" as="sourcePoint" />
            <mxPoint x="440" y="190" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
    """

# Draw.io XML을 iframe에 로드하는 함수
def load_drawio_with_xml(xml_content):
    
    if xml_content:
        # XML을 URL 인코딩
        encoded_xml = urllib.parse.quote(xml_content)
        
        # Draw.io iframe에 XML 데이터 로드
        iframe_html = f"""
        <iframe
        src="https://embed.diagrams.net/?embed=1&ui=atlas&proto=json&xml={encoded_xml}"
        width="100%"
        height="800"
        frameborder="0">
        </iframe>
        """
        return iframe_html
    else:
        # 기본 3-tier 구조 샘플 표시
        default_xml = get_default_3tier_xml()
        encoded_xml = urllib.parse.quote(default_xml)
        return f"""
<iframe frameborder="0" style="width:100%;height:863px;" src="https://viewer.diagrams.net/?tags=%7B%7D&lightbox=1&highlight=0000ff&edit=_blank&layers=1&nav=1&title=AWS_Architecture_250702.drawio#R%3Cmxfile%3E%3Cdiagram%20name%3D%22%ED%8E%98%EC%9D%B4%EC%A7%80-1%22%20id%3D%22QYOAMgD-o3gvjw3hr5vE%22%3E7VxZc9o6FP41foSx5f3RbGnvpB1u02l7%2B8IIUECNsRhZkNBffyUsgy2ZJQ1bW2cZrGNZOpa%2B7%2BgcLRh2e%2FZyR%2BF8%2BoGMUWwAc%2Fxi2B0DACuwAv4hJCspsU0%2Fk0woHkvZVvCAfyIpNKV0gccoLWVkhMQMz8vCEUkSNGIlGaSUPJezPZK4XOscTmSN5lbwMIIx0rJ9xWM2zaQB8LfydwhPpnnNlhdmd2YwzywLTqdwTJ4LIrtr2G1KCMuuZi9tFIvWy9sle6634%2B7wH4C%2FrV6%2BP0b9T2TV8DrO%2FFMD2FldSxgv5At86bdl%2FWyVv1SuO0UJ%2B%2BW6bEur6x3vAdK4%2B6pVmD4hNhLNYRp2iyxYjBPU3vSYEE4oHGOuTpvEhHJZQhL%2BbGvKZjFPWfzyeYoZepjDkSjzmcONyx5JwiRmLJCnZbWiVN7mc3E9e5kIfDbhc%2Bo0J5Qs5usq33PUVN4dLOcj8Tij5AnlKhnADvzQCj1REY5jRdUlogxz4EQxnohSGRGVQJmK0SMTJXL9cTK5X6c6til1rqpiDNMpGssX4YoyyBuNysbQe3A%2FHrhu6KWAaNnPd4jMEKMrnkXebVg58yRjc%2Fg%2BF9EvZdMC8n1XCqFk3GRT9hZZ%2FEKC6xVAywsu4AmNOUllklA2JROSwLi7lbZ4LybjTfNt89wT0S3rNvyBGFtJ9MAFI2W4HdnCOQuERnvbl6IYMrwsm5WqtpKP9gnmFW%2F6xQFuqVussOnbHghM4JrAB4HtlEtMyYKOkCxE6YCNVr%2FeJ76rkT%2F6%2BsAFLTh64uzaawDmQqu1nm6L%2F%2FHubWf%2FLs%2FaFpKmeFtNWCXzdaGlZ%2BMfVlUNqrBK5utCS88mUrnWZWGVzHd1jdWnrYqnLeVp%2FrfDnipWhf%2F2RPeWDBeX%2B1HEh6wqU%2Fe4%2FlHtUG7k7uEQxX2SYobXJnRIGCOzg1ZwxMkkbFiRaIdsOEzn2Ws94hehR7VRpyhDfGbSWzxZZdyHGTpfze7j7efGDEqeBrr5dCus59mMZ%2B6OFIj6lZBk8gMnR5AU0e4SZVy1spbPXBhTxUWhP8tIkoOjAjvXFL9cHis42gDkF4FWyQUNfSqCyOMjHqHmIkU0bZJkMKdohlOUDoTkrKMtUOACQh0vTliBl%2FBMePHNaq%2BuBsvtgcW1rg0WcMOeWd7A5%2FbMLBA2y74Z91ibwCz8OO5FnTOgR2bREmJOHxxjJl75uyDaWaJCzz%2Bm7oYek1ZEVJpPYjl%2BtxUVzYm1k9yqG6E4RJuiqsLKAtiKgZcoZkaWcLgu1MrcDPyzmCYMskJ6jGJUTKMxLiZjMnoqhnjCDBVuHwv0VzspNigbEsvUDclmJCpaEu98fkpwFG6iGjdXxE3DuTncAD0QfVgME8TOY96Ap1XXXwxjPOKyBv%2FX8VkZ7GqBrhrkagFuObjVAkc1aNQCxnLoqkW3agisxcnlUFqLZtWQV4uL9war55n8U%2BfMVCc1yxPHcJ7i4eYpikYLmnJ34JPg6JsnElNRHDdgg23mh7V5ygtWbdUmIle84B7oed3gdPOMwAkCy1Fd82NNh%2Ftq02ErpsOuMB1%2BhemwvLOZDt1V6VO8hAzVRK6J%2FGYim2bkRBVE7no9r%2Befjsi6c3NRItvOsUT2z0Zk3XfcErnTqtlcs7lm8y42WyU2u3Z4bTZ7YL%2BLrU8d1FyuuVy72MBWuHwDLran70fZjsw1kWsi14PyEUS%2BARfbcw652DWbazbXbK5ks7Jqe30X29Zd7I%2BIPRP6dJJJcifQbMEFloW5xnT1TTzPWSiT%2F8ni1onOSym1Kqb6iGLetpvlmiPRkDfkudeYQQBKGAJ22AzD0LGtwLbM0Mn9rAMLzFq5bnnh2jEVxDFIJ4hp5USUwlUhm7T0R6tvq6jar5aSnV9kCpx00TzfOHGTexl%2Bd5xZ3m0CTdXrIkhzrRppWst7RyLiZJ0A6jHqtD2qGG03DC%2Faob5Xs0q3f9J8m55re2YYKAWeeR9acBWOvbJLsjbYByy5TJzhd1%2FG4NSd%2FLbNmfryttYdlTHpuTf8V0SUdnMdoIptO1r41wEdHsftjpVf2d%2FHB27KbttGxdZsf7P1s3QUaiM9eacG9h9BqeBYSoW3RSl9ofl9jltg3kGGnuFK66DDhx93HdbZgXiFIEHb6fV62oyKzHxzx3d2nBXQJ5lykzCYyIY9I9eB65fJXrG1%2FqLndnLkF6DW%2FfaZC6L7Vo2wEyEMzucx10WoOIgJHA%2BGMIbJ6DXHON4ONatiXLko1PIjapVHxMwv%2FY%2F78Vaf5ryZ05w7ePqnnubk%2BqIBI4P153KenJO1DUvd93Z12uqnfD5Gn2s%2F5OSjRAIv4oIEZtM0bcv1g9DxbS8Ib2yUcK4ReWwnzErTZdvZszNOmB0MY%2FKz1QfDmHyEvZEwxsmxWQxjUiY8H72JfmH9z9XDJKPbNsKWEbjiIgiMMIjeN%2BYkZROKHv69rz2M38TDaIfArTi4%2Fad6GHScHm83nFebfEs5T%2BdVnKe7qJF39ajT6EZGyzdagdFtGZFttELJ5ShYX3hGy2l8gBTDzoHAtKZxTeM%2FksbqBp985etq3%2FmiB%2FR9Om7oY3AD4pqyvwllux1fHLf%2BWyiLRuCSI69z7ZHX06P5jLOHR9%2BawjWF%2F0IK2xdjME9uv6Y12xyx%2FbZbu%2Fs%2F%3C%2Fdiagram%3E%3C%2Fmxfile%3E">
</iframe>
        """

# 앱 시작 시 테이블 생성
create_projects_table()



# 대시보드 페이지
def dashboard_page():
    st.title("📊 대시보드")
    
    # 메트릭 카드
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("EC2 인스턴스", "12", "2")
    with col2:
        st.metric("RDS 인스턴스", "3", "0")
    with col3:
        st.metric("S3 버킷", "8", "1")
    with col4:
        st.metric("총 비용", "$1,234", "-$56")
    
    # 차트
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("빌링현황")
        
        # 샘플 데이터로 빌링현황 표시
        sample_billing_data = pd.DataFrame({
            'Project': ['Company A', 'Company B', 'Company C', 'Company D', 'Company E'],
            'Cost': [1250.75, 890.25, 2100.50, 650.00, 1450.30]
        })
        st.bar_chart(sample_billing_data.set_index('Project'))
    
    with col2:
        st.subheader("월별 비용 추이")
        cost_data = pd.DataFrame({
            'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
            'Cost': [1000, 1100, 1200, 1150, 1234]
        })
        st.line_chart(cost_data.set_index('Month'))

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
                    col3_1, col3_2, col3_3, col3_4, col3_5 = st.columns(5)
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
                        if st.button(f"✏️ 수정", key=f"edit_{project['id']}"):
                            st.session_state.show_edit_modal = True
                            st.session_state.edit_project_id = project['id']
                            st.rerun()
                    with col3_5:
                        if st.button(f"🗑️ 삭제", key=f"delete_{project['id']}"):
                            if delete_project_from_db(project['id']):
                                st.success("프로젝트가 삭제되었습니다.")
                                st.rerun()
                            else:
                                st.error("프로젝트 삭제에 실패했습니다.")

# 구성도 페이지
def diagram_page():
    st.title("🗺️ 구성도")
    
    # 프로젝트 선택
    project_names = get_project_names()
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
            with st.spinner(f"{selected_project} 프로젝트의 전체 AWS 리소스를 조회하고 있습니다..."):
                full_aws_data = get_full_aws_resources(selected_project)
            
            # 구성도그리기 페이지로 데이터 전달
            st.session_state.diagram_project = selected_project
            st.session_state.diagram_data = full_aws_data
            
            # Draw.io XML 구성도 생성
            with st.spinner("구성도를 생성하고 있습니다..."):
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
        st.warning("등록된 프로젝트가 없습니다. 프로젝트를 먼저 추가해주세요.")

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
    project_names = get_project_names()
    if project_names:
        # 프로젝트에서 인벤토리 버튼을 눌렀을 때 자동 선택
        default_index = 0
        if 'selected_project_for_inventory' in st.session_state and st.session_state.selected_project_for_inventory:
            if st.session_state.selected_project_for_inventory in project_names:
                default_index = project_names.index(st.session_state.selected_project_for_inventory) + 1
                # 사용 후 삭제하지 않고 유지
                # del st.session_state.selected_project_for_inventory
        
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
        st.warning("등록된 프로젝트가 없습니다. 프로젝트를 먼저 추가해주세요.")
        selected_project = None
    
    # AWS 리소스 데이터 가져오기
    aws_data = {}
    if selected_project and selected_project != "프로젝트 선택":
        with st.spinner(f"{selected_project} 프로젝트의 AWS 리소스를 조회하고 있습니다..."):
            aws_data = get_aws_resources(selected_project)
        
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
    
    # 데이터 표시
    if selected_project and selected_project != "프로젝트 선택":
        st.subheader(f"{selected_project} 프로젝트 리소스")
        
        # 만료 예정 항목 체크
        expiring_items = []
        
        for svc_name, df in aws_data.items():
            if not df.empty:
                st.subheader(f"{svc_name} ({len(df)}개)")
                if svc_name in ['ACM', 'EC2 RI', 'RDS RI'] and ('만료기간' in df.columns or '만료일시' in df.columns):
                    # 만료기간/만료일시 체크 및 색상 표시
                    def highlight_expiring_items(row):
                        try:
                            expiry_col = '만료기간' if '만료기간' in row.index else '만료일시'
                            if expiry_col in row.index and row[expiry_col] != 'N/A':
                                from datetime import datetime
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
        
        # 만료 예정 항목이 있으면 경고창 표시
        warning_key = f'expiry_warning_shown_{selected_project}'
        if expiring_items and warning_key not in st.session_state:
            expiring_types = list(set(expiring_items))
            expiry_text = ' 또는 '.join(expiring_types)
            
            @st.dialog("⚠️ 만료 알림")
            def show_expiry_warning():
                st.warning(f"**[만료알림]** {expiry_text}가 만료 예정이니, 확인 해주세요!!!")
                if st.button("확인 하겠습니다", type="primary", use_container_width=True):
                    st.session_state[warning_key] = True
                    st.rerun()
            
            show_expiry_warning()
    else:
        # 프로젝트 선택 안내
        st.info("프로젝트를 선택하여 AWS 리소스를 조회하세요.")
    
    # Excel 다운로드
    if selected_project and selected_project != "프로젝트 선택" and aws_data:
        # Excel 데이터 준비
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for svc_name, df in aws_data.items():
                if not df.empty:
                    df.to_excel(writer, sheet_name=svc_name, index=False)
        
        st.download_button(
            label="📥 Excel 다운로드",
            data=output.getvalue(),
            file_name=f"aws_inventory_{selected_project}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )



# AWS 리소스로 Draw.io XML 생성 (서브넷별 EC2 정확 배치)
def generate_aws_drawio_xml(project_name, aws_data):
    try:
        cell_id = 2
        cells = []
        
        # VPC 컴포넌트 (전체 틀)
        cells.append('<mxCell id="2" value="" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc;strokeColor=#248814;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#AAB7B8;dashed=0;" vertex="1" parent="1"><mxGeometry x="40" y="120" width="1200" height="800" as="geometry" /></mxCell>')
        cell_id += 1
        
        # VPC 라벨
        cells.append(f'<mxCell id="{cell_id}" value="VPC" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=14;fontStyle=1;fontColor=#248814;" vertex="1" parent="1"><mxGeometry x="50" y="130" width="100" height="30" as="geometry" /></mxCell>')
        cell_id += 1
        
        # Internet Gateway
        cells.append(f'<mxCell id="{cell_id}" value="Internet Gateway" style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.internet_gateway;" vertex="1" parent="1"><mxGeometry x="581" y="40" width="78" height="78" as="geometry" /></mxCell>')
        cell_id += 1
        
        # Subnet 및 EC2 정보 분석
        subnets_df = aws_data.get('Subnet', pd.DataFrame())
        ec2_df = aws_data.get('EC2', pd.DataFrame())
        
        # 서브넷별 리소스 개수 계산
        subnet_ec2_count = {}
        subnet_rds_count = {}
        subnet_info = {}
        
        if not subnets_df.empty:
            for _, subnet in subnets_df.iterrows():
                subnet_id = subnet.get('Subnet ID', '')
                subnet_name = subnet.get('Name', 'Subnet')
                az = subnet.get('Availability Zone', 'us-east-1a')
                
                # EC2 개수 계산
                ec2_count = 0
                if not ec2_df.empty:
                    ec2_count = len(ec2_df[ec2_df['Subnet ID'] == subnet_id])
                
                # RDS 개수 계산 (AZ 기준)
                rds_count = 0
                rds_df = aws_data.get('RDS', pd.DataFrame())
                if not rds_df.empty:
                    rds_count = len(rds_df[rds_df['AZ'] == az])
                
                subnet_ec2_count[subnet_id] = ec2_count
                subnet_rds_count[subnet_id] = rds_count
                subnet_info[subnet_id] = {
                    'name': subnet_name,
                    'az': az,
                    'is_public': 'public' in subnet_name.lower() or 'pub' in subnet_name.lower(),
                    'resource_count': ec2_count + rds_count
                }
        
        # 서브넷을 타입별, 리소스 유무별로 분류
        public_subnets_with_resources = {k: v for k, v in subnet_info.items() if v['is_public'] and v['resource_count'] > 0}
        public_subnets_empty = {k: v for k, v in subnet_info.items() if v['is_public'] and v['resource_count'] == 0}
        private_subnets_with_resources = {k: v for k, v in subnet_info.items() if not v['is_public'] and v['resource_count'] > 0}
        private_subnets_empty = {k: v for k, v in subnet_info.items() if not v['is_public'] and v['resource_count'] == 0}
        
        # AZ별로 분류
        def split_by_az(subnets_dict):
            az_a = {k: v for k, v in subnets_dict.items() if 'a' in v['az'].lower()}
            az_c = {k: v for k, v in subnets_dict.items() if 'c' in v['az'].lower()}
            return az_a, az_c
        
        pub_a_res, pub_c_res = split_by_az(public_subnets_with_resources)
        pub_a_empty, pub_c_empty = split_by_az(public_subnets_empty)
        priv_a_res, priv_c_res = split_by_az(private_subnets_with_resources)
        priv_a_empty, priv_c_empty = split_by_az(private_subnets_empty)
        
        # AZ 구역 크기 계산
        az_height = 700
        
        # AZ-A 구역
        cells.append(f'<mxCell id="{cell_id}" value="Availability Zone A" style="fillColor=none;strokeColor=#147EBA;dashed=1;verticalAlign=top;fontStyle=0;fontColor=#147EBA;whiteSpace=wrap;html=1;" vertex="1" parent="1"><mxGeometry x="80" y="180" width="500" height="{az_height}" as="geometry" /></mxCell>')
        cell_id += 1
        
        # AZ-C 구역
        cells.append(f'<mxCell id="{cell_id}" value="Availability Zone C" style="fillColor=none;strokeColor=#147EBA;dashed=1;verticalAlign=top;fontStyle=0;fontColor=#147EBA;whiteSpace=wrap;html=1;" vertex="1" parent="1"><mxGeometry x="660" y="180" width="500" height="{az_height}" as="geometry" /></mxCell>')
        cell_id += 1
        
        # 서브넷 배치 함수
        def create_subnet(subnet_id, info, x, y):
            nonlocal cell_id
            ec2_count = subnet_ec2_count.get(subnet_id, 0)
            rds_count = subnet_rds_count.get(subnet_id, 0)
            total_resources = ec2_count + rds_count
            subnet_height = max(120, 80 + (total_resources // 4 + 1) * 90)
            
            color = '#248814' if info['is_public'] else '#147EBA'
            
            cells.append(f'<mxCell id="{cell_id}" value="{info["name"]}" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_subnet;strokeColor={color};fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor={color};dashed=0;" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="460" height="{subnet_height}" as="geometry" /></mxCell>')
            
            subnet_positions[subnet_id] = {
                'x': x,
                'y': y,
                'width': 460,
                'height': subnet_height
            }
            
            cell_id += 1
            return y + subnet_height + 20
        
        # 서브넷 배치 (우선순위: Public 리소스 있음 -> Private 리소스 있음 -> Public 빈 것 -> Private 빈 것)
        subnet_positions = {}
        current_y_a = 220
        current_y_c = 220
        
        # 1. Public Subnets with resources (상단)
        for subnet_id, info in pub_a_res.items():
            current_y_a = create_subnet(subnet_id, info, 100, current_y_a)
        for subnet_id, info in pub_c_res.items():
            current_y_c = create_subnet(subnet_id, info, 680, current_y_c)
        
        # 2. Private Subnets with resources
        for subnet_id, info in priv_a_res.items():
            current_y_a = create_subnet(subnet_id, info, 100, current_y_a)
        for subnet_id, info in priv_c_res.items():
            current_y_c = create_subnet(subnet_id, info, 680, current_y_c)
        
        # 3. Empty Public Subnets
        for subnet_id, info in pub_a_empty.items():
            current_y_a = create_subnet(subnet_id, info, 100, current_y_a)
        for subnet_id, info in pub_c_empty.items():
            current_y_c = create_subnet(subnet_id, info, 680, current_y_c)
        
        # 4. Empty Private Subnets (하단)
        for subnet_id, info in priv_a_empty.items():
            current_y_a = create_subnet(subnet_id, info, 100, current_y_a)
        for subnet_id, info in priv_c_empty.items():
            current_y_c = create_subnet(subnet_id, info, 680, current_y_c)
        
        # NAT Gateway (첫 번째 Public Subnet 내부)
        if not aws_data.get('NAT Gateway', pd.DataFrame()).empty:
            first_public_subnet = next((sid for sid, info in subnet_info.items() if info['is_public']), None)
            if first_public_subnet and first_public_subnet in subnet_positions:
                pos = subnet_positions[first_public_subnet]
                cells.append(f'<mxCell id="{cell_id}" value="NAT Gateway" style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.nat_gateway;" vertex="1" parent="1"><mxGeometry x="{pos["x"] + 350}" y="{pos["y"] + 50}" width="78" height="78" as="geometry" /></mxCell>')
                cell_id += 1
        
        # Load Balancer (Public Subnet 사이)
        elb_id = None
        if not aws_data.get('ELB', pd.DataFrame()).empty:
            elb_id = cell_id
            cells.append(f'<mxCell id="{cell_id}" value="Load Balancer" style="sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.elastic_load_balancing;" vertex="1" parent="1"><mxGeometry x="581" y="270" width="78" height="78" as="geometry" /></mxCell>')
            cell_id += 1
        
        # EC2 인스턴스들 (서브넷별 정확 배치)
        ec2_ids = []
        if not ec2_df.empty:
            for _, ec2 in ec2_df.iterrows():
                instance_name = ec2.get('Name', 'EC2')
                if instance_name == 'N/A':
                    instance_name = 'EC2'
                
                subnet_id = ec2.get('Subnet ID', 'N/A')
                
                if subnet_id in subnet_positions:
                    pos = subnet_positions[subnet_id]
                    # 서브넷 내에서 EC2들의 위치 계산
                    subnet_ec2s = ec2_df[ec2_df['Subnet ID'] == subnet_id]
                    ec2_index = list(subnet_ec2s.index).index(ec2.name)
                    
                    # 4개씩 한 줄에 배치
                    row = ec2_index // 4
                    col = ec2_index % 4
                    
                    x_pos = pos['x'] + 40 + (col * 100)
                    y_pos = pos['y'] + 50 + (row * 90)
                    
                    cells.append(f'<mxCell id="{cell_id}" value="{instance_name}" style="sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;" vertex="1" parent="1"><mxGeometry x="{x_pos}" y="{y_pos}" width="78" height="78" as="geometry" /></mxCell>')
                    ec2_ids.append(cell_id)
                    cell_id += 1
        
        # RDS (해당 AZ의 Private Subnet 내부)
        rds_id = None
        rds_df = aws_data.get('RDS', pd.DataFrame())
        if not rds_df.empty:
            for _, rds in rds_df.iterrows():
                rds_name = rds.get('DB Instance', 'RDS')
                rds_az = rds.get('AZ', 'us-east-1a')
                
                # RDS AZ에 맞는 Private Subnet 찾기
                target_subnet = None
                for sid, info in subnet_info.items():
                    if not info['is_public'] and rds_az in info['az']:
                        target_subnet = sid
                        break
                
                if target_subnet and target_subnet in subnet_positions:
                    pos = subnet_positions[target_subnet]
                    # 해당 서브넷의 EC2 개수 확인하여 위치 조정
                    subnet_ec2s = ec2_df[ec2_df['Subnet ID'] == target_subnet] if not ec2_df.empty else pd.DataFrame()
                    ec2_count = len(subnet_ec2s)
                    
                    # EC2 다음 위치에 RDS 배치
                    row = ec2_count // 4
                    col = ec2_count % 4
                    
                    x_pos = pos['x'] + 40 + (col * 100)
                    y_pos = pos['y'] + 50 + (row * 90)
                    
                    rds_id = cell_id
                    cells.append(f'<mxCell id="{cell_id}" value="{rds_name}" style="sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];outlineConnect=0;fontColor=#232F3E;gradientColor=#4D72F3;gradientDirection=north;fillColor=#3334B9;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.rds;" vertex="1" parent="1"><mxGeometry x="{x_pos}" y="{y_pos}" width="78" height="78" as="geometry" /></mxCell>')
                    cell_id += 1
        
        # S3 (외부)
        if not aws_data.get('S3', pd.DataFrame()).empty:
            cells.append(f'<mxCell id="{cell_id}" value="S3" style="sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];outlineConnect=0;fontColor=#232F3E;gradientColor=#60A337;gradientDirection=north;fillColor=#277116;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.s3;" vertex="1" parent="1"><mxGeometry x="150" y="40" width="78" height="78" as="geometry" /></mxCell>')
            cell_id += 1
        
        # 화살표 연결
        # IGW -> ELB
        if elb_id:
            cells.append(f'<mxCell id="{cell_id}" value="" style="endArrow=classic;html=1;rounded=0;exitX=0.5;exitY=1;exitDx=0;exitDy=0;exitPerimeter=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;entryPerimeter=0;" edge="1" parent="1" source="3" target="{elb_id}"><mxGeometry width="50" height="50" relative="1" as="geometry"><mxPoint x="600" y="200" as="sourcePoint" /><mxPoint x="650" y="150" as="targetPoint" /></mxGeometry></mxCell>')
            cell_id += 1
        
        # ELB -> EC2s
        if elb_id and ec2_ids:
            for ec2_id in ec2_ids:
                cells.append(f'<mxCell id="{cell_id}" value="" style="endArrow=classic;html=1;rounded=0;exitX=0.5;exitY=1;exitDx=0;exitDy=0;exitPerimeter=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;entryPerimeter=0;" edge="1" parent="1" source="{elb_id}" target="{ec2_id}"><mxGeometry width="50" height="50" relative="1" as="geometry"><mxPoint x="600" y="400" as="sourcePoint" /><mxPoint x="650" y="350" as="targetPoint" /></mxGeometry></mxCell>')
                cell_id += 1
        
        # EC2 -> RDS
        if ec2_ids and rds_id:
            cells.append(f'<mxCell id="{cell_id}" value="" style="endArrow=classic;html=1;rounded=0;exitX=0.5;exitY=1;exitDx=0;exitDy=0;exitPerimeter=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;entryPerimeter=0;" edge="1" parent="1" source="{ec2_ids[0]}" target="{rds_id}"><mxGeometry width="50" height="50" relative="1" as="geometry"><mxPoint x="500" y="600" as="sourcePoint" /><mxPoint x="550" y="550" as="targetPoint" /></mxGeometry></mxCell>')
            cell_id += 1
        
        # 리소스가 없을 경우
        if len(cells) <= 6:
            cells.append('<mxCell id="50" value="No AWS Resources Found" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=16" vertex="1" parent="1"><mxGeometry x="500" y="400" width="200" height="80" as="geometry" /></mxCell>')
        
        # XML 생성
        cells_xml = '\n        '.join(cells)
        
        xml_content = f"""<mxfile host="embed.diagrams.net" modified="{datetime.now().isoformat()}Z" agent="5.0" version="22.1.16" etag="aws-diagram" type="embed">
  <diagram name="{project_name} AWS Architecture" id="aws-diagram">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1400" pageHeight="1000" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        {cells_xml}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""
        
        return xml_content.strip()
        
    except Exception as e:
        st.error(f"Draw.io XML 생성 오류: {e}")
        return None



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