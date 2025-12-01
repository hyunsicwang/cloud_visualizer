import streamlit as st
import pandas as pd

# S3 Public 여부 점검
def check_s3_public_access(session):
    try:
        s3 = session.client('s3')
        results = []
        
        # 모든 S3 버킷 조회
        buckets = s3.list_buckets()['Buckets']
        
        for bucket in buckets:
            bucket_name = bucket['Name']
            is_public = False
            
            try:
                # Public Access Block 설정 확인
                public_access_block = s3.get_public_access_block(Bucket=bucket_name)
                pab_config = public_access_block['PublicAccessBlockConfiguration']
                
                # 모든 Public Access Block이 True가 아니면 취약
                if not all([
                    pab_config.get('BlockPublicAcls', False),
                    pab_config.get('IgnorePublicAcls', False),
                    pab_config.get('BlockPublicPolicy', False),
                    pab_config.get('RestrictPublicBuckets', False)
                ]):
                    is_public = True
            except:
                # Public Access Block이 설정되지 않은 경우 취약
                is_public = True
            
            try:
                # Bucket ACL 확인
                acl = s3.get_bucket_acl(Bucket=bucket_name)
                for grant in acl['Grants']:
                    grantee = grant.get('Grantee', {})
                    if grantee.get('Type') == 'Group' and 'AllUsers' in grantee.get('URI', ''):
                        is_public = True
                        break
            except:
                pass
            
            results.append({
                'Bucket Name': bucket_name,
                '취약성여부': '취약함' if is_public else '양호함'
            })
        
        return pd.DataFrame(results)
    except Exception as e:
        st.error(f"S3 Public Access 점검 오류: {e}")
        return pd.DataFrame()

# Security Group Inbound 0.0.0.0/0 점검
def check_sg_open_to_world(session):
    try:
        ec2 = session.client('ec2')
        results = []
        
        # 모든 Security Group 조회
        sgs = ec2.describe_security_groups()['SecurityGroups']
        
        for sg in sgs:
            sg_id = sg['GroupId']
            sg_name = sg.get('GroupName', 'N/A')
            is_vulnerable = False
            
            # Inbound 규칙 확인
            for rule in sg.get('IpPermissions', []):
                for ip_range in rule.get('IpRanges', []):
                    if ip_range.get('CidrIp') == '0.0.0.0/0':
                        is_vulnerable = True
                        break
                if is_vulnerable:
                    break
            
            results.append({
                'Security Group ID': sg_id,
                'Security Group Name': sg_name,
                '취약성여부': '취약함' if is_vulnerable else '양호함'
            })
        
        return pd.DataFrame(results)
    except Exception as e:
        st.error(f"Security Group 점검 오류: {e}")
        return pd.DataFrame()

# IAM 사용자 MFA 점검
def check_iam_mfa(session):
    try:
        iam = session.client('iam')
        results = []
        
        # 모든 IAM 사용자 조회
        users = iam.list_users()['Users']
        
        for user in users:
            username = user['UserName']
            has_mfa = False
            
            try:
                # MFA 디바이스 확인
                mfa_devices = iam.list_mfa_devices(UserName=username)['MFADevices']
                has_mfa = len(mfa_devices) > 0
            except:
                pass
            
            results.append({
                'IAM User': username,
                '취약성여부': '양호함' if has_mfa else '취약함'
            })
        
        return pd.DataFrame(results)
    except Exception as e:
        st.error(f"IAM MFA 점검 오류: {e}")
        return pd.DataFrame()

# Root 계정 사용 및 액세스키 점검
def check_root_account(session):
    try:
        iam = session.client('iam')
        cloudtrail = session.client('cloudtrail')
        results = []
        
        # Root 계정 액세스키 확인
        try:
            account_summary = iam.get_account_summary()['SummaryMap']
            root_access_keys = account_summary.get('AccountAccessKeysPresent', 0)
            
            results.append({
                'Check Item': 'Root Account Access Keys',
                '취약성여부': '취약함' if root_access_keys > 0 else '양호함'
            })
        except:
            results.append({
                'Check Item': 'Root Account Access Keys',
                '취약성여부': '확인불가'
            })
        
        # Root 계정 사용 여부 (CloudTrail 로그 확인)
        try:
            # 최근 7일간 Root 사용 이벤트 확인
            import datetime
            end_time = datetime.datetime.now()
            start_time = end_time - datetime.timedelta(days=7)
            
            events = cloudtrail.lookup_events(
                LookupAttributes=[
                    {
                        'AttributeKey': 'Username',
                        'AttributeValue': 'root'
                    }
                ],
                StartTime=start_time,
                EndTime=end_time
            )
            
            root_usage = len(events['Events']) > 0
            
            results.append({
                'Check Item': 'Root Account Usage (Last 7 days)',
                '취약성여부': '취약함' if root_usage else '양호함'
            })
        except:
            results.append({
                'Check Item': 'Root Account Usage (Last 7 days)',
                '취약성여부': '확인불가'
            })
        
        return pd.DataFrame(results)
    except Exception as e:
        st.error(f"Root 계정 점검 오류: {e}")
        return pd.DataFrame()

# CloudTrail 로그 활성화 점검
def check_cloudtrail_logging(session):
    try:
        cloudtrail = session.client('cloudtrail')
        results = []
        
        # 모든 CloudTrail 조회
        try:
            trails = cloudtrail.describe_trails()['trailList']
            
            if not trails:
                results.append({
                    'Trail Name': 'No CloudTrail Found',
                    'Status': 'N/A',
                    '취약성여부': '취약함'
                })
            else:
                for trail in trails:
                    trail_name = trail['Name']
                    
                    # Trail 상태 확인
                    try:
                        status = cloudtrail.get_trail_status(Name=trail_name)
                        is_logging = status.get('IsLogging', False)
                        
                        results.append({
                            'Trail Name': trail_name,
                            'Status': 'Logging' if is_logging else 'Not Logging',
                            '취약성여부': '양호함' if is_logging else '취약함'
                        })
                    except Exception as status_error:
                        results.append({
                            'Trail Name': trail_name,
                            'Status': 'Error',
                            '취약성여부': '확인불가'
                        })
        except Exception as trail_error:
            results.append({
                'Trail Name': 'Error retrieving trails',
                'Status': 'Error',
                '취약성여부': '확인불가'
            })
        
        return pd.DataFrame(results)
    except Exception as e:
        st.error(f"CloudTrail 점검 오류: {e}")
        return pd.DataFrame()