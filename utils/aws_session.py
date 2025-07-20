import boto3
import streamlit as st

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