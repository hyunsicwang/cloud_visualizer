import streamlit as st
import pandas as pd

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