import streamlit as st
import pandas as pd
from datetime import datetime

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