from dataclasses import dataclass
import json
import re
import urllib.parse
import urllib.error
import urllib.request


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


@dataclass(frozen=True)
class DouyinVideo:
    platform_video_id: str
    creator_id: str
    source_url: str
    title: str = ""
    description: str = ""
    published_at: str = ""
    duration_seconds: int = 0
    public_url: str = ""
    cover_url: str = ""


def extract_creator_id(url_or_id):
    parsed = urllib.parse.urlparse(url_or_id)
    if not parsed.scheme and "/" not in url_or_id and "?" not in url_or_id:
        return url_or_id

    match = re.search(r"/user/([^/?#]+)", parsed.path)
    if match:
        return urllib.parse.unquote(match.group(1))
    return ""


def extract_seed_video_ids(url_or_text):
    ids = []

    def add(value):
        if value and re.fullmatch(r"\d{10,25}", value) and value not in ids:
            ids.append(value)

    parsed = urllib.parse.urlparse(url_or_text)
    query = urllib.parse.parse_qs(parsed.query)
    for key in ("vid", "video_id", "aweme_id", "awemeId"):
        for value in query.get(key, []):
            add(value)

    for match in re.finditer(r"/video/(\d{10,25})", url_or_text):
        add(match.group(1))

    return ids


class DouyinConnector:
    """Conservative Douyin metadata discovery from public page snapshots."""

    def fetch_json(self, url, referer="https://www.douyin.com/"):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Referer": referer,
                "Accept": "application/json, text/plain, */*",
            },
        )
        with urllib.request.urlopen(request, timeout=45) as response:
            text = response.read().decode("utf-8", "replace")
        try:
            return json.loads(text)
        except ValueError as exc:
            raise RuntimeError(
                "Douyin API did not return JSON: {0}".format(text[:120])
            ) from exc

    def fetch_html(self, url):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=45) as response:
            return response.read().decode("utf-8", "replace")

    def discover(self, creator_url, fetch=True):
        if fetch:
            return self.list_profile_videos(creator_url)
        html = self.fetch_html(creator_url) if fetch else ""
        return self.parse_videos(creator_url, html)

    def list_profile_videos(self, creator_url, count=10, cursor=0):
        payload = self.fetch_json(
            aweme_post_url(creator_url, count=count, cursor=cursor),
            referer=creator_url,
        )
        return parse_aweme_post_response(creator_url, payload)

    def list_all_profile_videos(self, creator_url, count=10, max_pages=20):
        cursor = 0
        seen = set()
        videos = []
        for _page in range(max_pages):
            payload = self.fetch_json(
                aweme_post_url(creator_url, count=count, cursor=cursor),
                referer=creator_url,
            )
            for video in parse_aweme_post_response(creator_url, payload):
                if video.platform_video_id in seen:
                    continue
                seen.add(video.platform_video_id)
                videos.append(video)

            next_cursor = payload.get("max_cursor")
            has_more = bool(payload.get("has_more"))
            if not has_more or not next_cursor or next_cursor == cursor:
                break
            cursor = next_cursor
        return videos

    def parse_videos(self, creator_url, html):
        creator_id = extract_creator_id(creator_url)
        video_ids = []

        def add(video_id):
            if video_id and video_id not in video_ids:
                video_ids.append(video_id)

        for video_id in extract_seed_video_ids(creator_url):
            add(video_id)

        for video_id in extract_seed_video_ids(html or ""):
            add(video_id)

        for video_id in _extract_json_video_ids(html or ""):
            add(video_id)

        return [
            DouyinVideo(
                platform_video_id=video_id,
                creator_id=creator_id,
                source_url="https://www.douyin.com/video/{0}".format(video_id),
            )
            for video_id in video_ids
        ]


def _extract_json_video_ids(html):
    ids = []

    def add(value):
        if value and value not in ids:
            ids.append(value)

    for pattern in (
        r'"(?:aweme_id|awemeId|video_id|videoId)"\s*:\s*"(\d{10,25})"',
        r"'(?:aweme_id|awemeId|video_id|videoId)'\s*:\s*'(\d{10,25})'",
    ):
        for match in re.finditer(pattern, html):
            add(match.group(1))

    for payload in _render_data_payloads(html):
        for value in _walk_json(payload):
            if isinstance(value, str) and re.fullmatch(r"\d{10,25}", value):
                add(value)

    return ids


def aweme_post_url(creator_url_or_id, count=10, cursor=0):
    creator_id = extract_creator_id(creator_url_or_id)
    query = urllib.parse.urlencode(
        {
            "sec_user_id": creator_id,
            "count": count,
            "max_cursor": cursor,
            "aid": 6383,
            "device_platform": "webapp",
        }
    )
    return "https://www.douyin.com/aweme/v1/web/aweme/post/?{0}".format(query)


def parse_aweme_post_response(creator_url_or_id, payload):
    creator_id = extract_creator_id(creator_url_or_id)
    videos = []
    for item in payload.get("aweme_list") or []:
        aweme_id = str(item.get("aweme_id") or "")
        if not aweme_id:
            continue
        video = item.get("video") or {}
        duration_ms = int(video.get("duration") or 0)
        videos.append(
            DouyinVideo(
                platform_video_id=aweme_id,
                creator_id=creator_id,
                source_url="https://www.douyin.com/video/{0}".format(aweme_id),
                title=(item.get("desc") or "").splitlines()[0],
                description=item.get("desc") or "",
                published_at=str(item.get("create_time") or ""),
                duration_seconds=round(duration_ms / 1000) if duration_ms else 0,
                public_url=select_public_play_url(video),
                cover_url=first_url((video.get("cover") or {}).get("url_list")),
            )
        )
    return videos


def select_public_play_url(video):
    urls = []
    for key in ("play_addr", "play_addr_h264", "download_addr"):
        source = video.get(key) or {}
        urls.extend(source.get("url_list") or [])
    for url in urls:
        if "www.douyin.com/aweme/v1/play" in url:
            return url
    return urls[0] if urls else ""


def first_url(urls):
    if isinstance(urls, list) and urls:
        return str(urls[0])
    return ""


def verify_media_url(url, opener=None, timeout=45):
    opener = opener or urllib.request.urlopen
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT},
        method="HEAD",
    )
    with opener(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        content_length = int(response.headers.get("Content-Length", "0") or 0)
        status = getattr(response, "status", 0) or 0
        final_url = response.geturl()
    return {
        "url": url,
        "final_url": final_url,
        "status": status,
        "content_type": content_type,
        "content_length": content_length,
        "is_video": content_type.startswith("video/"),
    }


def _render_data_payloads(html):
    pattern = r'<script[^>]*id=["\']RENDER_DATA["\'][^>]*>(.*?)</script>'
    for match in re.finditer(pattern, html, flags=re.DOTALL):
        text = urllib.parse.unquote(match.group(1))
        try:
            yield json.loads(text)
        except ValueError:
            continue


def _walk_json(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"aweme_id", "awemeId", "video_id", "videoId"}:
                yield child
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)
