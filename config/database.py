import os
import psycopg2
from psycopg2 import Error
import streamlit as st
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 데이터베이스 연결 함수
def get_db_connection():
    try:
        connection = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
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
            # 프로젝트 테이블 생성
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
            
            # 보안점검 테이블 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS security (
                    id SERIAL PRIMARY KEY,
                    project_name VARCHAR(255) NOT NULL UNIQUE,
                    security_point DECIMAL(5,2) NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 시퀀스 재설정 시도
            try:
                cursor.execute("SELECT MAX(id) FROM project")
                max_id = cursor.fetchone()[0]
                if max_id is not None:
                    cursor.execute(f"ALTER SEQUENCE project_id_seq RESTART WITH {max_id + 1}")
            except:
                pass  # 시퀀스 재설정 실패는 무시
                
            connection.commit()
        except Error as e:
            st.error(f"테이블 생성 오류: {e}")
        finally:
            connection.close()

# 보안점수 저장/업데이트
def update_security_score(project_name, security_point):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            # UPSERT (INSERT ON CONFLICT UPDATE)
            cursor.execute("""
                INSERT INTO security (project_name, security_point, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (project_name)
                DO UPDATE SET 
                    security_point = EXCLUDED.security_point,
                    updated_at = CURRENT_TIMESTAMP
            """, (project_name, security_point))
            connection.commit()
            return True
        except Error as e:
            st.error(f"보안점수 저장 오류: {e}")
            return False
        finally:
            connection.close()
    return False

# 모든 프로젝트의 보안점수 조회
def get_all_security_scores():
    connection = get_db_connection()
    security_scores = []
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT project_name, security_point FROM security ORDER BY security_point DESC")
            rows = cursor.fetchall()
            security_scores = [{'project': row[0], 'score': float(row[1])} for row in rows]
        except Error as e:
            st.error(f"보안점수 조회 오류: {e}")
        finally:
            connection.close()
    return security_scores

# 멤버 테이블 생성
def create_member_table():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS member (
                    id VARCHAR(255) PRIMARY KEY,
                    pw VARCHAR(255) NOT NULL,
                    permission VARCHAR(50) DEFAULT 'user',
                    projects TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # admin 계정 생성 (이미 존재하면 무시)
            cursor.execute("""
                INSERT INTO member (id, pw, permission, projects)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, ('admin', 'Woongjin!2025', 'admin', 'all'))
            
            connection.commit()
        except Error as e:
            st.error(f"멤버 테이블 생성 오류: {e}")
        finally:
            connection.close()

# 사용자 인증
def authenticate_user(user_id, password):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT id, permission, projects FROM member WHERE id = %s AND pw = %s", (user_id, password))
            result = cursor.fetchone()
            if result:
                return {'id': result[0], 'permission': result[1], 'projects': result[2]}
        except Error as e:
            st.error(f"사용자 인증 오류: {e}")
        finally:
            connection.close()
    return None

# 사용자가 접근 가능한 프로젝트 ID 목록 조회
def get_user_project_ids(user_id):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT projects FROM member WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            if result and result[0]:
                projects = result[0]
                if projects == 'all':
                    return 'all'
                else:
                    return [int(pid) for pid in projects.split(',') if pid.strip()]
            return []
        except Error as e:
            st.error(f"사용자 프로젝트 조회 오류: {e}")
        finally:
            connection.close()
    return []

# 사용자 생성
def create_user(user_id, password):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO member (id, pw, permission, projects)
                VALUES (%s, %s, 'user', '')
            """, (user_id, password))
            connection.commit()
            return True
        except Error as e:
            if "duplicate key" in str(e).lower():
                st.error("이미 존재하는 아이디입니다.")
            else:
                st.error(f"사용자 생성 오류: {e}")
            return False
        finally:
            connection.close()
    return False

# 사용자 프로젝트 권한 업데이트
def update_user_projects(user_id, project_id):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            # 현재 프로젝트 목록 조회
            cursor.execute("SELECT projects FROM member WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            if result:
                current_projects = result[0]
                if current_projects and current_projects != 'all':
                    projects_list = current_projects.split(',')
                    if str(project_id) not in projects_list:
                        projects_list.append(str(project_id))
                        new_projects = ','.join(projects_list)
                    else:
                        new_projects = current_projects
                else:
                    new_projects = str(project_id)
                
                cursor.execute("UPDATE member SET projects = %s WHERE id = %s", (new_projects, user_id))
                connection.commit()
                return True
        except Error as e:
            st.error(f"프로젝트 권한 업데이트 오류: {e}")
        finally:
            connection.close()
    return False