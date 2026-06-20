import json
import subprocess
import sys

from video_knowledge.store import KnowledgeStore


PROFILE_URL = (
    "https://www.douyin.com/user/"
    "MS4wLjABAAAAV3KX6fCj_8GMK6EFi7gSiXljnuknI15fGVtcBTSttn0"
    "?from_tab_name=main&vid=7648701859682667811"
)


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "video_knowledge", *args],
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_subscribe_and_discover_seed_video(tmp_path):
    db_path = tmp_path / "knowledge.sqlite"

    subscribe = run_cli("--db", str(db_path), "subscribe", PROFILE_URL)
    discover = run_cli("--db", str(db_path), "discover", PROFILE_URL, "--no-fetch")

    assert subscribe.returncode == 0, subscribe.stderr
    assert discover.returncode == 0, discover.stderr
    payload = json.loads(discover.stdout)
    assert payload["new_videos"] == 1
    assert payload["videos"][0]["platform_video_id"] == "7648701859682667811"


def test_cli_understand_persists_result_for_discovered_video(tmp_path):
    db_path = tmp_path / "knowledge.sqlite"
    transcript_path = tmp_path / "transcript.txt"
    transcript_path.write_text(
        "0 8 First capture the useful source material.\n"
        "8 18 Then extract concepts and keep timestamp evidence.\n",
        encoding="utf-8",
    )

    discover = run_cli("--db", str(db_path), "discover", PROFILE_URL, "--no-fetch")
    understand = run_cli(
        "--db",
        str(db_path),
        "understand",
        "7648701859682667811",
        "--transcript",
        str(transcript_path),
        "--duration-seconds",
        "18",
    )

    store = KnowledgeStore(db_path)
    video = store.get_video_by_platform_id("douyin", "7648701859682667811")

    assert discover.returncode == 0, discover.stderr
    assert understand.returncode == 0, understand.stderr
    assert video["processing_status"] == "understood"
    assert store.count("knowledge_items") == 2


def test_cli_ark_understand_dry_run_builds_video_payload(tmp_path):
    db_path = tmp_path / "knowledge.sqlite"

    result = run_cli(
        "--db",
        str(db_path),
        "ark-understand",
        "7648701859682667811",
        "--video-url",
        "https://www.douyin.com/aweme/v1/play/?video_id=v0300&is_play_url=1",
        "--model",
        "ep-20260513103751-6d9f9",
        "--ark-api-key",
        "secret-for-test",
        "--fps",
        "5",
        "--reasoning-effort",
        "high",
        "--dry-run",
    )

    assert result.returncode == 0, result.stderr
    assert "secret-for-test" not in result.stdout
    payload = json.loads(result.stdout)
    assert payload["model"] == "ep-20260513103751-6d9f9"
    assert payload["reasoning"] == {"effort": "high"}
    assert payload["messages"][0]["content"][1]["video_url"]["fps"] == 5
    assert "response_format" not in payload


def test_cli_distill_profile_dry_run_reports_videos_without_model_call(tmp_path):
    db_path = tmp_path / "knowledge.sqlite"
    fixture = tmp_path / "aweme_post.json"
    fixture.write_text(
        json.dumps(
            {
                "aweme_list": [
                    {
                        "aweme_id": "7000000000000000001",
                        "desc": "first lesson",
                        "video": {
                            "play_addr": {
                                "url_list": [
                                    "https://www.douyin.com/aweme/v1/play/?video_id=v1"
                                ]
                            }
                        },
                    }
                ],
                "has_more": 0,
                "max_cursor": 0,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = run_cli(
        "--db",
        str(db_path),
        "distill-profile",
        PROFILE_URL,
        "--model",
        "ep-20260513103751-6d9f9",
        "--ark-api-key",
        "secret-for-test",
        "--fixture-json",
        str(fixture),
        "--dry-run",
    )

    assert result.returncode == 0, result.stderr
    assert "secret-for-test" not in result.stdout
    payload = json.loads(result.stdout)
    assert payload == {
        "discovered": 1,
        "to_distill": 1,
        "videos": [
            {
                "platform_video_id": "7000000000000000001",
                "title": "first lesson",
                "has_media_url": True,
            }
        ],
    }
