---
name: douyin-video-knowledge-distiller
description: Use when a user wants to extract public Douyin creator videos, refresh playable MP4 URLs, and distill video teaching knowledge into Markdown context packs for downstream LLMs.
---

# Douyin Video Knowledge Distiller

## Overview

Use this skill to turn a public Douyin creator homepage into reusable teaching knowledge packs. The output is Markdown meant to be pasted into another LLM context, not a video summary database.

## Core Workflow

1. Extract the creator `sec_user_id` from the Douyin profile URL.
2. Page through public `aweme/post` results to collect video metadata.
3. For each `aweme_id`, refresh a fresh `aweme/detail` play URL immediately before model use.
4. Verify the play URL resolves to `200 video/mp4`.
5. Send the fresh public URL to Ark VLM with `fps=5` and `reasoning.effort=high`.
6. Save one Markdown context pack per video under `context_packs/<aweme_id>.md`.
7. Retry by refreshing the play URL; if Ark still fails, use the fallback flow in `references/failure-recovery.md`.

Never treat `play_url` as a long-lived asset. Store `aweme_id`, `creator_id`, title, description, duration, and source URL; refresh media URLs only at processing time.

## Quick Start

Set the Ark key outside the zip:

```bash
export ARK_API_KEY="..."
```

Run a dry run:

```bash
python scripts/distill_profile.py --db data/knowledge.sqlite distill-profile \
  "https://www.douyin.com/user/SEC_USER_ID?from_tab_name=main" \
  --model ep-20260513103751-6d9f9 \
  --fps 5 \
  --reasoning-effort high \
  --dry-run
```

Run distillation:

```bash
python scripts/distill_profile.py --db data/knowledge.sqlite distill-profile \
  "https://www.douyin.com/user/SEC_USER_ID?from_tab_name=main" \
  --model ep-20260513103751-6d9f9 \
  --fps 5 \
  --reasoning-effort high \
  --out-dir data/context_packs
```

Run one video with a freshly refreshed URL:

```bash
python scripts/distill_profile.py --db data/knowledge.sqlite ark-understand AWEME_ID \
  --video-url "https://www.douyin.com/aweme/v1/play/?..." \
  --model ep-20260513103751-6d9f9 \
  --fps 5 \
  --reasoning-effort high \
  --output data/context_packs/AWEME_ID.md
```

## Output Contract

The model output is Markdown with only these sections:

```markdown
# 教学知识包

## 教学目标
## 适用场景
## 核心方法
## 可复用模板
## 关键判断
## 注意事项
```

`核心方法` must be operational enough for a person or LLM that never watched the video to reuse the teaching. Each operation card should include why to do it, input materials, exact actions, parameters or prompt fragments, expected output, and how to adjust when it fails.

Read `references/output-format.md` before changing the output shape. Read `references/ark-prompt.md` before changing the model prompt.

## Security

Do not hardcode Ark API keys into this skill or any zip. Keep secrets in environment variables or an untracked local `.env`. The included `.env.example` is a placeholder only.

## Common Mistakes

- Reusing an old `play_url`: refresh it from `aweme/detail` immediately before calling Ark.
- Saving MP4 URLs as durable assets: save `aweme_id` instead.
- Asking for JSON: this workflow needs compact Markdown context, not structured JSON.
- Leaving `核心方法` high level: force operation cards with enough detail to reproduce the teaching.
- Treating one Ark failure as final: retry with a fresh play URL, then use fallback.
