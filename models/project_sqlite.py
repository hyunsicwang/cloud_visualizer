import streamlit as st
from config.database_sqlite import get_db_connection

# 프로젝트 추가
def add_project_to_db(project_name, account_id, region, access_key, secret_key):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO project (project_name, account_id, region, access_key, secret_key)
                VALUES (?, ?, ?, ?, ?)
            """, (project_name, account_id, region, access_key, secret_key))
            connection.commit()
            return True
        except Exception as e:
            st.error(f"프로젝트 추가 오류: {e}")
            return False
        finally:
            connection.close()
    return False

# 프로젝트 목록 조회
def get_projects_from_db():
    connection = get_db_connection()
    projects = []
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM project ORDER BY created_at DESC")
            rows = cursor.fetchall()
            projects = [dict(row) for row in rows]
            # access_key 마스킹 처리
            for project in projects:
                project['access_key'] = project['access_key'][:8] + "..."
                project['secret_key'] = "***"
        except Exception as e:
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
                SET project_name = ?, account_id = ?, region = ?, access_key = ?, secret_key = ?
                WHERE id = ?
            """, (project_name, account_id, region, access_key, secret_key, project_id))
            connection.commit()
            return True
        except Exception as e:
            st.error(f"프로젝트 수정 오류: {e}")
            return False
        finally:
            connection.close()
    return False

# 프로젝트 원본 정보 조회
def get_project_original_info(project_id):
    connection = get_db_connection()
    project_info = None
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM project WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            if row:
                project_info = dict(row)
        except Exception as e:
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
            cursor.execute("DELETE FROM project WHERE id = ?", (project_id,))
            connection.commit()
            return True
        except Exception as e:
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
        except Exception as e:
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
            cursor.execute("SELECT * FROM project WHERE project_name = ?", (project_name,))
            row = cursor.fetchone()
            if row:
                project_info = dict(row)
        except Exception as e:
            st.error(f"프로젝트 정보 조회 오류: {e}")
        finally:
            connection.close()
    return project_info