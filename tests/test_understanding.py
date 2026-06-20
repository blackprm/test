from video_knowledge.understanding import TranscriptSegment, understand_transcript


def test_understand_transcript_returns_timestamped_knowledge():
    segments = [
        TranscriptSegment(0, 8, "First capture the useful source material."),
        TranscriptSegment(8, 18, "Then extract concepts and keep timestamp evidence."),
        TranscriptSegment(18, 30, "Finally review uncertain claims before using them."),
    ]

    result = understand_transcript(
        title="Video knowledge workflow",
        source_url="https://www.douyin.com/video/7648701859682667811",
        duration_seconds=30,
        transcript=segments,
    )

    assert result["summary"] == (
        "First capture the useful source material. Then extract concepts and keep "
        "timestamp evidence. Finally review uncertain claims before using them."
    )
    assert result["chapters"][0]["start_time_seconds"] == 0
    assert result["chapters"][0]["end_time_seconds"] == 30
    assert result["knowledge_items"][0]["evidence_text"] == segments[0].text
    assert result["knowledge_items"][0]["confidence"] >= 0.5
    assert result["action_items"] == ["Review uncertain claims before using them."]


def test_understand_transcript_clamps_timestamps_to_duration():
    result = understand_transcript(
        title="Short video",
        source_url="https://www.douyin.com/video/7000000000000000000",
        duration_seconds=10,
        transcript=[TranscriptSegment(4, 99, "Use a bounded timestamp range.")],
    )

    assert result["chapters"][0]["end_time_seconds"] == 10
    assert result["knowledge_items"][0]["end_time_seconds"] == 10
