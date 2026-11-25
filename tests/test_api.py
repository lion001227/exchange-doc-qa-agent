from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_chat_success(monkeypatch):
    from backend import main

    def fake_ask_agent(question,thread_id):
        return f"已收到问题：{question}"
    monkeypatch.setattr(main, "ask_agent", fake_ask_agent)

    response = client.post(
        "/api/chat",
            json={"question":"测试问题","thread_id":"test1"})
    assert response.status_code == 200
    assert response.json()["answer"]== "已收到问题：测试问题"
    assert response.json()["thread_id"]== "test1"

def test_chat_empty_question():
    response = client.post("/api/chat",
            json={"question":"","thread_id":"test1"})
    assert response.status_code == 422

