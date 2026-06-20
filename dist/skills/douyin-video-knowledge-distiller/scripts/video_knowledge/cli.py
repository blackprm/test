import argparse
import json
import os
import shlex
import sys

from .ark import ArkVideoKnowledgeClient
from .douyin import DouyinConnector, parse_aweme_post_response
from .store import KnowledgeStore
from .understanding import (
    parse_transcript_text,
    understand_transcript,
    understand_with_model_command,
)


DEFAULT_DB = "data/video_knowledge/knowledge.sqlite"


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    store = KnowledgeStore(args.db)

    try:
        if args.command == "subscribe":
            return subscribe(store, args)
        if args.command == "discover":
            return discover(store, args)
        if args.command == "understand":
            return understand(store, args)
        if args.command == "ark-understand":
            return ark_understand(store, args)
        if args.command == "distill-profile":
            return distill_profile(store, args)
    except Exception as exc:
        print("error: {0}".format(exc), file=sys.stderr)
        return 1

    parser.print_help()
    return 2


def build_parser():
    parser = argparse.ArgumentParser(
        description="Subscribe to Douyin creators and extract timestamped knowledge."
    )
    parser.add_argument("--db", default=DEFAULT_DB, help="SQLite database path.")
    subparsers = parser.add_subparsers(dest="command")

    subscribe_parser = subparsers.add_parser("subscribe")
    subscribe_parser.add_argument("creator_url")
    subscribe_parser.add_argument("--user-id", default="local")

    discover_parser = subparsers.add_parser("discover")
    discover_parser.add_argument("creator_url")
    discover_parser.add_argument("--user-id", default="local")
    discover_parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="Only use video IDs already present in the URL.",
    )

    understand_parser = subparsers.add_parser("understand")
    understand_parser.add_argument("video_id")
    understand_parser.add_argument("--transcript", required=True)
    understand_parser.add_argument("--title", default="")
    understand_parser.add_argument("--source-url", default="")
    understand_parser.add_argument("--duration-seconds", type=int, default=0)
    understand_parser.add_argument(
        "--model-command",
        help="External command that reads JSON stdin and returns structured JSON.",
    )

    ark_parser = subparsers.add_parser("ark-understand")
    ark_parser.add_argument("video_id")
    ark_parser.add_argument("--video-url", default="")
    ark_parser.add_argument("--model", required=True)
    ark_parser.add_argument("--ark-api-key", default="")
    ark_parser.add_argument("--ark-api-key-env", default="ARK_API_KEY")
    ark_parser.add_argument("--base-url", default="https://ark.cn-beijing.volces.com/api/v3")
    ark_parser.add_argument("--fps", type=float, default=5)
    ark_parser.add_argument("--reasoning-effort", default="high")
    ark_parser.add_argument("--dry-run", action="store_true")
    ark_parser.add_argument("--output", default="")

    distill_parser = subparsers.add_parser("distill-profile")
    distill_parser.add_argument("creator_url")
    distill_parser.add_argument("--user-id", default="local")
    distill_parser.add_argument("--model", required=True)
    distill_parser.add_argument("--ark-api-key", default="")
    distill_parser.add_argument("--ark-api-key-env", default="ARK_API_KEY")
    distill_parser.add_argument("--base-url", default="https://ark.cn-beijing.volces.com/api/v3")
    distill_parser.add_argument("--fps", type=float, default=5)
    distill_parser.add_argument("--reasoning-effort", default="high")
    distill_parser.add_argument("--count", type=int, default=10)
    distill_parser.add_argument("--max-pages", type=int, default=20)
    distill_parser.add_argument("--limit", type=int, default=0)
    distill_parser.add_argument("--out-dir", default="data/video_knowledge_pipeline/context_packs")
    distill_parser.add_argument("--fixture-json", default="")
    distill_parser.add_argument("--dry-run", action="store_true")

    return parser


def subscribe(store, args):
    subscription = store.add_subscription(args.creator_url, user_id=args.user_id)
    print_json(subscription.__dict__)
    return 0


def discover(store, args):
    subscription = store.add_subscription(args.creator_url, user_id=args.user_id)
    connector = DouyinConnector()
    videos = connector.discover(args.creator_url, fetch=not args.no_fetch)
    inserted = store.record_discovered_videos(subscription.id, videos)
    print_json({"new_videos": len(inserted), "videos": inserted})
    return 0


def understand(store, args):
    transcript = parse_transcript_text(read_text(args.transcript))
    source_url = args.source_url or "https://www.douyin.com/video/{0}".format(args.video_id)
    title = args.title or "Douyin video {0}".format(args.video_id)
    if args.model_command:
        command = shlex.split(args.model_command)
        result = understand_with_model_command(
            command, title, source_url, args.duration_seconds, transcript
        )
    else:
        result = understand_transcript(
            title, source_url, args.duration_seconds, transcript
        )
    video = store.get_video_by_platform_id("douyin", args.video_id)
    if video:
        store.save_understanding(video["id"], result)
    print_json(result)
    return 0


def ark_understand(store, args):
    video = store.get_video_by_platform_id("douyin", args.video_id)
    video_url = args.video_url or ((video or {}).get("media_url") or "")
    if not video_url:
        raise ValueError("A video URL is required. Pass --video-url or run discover first.")
    api_key = args.ark_api_key or os.environ.get(args.ark_api_key_env, "")
    client = ArkVideoKnowledgeClient(
        api_key=api_key,
        model=args.model,
        fps=args.fps,
        reasoning_effort=args.reasoning_effort,
        base_url=args.base_url,
    )
    if args.dry_run:
        print_json(client.build_payload(video_url))
        return 0
    result = client.extract(video_url)
    if video:
        if isinstance(result, str):
            store.save_context_pack(video["id"], result)
        else:
            store.save_understanding(video["id"], result)
    if args.output:
        output_text = (
            result
            if isinstance(result, str)
            else json.dumps(result, ensure_ascii=False, indent=2)
        )
        write_text(args.output, output_text)
    if isinstance(result, str):
        print(result)
    else:
        print_json(result)
    return 0


def distill_profile(store, args):
    subscription = store.add_subscription(args.creator_url, user_id=args.user_id)
    videos = load_profile_videos(args)
    inserted = store.record_discovered_videos(subscription.id, videos)
    all_records = videos[: args.limit] if args.limit else videos
    summary = {
        "discovered": len(videos),
        "to_distill": len(all_records),
        "videos": [
            {
                "platform_video_id": video.platform_video_id,
                "title": video.title,
                "has_media_url": bool(video.public_url),
            }
            for video in all_records
        ],
    }
    if args.dry_run:
        print_json(summary)
        return 0

    api_key = args.ark_api_key or os.environ.get(args.ark_api_key_env, "")
    client = ArkVideoKnowledgeClient(
        api_key=api_key,
        model=args.model,
        fps=args.fps,
        reasoning_effort=args.reasoning_effort,
        base_url=args.base_url,
    )
    ensure_dir(args.out_dir)
    results = []
    for video in all_records:
        if not video.public_url:
            results.append(
                {
                    "platform_video_id": video.platform_video_id,
                    "status": "skipped",
                    "reason": "missing media url",
                }
            )
            continue
        context_pack = client.extract(video.public_url)
        row = store.get_video_by_platform_id("douyin", video.platform_video_id)
        if row:
            store.save_context_pack(row["id"], context_pack)
        output_path = os.path.join(args.out_dir, video.platform_video_id + ".md")
        write_text(output_path, context_pack)
        results.append(
            {
                "platform_video_id": video.platform_video_id,
                "status": "completed",
                "output": output_path,
            }
        )
    print_json({"discovered": len(videos), "processed": results})
    return 0


def load_profile_videos(args):
    if args.fixture_json:
        payload = json.loads(read_text(args.fixture_json))
        return parse_aweme_post_response(args.creator_url, payload)
    connector = DouyinConnector()
    return connector.list_all_profile_videos(
        args.creator_url, count=args.count, max_pages=args.max_pages
    )


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def read_text(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def write_text(path, text):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def print_json(payload):
    print(json.dumps(payload, ensure_ascii=False, indent=2))
