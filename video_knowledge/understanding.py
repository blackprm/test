from dataclasses import dataclass
import json
import re
import subprocess


@dataclass(frozen=True)
class TranscriptSegment:
    start_time_seconds: int
    end_time_seconds: int
    text: str


def understand_transcript(title, source_url, duration_seconds, transcript):
    segments = [
        TranscriptSegment(
            clamp(segment.start_time_seconds, duration_seconds),
            clamp(segment.end_time_seconds, duration_seconds),
            segment.text.strip(),
        )
        for segment in transcript
        if segment.text.strip()
    ]
    if not segments:
        return empty_result(title, source_url)

    summary = " ".join(segment.text for segment in segments[:3])
    end_time = max(segment.end_time_seconds for segment in segments)
    knowledge_items = [
        {
            "title": short_title(segment.text),
            "content": segment.text,
            "tags": infer_tags(segment.text),
            "start_time_seconds": segment.start_time_seconds,
            "end_time_seconds": segment.end_time_seconds,
            "evidence_text": segment.text,
            "confidence": 0.72,
            "needs_verification": needs_verification(segment.text),
        }
        for segment in segments[:8]
    ]

    return {
        "title": title,
        "source_url": source_url,
        "summary": summary,
        "chapters": [
            {
                "title": title or "Video notes",
                "start_time_seconds": segments[0].start_time_seconds,
                "end_time_seconds": end_time,
                "summary": summary,
            }
        ],
        "knowledge_items": knowledge_items,
        "action_items": extract_action_items(segments),
        "low_confidence_notes": [
            item["content"] for item in knowledge_items if item["needs_verification"]
        ],
    }


def understand_with_model_command(command, title, source_url, duration_seconds, transcript):
    payload = {
        "title": title,
        "source_url": source_url,
        "duration_seconds": duration_seconds,
        "transcript": [segment.__dict__ for segment in transcript],
        "required_output_shape": {
            "summary": "string",
            "chapters": "list with title, start_time_seconds, end_time_seconds, summary",
            "knowledge_items": (
                "list with title, content, tags, start_time_seconds, "
                "end_time_seconds, evidence_text, confidence, needs_verification"
            ),
            "action_items": "list of strings",
        },
    }
    completed = subprocess.run(
        command,
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "model command failed")
    try:
        result = json.loads(completed.stdout)
    except ValueError as exc:
        raise RuntimeError("model command did not return JSON") from exc
    return normalize_result(result, title, source_url, duration_seconds)


def parse_transcript_text(text):
    segments = []
    for index, line in enumerate(text.splitlines()):
        stripped = line.strip()
        if not stripped:
            continue
        match = re.match(r"\[?(\d+)(?:\s*[-,:]\s*|\s+)(\d+)\]?\s+(.+)", stripped)
        if match:
            start, end, content = match.groups()
            segments.append(TranscriptSegment(int(start), int(end), content))
        else:
            start = index * 10
            segments.append(TranscriptSegment(start, start + 10, stripped))
    return segments


def normalize_result(result, title, source_url, duration_seconds):
    normalized = {
        "title": result.get("title") or title,
        "source_url": result.get("source_url") or source_url,
        "summary": result.get("summary", ""),
        "chapters": [],
        "knowledge_items": [],
        "action_items": list(result.get("action_items", [])),
        "low_confidence_notes": list(result.get("low_confidence_notes", [])),
    }
    for chapter in result.get("chapters", []):
        normalized["chapters"].append(
            {
                "title": chapter.get("title", ""),
                "summary": chapter.get("summary", ""),
                "start_time_seconds": clamp(
                    int(chapter.get("start_time_seconds", 0)), duration_seconds
                ),
                "end_time_seconds": clamp(
                    int(chapter.get("end_time_seconds", 0)), duration_seconds
                ),
            }
        )
    for item in result.get("knowledge_items", []):
        normalized["knowledge_items"].append(
            {
                "title": item.get("title", ""),
                "content": item.get("content", ""),
                "tags": list(item.get("tags", [])),
                "start_time_seconds": clamp(
                    int(item.get("start_time_seconds", 0)), duration_seconds
                ),
                "end_time_seconds": clamp(
                    int(item.get("end_time_seconds", 0)), duration_seconds
                ),
                "evidence_text": item.get("evidence_text", ""),
                "confidence": float(item.get("confidence", 0)),
                "needs_verification": bool(item.get("needs_verification", False)),
            }
        )
    return normalized


def empty_result(title, source_url):
    return {
        "title": title,
        "source_url": source_url,
        "summary": "",
        "chapters": [],
        "knowledge_items": [],
        "action_items": [],
        "low_confidence_notes": ["No transcript text was provided."],
    }


def extract_action_items(segments):
    actions = []
    for segment in segments:
        text = segment.text.strip()
        lowered = text.lower()
        if lowered.startswith("finally "):
            action = text[len("finally ") :]
            actions.append(capitalize(action))
        elif "should " in lowered:
            actions.append(capitalize(text))
    return actions[:5]


def infer_tags(text):
    lowered = text.lower()
    tags = []
    if "concept" in lowered:
        tags.append("concept")
    if "evidence" in lowered or "source" in lowered:
        tags.append("evidence")
    if "review" in lowered:
        tags.append("review")
    return tags or ["video-note"]


def needs_verification(text):
    lowered = text.lower()
    return any(word in lowered for word in ["uncertain", "maybe", "claim"])


def short_title(text):
    words = re.findall(r"[\w'-]+", text)
    if not words:
        return "Knowledge point"
    return " ".join(words[:6]).rstrip(".")


def capitalize(text):
    if not text:
        return text
    return text[0].upper() + text[1:]


def clamp(value, duration_seconds):
    if duration_seconds <= 0:
        return max(0, value)
    return max(0, min(value, duration_seconds))
