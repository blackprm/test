from video_knowledge.douyin import DouyinVideo
from video_knowledge.store import KnowledgeStore


PROFILE_URL = (
    "https://www.douyin.com/user/"
    "MS4wLjABAAAAV3KX6fCj_8GMK6EFi7gSiXljnuknI15fGVtcBTSttn0"
    "?from_tab_name=main&vid=7648701859682667811"
)


def test_subscription_discovery_is_idempotent(tmp_path):
    store = KnowledgeStore(tmp_path / "knowledge.sqlite")
    subscription = store.add_subscription(PROFILE_URL, user_id="local")
    video = DouyinVideo(
        platform_video_id="7648701859682667811",
        creator_id=subscription.creator_id,
        source_url="https://www.douyin.com/video/7648701859682667811",
        title="Seed video",
        public_url="https://www.douyin.com/aweme/v1/play/?video_id=v0300",
        cover_url="https://example.com/cover.jpeg",
    )

    first = store.record_discovered_videos(subscription.id, [video])
    second = store.record_discovered_videos(subscription.id, [video])

    assert len(first) == 1
    assert second == []
    assert store.count("videos") == 1
    assert store.count("jobs") == 1
    assert first[0]["media_url"] == "https://www.douyin.com/aweme/v1/play/?video_id=v0300"
    assert first[0]["cover_url"] == "https://example.com/cover.jpeg"


def test_completed_understanding_marks_video_and_persists_knowledge(tmp_path):
    store = KnowledgeStore(tmp_path / "knowledge.sqlite")
    subscription = store.add_subscription(PROFILE_URL, user_id="local")
    video = DouyinVideo(
        platform_video_id="7648701859682667811",
        creator_id=subscription.creator_id,
        source_url="https://www.douyin.com/video/7648701859682667811",
    )
    [record] = store.record_discovered_videos(subscription.id, [video])
    result = {
        "summary": "This video explains a repeatable learning workflow.",
        "chapters": [
            {
                "title": "Workflow",
                "start_time_seconds": 0,
                "end_time_seconds": 42,
                "summary": "Capture, extract, review.",
            }
        ],
        "knowledge_items": [
            {
                "title": "Review loop",
                "content": "Every extracted note should keep source evidence.",
                "start_time_seconds": 12,
                "end_time_seconds": 20,
                "evidence_text": "keep source evidence",
                "confidence": 0.86,
                "needs_verification": False,
                "tags": ["learning"],
            }
        ],
        "action_items": ["Review low-confidence claims."],
    }

    store.save_understanding(record["id"], result)

    assert store.get_video(record["id"])["processing_status"] == "understood"
    assert store.count("knowledge_items") == 1
    assert store.get_job_for_video(record["id"], "understand_video")["status"] == "completed"


def test_save_context_pack_persists_markdown_without_structured_items(tmp_path):
    store = KnowledgeStore(tmp_path / "knowledge.sqlite")
    subscription = store.add_subscription(PROFILE_URL, user_id="local")
    video = DouyinVideo(
        platform_video_id="7648701859682667811",
        creator_id=subscription.creator_id,
        source_url="https://www.douyin.com/video/7648701859682667811",
    )
    [record] = store.record_discovered_videos(subscription.id, [video])
    context_pack = (
        "# 教学知识包\n\n"
        "## 教学目标\n"
        "教会用户用升格慢动作强化运动镜头。\n"
    )

    store.save_context_pack(record["id"], context_pack)

    saved = store.get_video(record["id"])
    assert saved["processing_status"] == "understood"
    assert saved["summary"] == "教会用户用升格慢动作强化运动镜头。"
    assert saved["context_pack"] == context_pack
    assert store.count("knowledge_items") == 0
    assert store.get_job_for_video(record["id"], "understand_video")["status"] == "completed"
