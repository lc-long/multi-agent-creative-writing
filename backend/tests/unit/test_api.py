"""
Unit Tests for API Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


def test_root_endpoint(client):
    """测试根端点"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data


def test_health_endpoint(client):
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_api_health_endpoint(client):
    """测试API健康检查端点"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_list_agents(client):
    """测试获取Agent列表"""
    response = client.get("/api/v1/agents")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert len(data["agents"]) == 4


def test_create_story_session(client):
    """测试创建故事会话"""
    response = client.post(
        "/api/v1/stories",
        json={
            "theme": "未来世界的AI觉醒",
            "genre": "science_fiction",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["status"] == "pending"


def test_get_story_not_found(client):
    """测试获取不存在的故事"""
    response = client.get("/api/v1/stories/nonexistent")
    assert response.status_code == 404
