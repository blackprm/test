from dataclasses import dataclass
from pathlib import Path
import json
import sqlite3
from datetime import datetime, timezone

from .douyin import extract_creator_id


@dataclass(frozen=True)
class Subscription:
    id: int
    user_id: str
    platform: str
    creator_id: str
    creator_url: str
    status: str


class KnowledgeStore:
    def __init__(self, path):
        self.path = Path(path)
        if self.path.parent:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.path))
        self.connection.row_factory = sqlite3.Row
        self._migrate()

    def add_subscription(self, creator_url, user_id="local"):
        creator_id = extract_creator_id(creator_url)
        if not creator_id:
            raise ValueError("Could not extract Douyin creator id from URL.")

        now = utc_now()
        with self.connection:
            self.connection.execute(
                """
                insert into subscriptions (
                    user_id, platform, creator_id, creator_url, status,
                    created_at, updated_at
                )
                values (?, 'douyin', ?, ?, 'active', ?, ?)
                on conflict(user_id, platform, creator_id) do update set
                    creator_url = excluded.creator_url,
                    status = 'active',
                    updated_at = excluded.updated_at
                """,
                (user_id, creator_id, creator_url, now, now),
            )
        return self.get_subscription(user_id, creator_id)

    def get_subscription(self, user_id, creator_id):
        row = self.connection.execute(
            """
            select id, user_id, platform, creator_id, creator_url, status
            from subscriptions
            where user_id = ? and platform = 'douyin' and creator_id = ?
            """,
            (user_id, creator_id),
        ).fetchone()
        if row is None:
            return None
        return Subscription(**dict(row))

    def record_discovered_videos(self, subscription_id, videos):
        inserted = []
        now = utc_now()
        with self.connection:
            self.connection.execute(
                "update subscriptions set last_checked_at = ?, updated_at = ? where id = ?",
                (now, now, subscription_id),
            )
            for video in videos:
                cursor = self.connection.execute(
                    """
                    insert into videos (
                        platform, platform_video_id, subscription_id, creator_id,
                        title, description, source_url, media_url, cover_url, published_at,
                        duration_seconds, processing_status, created_at, updated_at
                    )
                    values (
                        'douyin', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'queued', ?, ?
                    )
                    on conflict(platform, platform_video_id) do nothing
                    """,
                    (
                        video.platform_video_id,
                        subscription_id,
                        video.creator_id,
                        video.title,
                        video.description,
                        video.source_url,
                        video.public_url,
                        video.cover_url,
                        video.published_at,
                        video.duration_seconds,
                        now,
                        now,
                    ),
                )
                if cursor.rowcount != 1:
                    continue

                record = self.connection.execute(
                    """
                    select *
                    from videos
                    where platform = 'douyin' and platform_video_id = ?
                    """,
                    (video.platform_video_id,),
                ).fetchone()
                idempotency_key = "understand_video:{0}".format(record["id"])
                self.connection.execute(
                    """
                    insert into jobs (
                        kind, video_id, status, idempotency_key, created_at, updated_at
                    )
                    values ('understand_video', ?, 'queued', ?, ?, ?)
                    on conflict(idempotency_key) do nothing
                    """,
                    (record["id"], idempotency_key, now, now),
                )
                inserted.append(dict(record))
        return inserted

    def save_understanding(self, video_id, result):
        now = utc_now()
        with self.connection:
            self.connection.execute(
                """
                update videos
                set processing_status = 'understood',
                    summary = ?,
                    updated_at = ?
                where id = ?
                """,
                (result.get("summary", ""), now, video_id),
            )
            self.connection.execute(
                """
                update jobs
                set status = 'completed',
                    updated_at = ?
                where video_id = ? and kind = 'understand_video'
                """,
                (now, video_id),
            )
            self.connection.execute("delete from chapters where video_id = ?", (video_id,))
            self.connection.execute(
                "delete from knowledge_items where video_id = ?", (video_id,)
            )
            for chapter in result.get("chapters", []):
                self.connection.execute(
                    """
                    insert into chapters (
                        video_id, title, summary, start_time_seconds,
                        end_time_seconds, created_at
                    )
                    values (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        video_id,
                        chapter.get("title", ""),
                        chapter.get("summary", ""),
                        chapter.get("start_time_seconds", 0),
                        chapter.get("end_time_seconds", 0),
                        now,
                    ),
                )
            for item in result.get("knowledge_items", []):
                self.connection.execute(
                    """
                    insert into knowledge_items (
                        video_id, title, content, tags, start_time_seconds,
                        end_time_seconds, evidence_text, confidence,
                        needs_verification, created_at
                    )
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        video_id,
                        item.get("title", ""),
                        item.get("content", ""),
                        json.dumps(item.get("tags", []), ensure_ascii=False),
                        item.get("start_time_seconds", 0),
                        item.get("end_time_seconds", 0),
                        item.get("evidence_text", ""),
                        item.get("confidence", 0),
                        1 if item.get("needs_verification") else 0,
                        now,
                    ),
                )

    def save_context_pack(self, video_id, context_pack):
        now = utc_now()
        summary = first_content_line(context_pack)
        with self.connection:
            self.connection.execute(
                """
                update videos
                set processing_status = 'understood',
                    summary = ?,
                    context_pack = ?,
                    updated_at = ?
                where id = ?
                """,
                (summary, context_pack, now, video_id),
            )
            self.connection.execute(
                """
                update jobs
                set status = 'completed',
                    updated_at = ?
                where video_id = ? and kind = 'understand_video'
                """,
                (now, video_id),
            )

    def get_video(self, video_id):
        row = self.connection.execute(
            "select * from videos where id = ?", (video_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_video_by_platform_id(self, platform, platform_video_id):
        row = self.connection.execute(
            """
            select *
            from videos
            where platform = ? and platform_video_id = ?
            """,
            (platform, platform_video_id),
        ).fetchone()
        return dict(row) if row else None

    def get_job_for_video(self, video_id, kind):
        row = self.connection.execute(
            """
            select *
            from jobs
            where video_id = ? and kind = ?
            """,
            (video_id, kind),
        ).fetchone()
        return dict(row) if row else None

    def count(self, table_name):
        if table_name not in {
            "subscriptions",
            "videos",
            "jobs",
            "chapters",
            "knowledge_items",
        }:
            raise ValueError("Unsupported table name: {0}".format(table_name))
        row = self.connection.execute(
            "select count(*) as total from {0}".format(table_name)
        ).fetchone()
        return row["total"]

    def _migrate(self):
        with self.connection:
            self.connection.executescript(
                """
                create table if not exists subscriptions (
                    id integer primary key autoincrement,
                    user_id text not null,
                    platform text not null,
                    creator_id text not null,
                    creator_url text not null,
                    status text not null,
                    last_checked_at text,
                    last_success_at text,
                    failure_count integer not null default 0,
                    created_at text not null,
                    updated_at text not null,
                    unique(user_id, platform, creator_id)
                );

                create table if not exists videos (
                    id integer primary key autoincrement,
                    platform text not null,
                    platform_video_id text not null,
                    subscription_id integer not null,
                    creator_id text not null,
                    title text not null default '',
                    description text not null default '',
                    source_url text not null,
                    media_url text not null default '',
                    cover_url text not null default '',
                    published_at text not null default '',
                    duration_seconds integer not null default 0,
                    processing_status text not null,
                    summary text not null default '',
                    context_pack text not null default '',
                    created_at text not null,
                    updated_at text not null,
                    unique(platform, platform_video_id)
                );

                create table if not exists jobs (
                    id integer primary key autoincrement,
                    kind text not null,
                    video_id integer not null,
                    status text not null,
                    idempotency_key text not null unique,
                    failure_reason text not null default '',
                    created_at text not null,
                    updated_at text not null
                );

                create table if not exists chapters (
                    id integer primary key autoincrement,
                    video_id integer not null,
                    title text not null,
                    summary text not null,
                    start_time_seconds integer not null,
                    end_time_seconds integer not null,
                    created_at text not null
                );

                create table if not exists knowledge_items (
                    id integer primary key autoincrement,
                    video_id integer not null,
                    title text not null,
                    content text not null,
                    tags text not null,
                    start_time_seconds integer not null,
                    end_time_seconds integer not null,
                    evidence_text text not null,
                    confidence real not null,
                    needs_verification integer not null,
                    created_at text not null
                );
                """
            )
            ensure_column(self.connection, "videos", "media_url", "text not null default ''")
            ensure_column(self.connection, "videos", "cover_url", "text not null default ''")
            ensure_column(self.connection, "videos", "context_pack", "text not null default ''")


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def first_content_line(text):
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        return stripped
    return ""


def ensure_column(connection, table_name, column_name, column_type):
    rows = connection.execute("pragma table_info({0})".format(table_name)).fetchall()
    if any(row["name"] == column_name for row in rows):
        return
    connection.execute(
        "alter table {0} add column {1} {2}".format(
            table_name, column_name, column_type
        )
    )
