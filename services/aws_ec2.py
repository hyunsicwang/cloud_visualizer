import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# EC2 인스턴스 조회
def get_ec2_instances(session):
    try:
        ec2 = session.client('ec2')
        response = ec2.describe_instances()
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
                # Private IP 추출
                private_ip = instance.get('PrivateIpAddress', 'N/A')
                instances.append({
                    'Instance ID': instance['InstanceId'],
                    'Name': name,
                    'Type': instance['InstanceType'],
                    'Private IP': private_ip,  # Private IP 추가
                    'State': instance['State']['Name'],
                    'AZ': instance['Placement']['AvailabilityZone'],
                    'Subnet ID': instance.get('SubnetId', 'N/A')
                })
        return pd.DataFrame(instances)
    except Exception as e:
        st.error(f"EC2 조회 오류: {e}")
        return pd.DataFrame()

# EC2 Reserved Instance 조회
def get_ec2_reserved_instances(session):
    try:
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