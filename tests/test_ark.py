from video_knowledge.ark import (
    ArkVideoKnowledgeClient,
    knowledge_prompt,
    parse_chat_completion_content,
)
import json


def test_ark_payload_uses_video_url_fps_and_high_reasoning():
    client = ArkVideoKnowledgeClient(
        api_key="test-key",
        model="ep-20260513103751-6d9f9",
        fps=5,
        reasoning_effort="high",
    )

    payload = client.build_payload(
        "https://www.douyin.com/aweme/v1/play/?video_id=v0300&is_play_url=1"
    )

    assert payload["model"] == "ep-20260513103751-6d9f9"
    assert payload["reasoning"] == {"effort": "high"}
    assert "response_format" not in payload
    content = payload["messages"][0]["content"]
    assert content[0]["type"] == "text"
    assert content[1] == {
        "type": "video_url",
        "video_url": {
            "url": "https://www.douyin.com/aweme/v1/play/?video_id=v0300&is_play_url=1",
            "fps": 5,
        },
    }


def test_knowledge_prompt_requests_minimal_markdown_context_pack_without_timestamps():
    prompt = knowledge_prompt()

    assert "# 教学知识包" in prompt
    assert "## 教学目标" in prompt
    assert "## 适用场景" in prompt
    assert "## 核心方法" in prompt
    assert "## 可复用模板" in prompt
    assert "## 关键判断" in prompt
    assert "## 注意事项" in prompt
    assert "JSON" not in prompt
    assert "时间戳" not in prompt


def test_knowledge_prompt_forces_actionable_core_method_details():
    prompt = knowledge_prompt()

    assert "不要只写概念性步骤" in prompt
    assert "为什么做" in prompt
    assert "输入材料" in prompt
    assert "具体操作" in prompt
    assert "参数或提示词片段" in prompt
    assert "产出长什么样" in prompt
    assert "失败时怎么调" in prompt


def test_parse_chat_completion_content_returns_markdown_context_pack():
    response = {
        "choices": [
            {
                "message": {
                    "content": "# 教学知识包\n\n## 教学目标\n讲解 AI 运镜。"
                }
            }
        ]
    }

    result = parse_chat_completion_content(response)

    assert result == "# 教学知识包\n\n## 教学目标\n讲解 AI 运镜。"


def test_ark_extract_retries_transient_disconnect():
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return json.dumps(
                {"choices": [{"message": {"content": "# 教学知识包"}}]},
                ensure_ascii=False,
            ).encode("utf-8")

    calls = {"count": 0}

    def fake_opener(request, timeout):
        calls["count"] += 1
        if calls["count"] == 1:
            raise ConnectionResetError("reset")
        return FakeResponse()

    client = ArkVideoKnowledgeClient(
        api_key="test-key",
        model="ep-20260513103751-6d9f9",
        opener=fake_opener,
        retry_sleep=lambda seconds: None,
    )

    assert client.extract("https://example.com/video.mp4", timeout=1, max_attempts=2) == "# 教学知识包"
    assert calls["count"] == 2
