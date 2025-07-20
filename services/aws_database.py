import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

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

# RDS Reserved Instance 조회
def get_rds_reserved_instances(session):
    try:
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