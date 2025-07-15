# Cloud Visualizer

AWS 인프라 리소스를 시각화하여 관리할 수 있는 웹 포탈

## 기능

- **대시보드**: 인프라 현황 및 메트릭 시각화
- **프로젝트**: 프로젝트별 리소스 관리
- **구성도**: diagrams.net 기반 인프라 구성도 생성/편집
- **인벤토리**: AWS 서비스별 리소스 목록 및 Excel 다운로드

## 실행 방법

### 1. Python 가상환경 생성 (권장)
```bash
python -m venv venv
venv\Scripts\activate
```

### 2. 의존성 설치
```bash
# Streamlit 및 MySQL 관련 패키지 설치
pip install streamlit mysql-connector-python sqlalchemy

# 기타 의존성 설치 (requirements.txt가 있는 경우)
pip install -r requirements.txt
```

### 3. 애플리케이션 실행
```bash
streamlit run app.py
```

## 데이터베이스 설정 (XAMPP + MySQL)

### 1. XAMPP 설치
1. [XAMPP 다운로드](https://www.apachefriends.org/download.html)
2. Windows용 XAMPP 다운로드 (약 150MB)
3. 관리자 권한으로 설치 실행
4. 설치 경로: `C:\xampp` (기본값 권장)

### 2. XAMPP 실행 및 MySQL 시작
1. XAMPP Control Panel 실행
2. MySQL 옆의 **Start** 버튼 클릭
3. 상태가 초록색으로 변경되면 MySQL 서버 실행 완료

### 3. 데이터베이스 생성
**방법 1: phpMyAdmin 사용 (권장)**
1. 브라우저에서 `http://localhost/phpmyadmin` 접속
2. 좌측 메뉴에서 **새로 만들기** 클릭
3. 데이터베이스 이름: `cloud_visualizer` 입력 후 **만들기**

**방법 2: SQL 명령어 사용**
```sql
CREATE DATABASE cloud_visualizer;
CREATE USER 'cloud_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON cloud_visualizer.* TO 'cloud_user'@'localhost';
FLUSH PRIVILEGES;
```

### 4. 환경 변수 설정
`.env` 파일 생성:
```
DB_HOST=localhost
DB_PORT=3306
DB_NAME=cloud_visualizer
DB_USER=root
DB_PASSWORD=
```
**참고**: XAMPP 기본 설정에서는 root 계정에 비밀번호가 없습니다.

### 트러블슈팅
- `streamlit` 명령어를 찾을 수 없는 경우: `pip install streamlit` 실행
- Python 모듈로 실행: `python -m streamlit run app.py`
- MySQL 연결 오류: 서버 실행 상태 및 계정 정보 확인

## 지원 서비스

- EC2
- RDS
- S3
- ELB (ALB/NLB)
- ElastiCache
- CloudFront
- EFS
- AWS WAF