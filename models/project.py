import streamlit as st
from psycopg2 import Error
from config.database import get_db_connection

# 프로젝트 추가 (프로젝트 ID 반환)
def add_project_to_db(project_name, account_id, region, access_key, secret_key):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            # SERIAL 타입을 사용하여 자동 증가하는 ID 생성
            cursor.execute("""
                INSERT INTO project (project_name, account_id, region, access_key, secret_key)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            """, (project_name, account_id, region, access_key, secret_key))
            project_id = cursor.fetchone()[0]
            connection.commit()
            return project_id
        except Error as e:
            st.error(f"프로젝트 추가 오류: {e}")
            return None
        finally:
            connection.close()
    return None

# 프로젝트 목록 조회
def get_projects_from_db():
    connection = get_db_connection()
    projects = []
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM project ORDER BY created_at DESC")
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            projects = [dict(zip(columns, row)) for row in rows]
            # access_key 마스킹 처리
            for project in projects:
                project['access_key'] = project['access_key'][:8] + "..."
                project['secret_key'] = "***"
        except Error as e:
            st.error(f"프로젝트 조회 오류: {e}")
        finally:
            connection.close()
    return projects

# 프로젝트 수정
def update_project_in_db(project_id, project_name, account_id, region, access_key, secret_key):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE project 
                SET project_name = %s, account_id = %s, region = %s, access_key = %s, secret_key = %s
                WHERE id = %s
            """, (project_name, account_id, region, access_key, secret_key, project_id))
            connection.commit()
            return True
        except Error as e:
            st.error(f"프로젝트 수정 오류: {e}")
            return False
        finally:
            connection.close()
    return False

# 프로젝트 원본 정보 조회 (마스킹 없이)
def get_project_original_info(project_id):
    connection = get_db_connection()
    project_info = None
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM project WHERE id = %s", (project_id,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                project_info = dict(zip(columns, row))
        except Error as e:
            st.error(f"프로젝트 정보 조회 오류: {e}")
        finally:
            connection.close()
    return project_info

# 프로젝트 삭제
def delete_project_from_db(project_id):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM project WHERE id = %s", (project_id,))
            connection.commit()
            return True
        except Error as e:
            st.error(f"프로젝트 삭제 오류: {e}")
            return False
        finally:
            connection.close()
    return False

# 프로젝트명 목록 조회
def get_project_names():
    connection = get_db_connection()
    project_names = []
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT project_name FROM project ORDER BY project_name")
            results = cursor.fetchall()
            project_names = [row[0] for row in results]
        except Error as e:
            st.error(f"프로젝트명 조회 오류: {e}")
        finally:
            connection.close()
    return project_names

# 프로젝트 정보 조회
def get_project_info(project_name):
    connection = get_db_connection()
    project_info = None
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM project WHERE project_name = %s", (project_name,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                project_info = dict(zip(columns, row))
        except Error as e:
            st.error(f"프로젝트 정보 조회 오류: {e}")
        finally:
            connection.close()
    return project_info