from video_knowledge.douyin import (
    DouyinConnector,
    aweme_post_url,
    extract_creator_id,
    extract_seed_video_ids,
    parse_aweme_post_response,
    verify_media_url,
)


PROFILE_URL = (
    "https://www.douyin.com/user/"
    "MS4wLjABAAAAV3KX6fCj_8GMK6EFi7gSiXljnuknI15fGVtcBTSttn0"
    "?from_tab_name=main&vid=7648701859682667811"
)


def test_extract_creator_id_from_profile_url():
    assert (
        extract_creator_id(PROFILE_URL)
        == "MS4wLjABAAAAV3KX6fCj_8GMK6EFi7gSiXljnuknI15fGVtcBTSttn0"
    )


def test_extract_seed_video_ids_from_url_query_and_direct_video_url():
    direct = "https://www.douyin.com/video/7123456789012345678"

    assert extract_seed_video_ids(PROFILE_URL) == ["7648701859682667811"]
    assert extract_seed_video_ids(direct) == ["7123456789012345678"]


def test_parse_video_ids_from_html_links_and_json_shapes():
    html = """
    <a href="/video/7000000000000000001">one</a>
    <script>
      window.__DATA__ = {
        "aweme_id": "7000000000000000002",
        "awemeId": "7000000000000000003",
        "desc": "demo title"
      };
    </script>
    """

    connector = DouyinConnector()

    videos = connector.parse_videos(PROFILE_URL, html)

    assert [video.platform_video_id for video in videos] == [
        "7648701859682667811",
        "7000000000000000001",
        "7000000000000000002",
        "7000000000000000003",
    ]
    assert all(video.creator_id.endswith("BTSttn0") for video in videos)


def test_aweme_post_url_uses_profile_sec_user_id():
    url = aweme_post_url(PROFILE_URL, count=20, cursor=123)

    assert "sec_user_id=MS4wLjABAAAAV3KX6fCj_8GMK6EFi7gSiXljnuknI15fGVtcBTSttn0" in url
    assert "count=20" in url
    assert "max_cursor=123" in url


def test_parse_aweme_post_response_returns_video_list_with_public_play_url():
    payload = {
        "status_code": 0,
        "aweme_list": [
            {
                "aweme_id": "7648701859682667811",
                "desc": "一条视频教会你用升格慢动作锁住炸裂瞬间",
                "create_time": 1780884000,
                "video": {
                    "duration": 35086,
                    "play_addr": {
                        "url_list": [
                            "https://v26-web.douyinvod.com/forbidden-direct.mp4",
                            "https://www.douyin.com/aweme/v1/play/?video_id=v0300&is_play_url=1",
                        ]
                    },
                    "cover": {"url_list": ["https://example.com/cover.jpeg"]},
                },
            },
            {
                "aweme_id": "7648538903279865088",
                "desc": "精准控制AI摄像机",
                "create_time": 1780797600,
                "video": {
                    "duration": 31510,
                    "play_addr_h264": {
                        "url_list": [
                            "https://www.douyin.com/aweme/v1/play/?video_id=v0400&is_play_url=1"
                        ]
                    },
                },
            },
        ],
    }

    videos = parse_aweme_post_response(PROFILE_URL, payload)

    assert [video.platform_video_id for video in videos] == [
        "7648701859682667811",
        "7648538903279865088",
    ]
    assert videos[0].title == "一条视频教会你用升格慢动作锁住炸裂瞬间"
    assert videos[0].duration_seconds == 35
    assert videos[0].public_url == (
        "https://www.douyin.com/aweme/v1/play/?video_id=v0300&is_play_url=1"
    )
    assert videos[0].cover_url == "https://example.com/cover.jpeg"


def test_verify_media_url_returns_final_mp4_metadata():
    class FakeHeaders:
        def get(self, name, default=None):
            return {
                "Content-Type": "video/mp4",
                "Content-Length": "1234",
            }.get(name, default)

    class FakeResponse:
        headers = FakeHeaders()
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def geturl(self):
            return "https://v11.douyinvod.com/final.mp4"

    def fake_open(request, timeout):
        assert request.get_method() == "HEAD"
        return FakeResponse()

    result = verify_media_url(
        "https://www.douyin.com/aweme/v1/play/?video_id=v0300",
        opener=fake_open,
    )

    assert result == {
        "url": "https://www.douyin.com/aweme/v1/play/?video_id=v0300",
        "final_url": "https://v11.douyinvod.com/final.mp4",
        "status": 200,
        "content_type": "video/mp4",
        "content_length": 1234,
        "is_video": True,
    }


def test_list_all_profile_videos_paginates_and_deduplicates():
    pages = [
        {
            "aweme_list": [
                {
                    "aweme_id": "7000000000000000001",
                    "desc": "first",
                    "video": {
                        "play_addr": {
                            "url_list": [
                                "https://www.douyin.com/aweme/v1/play/?video_id=v1"
                            ]
                        }
                    },
                }
            ],
            "has_more": 1,
            "max_cursor": 100,
        },
        {
            "aweme_list": [
                {
                    "aweme_id": "7000000000000000001",
                    "desc": "duplicate",
                    "video": {
                        "play_addr": {
                            "url_list": [
                                "https://www.douyin.com/aweme/v1/play/?video_id=v1"
                            ]
                        }
                    },
                },
                {
                    "aweme_id": "7000000000000000002",
                    "desc": "second",
                    "video": {
                        "play_addr": {
                            "url_list": [
                                "https://www.douyin.com/aweme/v1/play/?video_id=v2"
                            ]
                        }
                    },
                },
            ],
            "has_more": 0,
            "max_cursor": 100,
        },
    ]

    class FakeConnector(DouyinConnector):
        def __init__(self):
            self.urls = []

        def fetch_json(self, url, referer=""):
            self.urls.append(url)
            return pages[len(self.urls) - 1]

    connector = FakeConnector()

    videos = connector.list_all_profile_videos(PROFILE_URL, count=1, max_pages=5)

    assert [video.platform_video_id for video in videos] == [
        "7000000000000000001",
        "7000000000000000002",
    ]
    assert "max_cursor=0" in connector.urls[0]
    assert "max_cursor=100" in connector.urls[1]
