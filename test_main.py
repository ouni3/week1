import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from main import app, Base, StudentDB
import os

# 使用内存数据库进行测试
TEST_DATABASE_URL = "sqlite:///./test.db"

# 创建测试引擎
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def test_db():
    """为每个测试创建新的数据库表"""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def client(test_db):
    """创建测试客户端"""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def db_session():
    """创建数据库会话"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_root(client):
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_create_student(client, db_session):
    """测试创建学生"""
    student_data = {"name": "张三", "student_id": 1001}
    response = client.post("/students/", json=student_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "张三"
    assert data["student_id"] == 1001
    assert "id" in data

def test_get_student_exists(client, db_session):
    """测试获取存在的学生"""
    # 先创建学生
    student_data = {"name": "李四", "student_id": 1002}
    create_response = client.post("/students/", json=student_data)
    assert create_response.status_code == 200
    
    # 获取学生
    response = client.get("/students/1002")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "李四"
    assert data["student_id"] == 1002

def test_get_student_not_exists(client, db_session):
    """测试获取不存在的学生"""
    response = client.get("/students/9999")
    assert response.status_code == 200
    assert response.json() == {"error": "学生未找到"}

def test_create_multiple_students(client, db_session):
    """测试创建多个学生"""
    students = [
        {"name": "王五", "student_id": 1003},
        {"name": "赵六", "student_id": 1004},
        {"name": "钱七", "student_id": 1005}
    ]
    
    for student_data in students:
        response = client.post("/students/", json=student_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == student_data["name"]
        assert data["student_id"] == student_data["student_id"]

def test_duplicate_student_id(client, db_session):
    """测试重复的学生ID"""
    student_data = {"name": "孙八", "student_id": 1006}
    
    # 第一次创建
    response1 = client.post("/students/", json=student_data)
    assert response1.status_code == 200
    
    # 第二次创建相同ID的学生（应该失败）
    response2 = client.post("/students/", json=student_data)
    # 由于数据库唯一约束，第二次创建应该返回500错误
    assert response2.status_code == 400
    assert response2.json() == {"error": "学号已存在"}

def test_invalid_student_data(client, db_session):
    """测试无效的学生数据"""
    # 缺少name字段
    invalid_data = {"student_id": 1007}
    response = client.post("/students/", json=invalid_data)
    assert response.status_code == 422  # 验证错误
    
    # 缺少student_id字段
    invalid_data2 = {"name": "周九"}
    response2 = client.post("/students/", json=invalid_data2)
    assert response2.status_code == 422  # 验证错误

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 