import streamlit as st
import pandas as pd

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