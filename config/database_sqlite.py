import sqlite3
import streamlit as st
import os

# SQLite 데이터베이스 연결
def get_db_connection():
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'cloud_visualizer.db')
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
        return connection
    except Exception as e:
        st.error(f"데이터베이스 연결 오류: {e}")
        return None

# 프로젝트 테이블 생성
def create_projects_table():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    region TEXT NOT NULL,
                    access_key TEXT NOT NULL,
                    secret_key TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            connection.commit()
        except Exception as e:
            st.error(f"테이블 생성 오류: {e}")
        finally:
            connection.close()