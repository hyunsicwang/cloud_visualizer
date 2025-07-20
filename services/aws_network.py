import streamlit as st
import pandas as pd

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
        elb_details = []
        
        # ALB/NLB 조회
        try:
            response = elb.describe_load_balancers()
            for lb in response['LoadBalancers']:
                lb_arn = lb['LoadBalancerArn']
                lb_name = lb['LoadBalancerName']
                lb_type = lb['Type']
                lb_scheme = lb['Scheme']
                
                # 리스너 조회
                listeners_info = []
                target_groups_info = []
                all_ec2_instances = set()
                
                try:
                    listeners = elb.describe_listeners(LoadBalancerArn=lb_arn)['Listeners']
                    for listener in listeners:
                        listener_port = listener['Port']
                        listener_protocol = listener['Protocol']
                        listeners_info.append(f"{listener_protocol}:{listener_port}")
                        
                        # 대상 그룹 조회
                        for action in listener.get('DefaultActions', []):
                            if action['Type'] == 'forward':
                                tg_arn = None
                                if 'TargetGroupArn' in action:
                                    tg_arn = action['TargetGroupArn']
                                elif 'ForwardConfig' in action and action['ForwardConfig'].get('TargetGroups'):
                                    tg_arn = action['ForwardConfig']['TargetGroups'][0]['TargetGroupArn']
                                
                                if tg_arn:
                                    try:
                                        # 대상 그룹 상세 정보
                                        tg_info = elb.describe_target_groups(TargetGroupArns=[tg_arn])['TargetGroups'][0]
                                        tg_name = tg_info['TargetGroupName']
                                        target_groups_info.append(tg_name)
                                        
                                        # 대상 상태 확인 및 EC2 인스턴스 정보 수집
                                        target_health = elb.describe_target_health(TargetGroupArn=tg_arn)
                                        ec2_client = session.client('ec2')
                                        
                                        for target in target_health['TargetHealthDescriptions']:
                                            if target['Target']['Id'].startswith('i-'):
                                                instance_id = target['Target']['Id']
                                                try:
                                                    ec2_response = ec2_client.describe_instances(InstanceIds=[instance_id])
                                                    for reservation in ec2_response['Reservations']:
                                                        for instance in reservation['Instances']:
                                                            instance_name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
                                                            private_ip = instance.get('PrivateIpAddress', 'N/A')
                                                            all_ec2_instances.add(f"{instance_name} ({instance_id}, {private_ip})")
                                                except:
                                                    all_ec2_instances.add(f"Unknown ({instance_id})")
                                    except Exception as tg_error:
                                        continue
                except Exception as listener_error:
                    listeners_info = ['N/A']
                
                # ELB별로 하나의 행만 생성
                elb_details.append({
                    'ELB Name': lb_name,
                    'Type': lb_type,
                    'Scheme': lb_scheme,
                    'Listeners': ', '.join(listeners_info) if listeners_info else 'N/A',
                    'Target Groups': ', '.join(list(set(target_groups_info))) if target_groups_info else 'N/A',
                    'EC2 Instances': ', '.join(sorted(all_ec2_instances)) if all_ec2_instances else 'No EC2 Instances'
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
                listeners_info = []
                for listener in clb['ListenerDescriptions']:
                    listener_info = listener['Listener']
                    protocol = listener_info['Protocol']
                    port = listener_info['LoadBalancerPort']
                    listeners_info.append(f"{protocol}:{port}")
                
                # CLB에 연결된 EC2 인스턴스 정보
                ec2_instances = set()
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
                                    ec2_instances.add(f"{instance_name} ({instance_id}, {private_ip})")
                        except:
                            ec2_instances.add(f"Unknown ({instance_id})")
                except:
                    pass
                
                elb_details.append({
                    'ELB Name': clb_name,
                    'Type': 'classic',
                    'Scheme': clb_scheme,
                    'Listeners': ', '.join(listeners_info) if listeners_info else 'N/A',
                    'Target Groups': 'Direct Instance',
                    'EC2 Instances': ', '.join(sorted(ec2_instances)) if ec2_instances else 'No EC2 Instances'
                })
        except Exception as clb_error:
            pass
        
        return pd.DataFrame(elb_details)
        
    except Exception as e:
        st.error(f"ELB 상세 정보 조회 오류: {e}")
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