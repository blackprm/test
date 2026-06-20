# Video Knowledge and Douyin Subscription Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an MVP that can understand a single video, extract structured knowledge with timestamped evidence, subscribe to a Douyin creator homepage, discover new videos, and route each new video through the same understanding pipeline.

**Architecture:** Keep platform acquisition, media processing, model inference, knowledge extraction, storage, and notification decoupled. The subscription crawler only discovers and enqueues videos; workers perform media preparation and video understanding; the knowledge store keeps structured notes and source evidence.

**Compliance posture:** Use official or authorized access paths where available, respect platform terms and rate limits, do not bypass access controls, do not redistribute original videos, and keep deletion/export controls in the product.

---

## Project Shape

Suggested service layout:

```text
src/
  connectors/
    douyinConnector.ts
  media/
    mediaPipeline.ts
    transcriptService.ts
    keyframeService.ts
  models/
    videoUnderstandingClient.ts
  subscriptions/
    subscriptionService.ts
    subscriptionScheduler.ts
  knowledge/
    knowledgeExtractor.ts
    knowledgeStore.ts
    searchIndexer.ts
  queues/
    jobs.ts
    worker.ts
  notifications/
    notificationService.ts
  compliance/
    policy.ts
    auditLog.ts
```

Suggested database tables:

```text
subscriptions
videos
video_assets
video_chapters
knowledge_items
processing_jobs
audit_events
```

## Task 1: Define Storage and State Machine

**Files:**
- Create or modify migration files for `subscriptions`, `videos`, `video_assets`, `video_chapters`, `knowledge_items`, `processing_jobs`, and `audit_events`.
- Create repository/store modules under `src/knowledge` and `src/subscriptions`.

- [ ] **Step 1: Add subscription table**

Fields:

- `id`
- `user_id`
- `platform`
- `creator_id`
- `creator_url`
- `creator_name`
- `status`
- `poll_interval_minutes`
- `last_checked_at`
- `last_success_at`
- `cursor`
- `failure_count`
- `created_at`
- `updated_at`

Expected: one user can subscribe to one or more Douyin creator homepages.

- [ ] **Step 2: Add video table**

Fields:

- `id`
- `platform`
- `platform_video_id`
- `subscription_id`
- `creator_id`
- `title`
- `description`
- `source_url`
- `published_at`
- `duration_seconds`
- `processing_status`
- `created_at`
- `updated_at`

Expected: unique index on `(platform, platform_video_id)` prevents duplicate model runs.

- [ ] **Step 3: Add knowledge tables**

Create chapter and knowledge-item records with start/end timestamps, content, tags, confidence, evidence text, and `needs_verification`.

Expected: every important knowledge item can link back to one video and one timestamp range.

## Task 2: Implement Single Video Understanding Pipeline

**Files:**
- Create: `src/media/mediaPipeline.ts`
- Create: `src/media/transcriptService.ts`
- Create: `src/media/keyframeService.ts`
- Create: `src/models/videoUnderstandingClient.ts`
- Create: `src/knowledge/knowledgeExtractor.ts`

- [ ] **Step 1: Normalize video input**

Accept local upload, object-storage URL, or connector-produced media asset. Store canonical metadata and an internal asset ID.

Expected: downstream workers do not need to know whether the video came from upload or Douyin discovery.

- [ ] **Step 2: Extract transcript and visual signals**

Produce:

- transcript segments with timestamps;
- sampled keyframes;
- scene boundaries when available;
- duration and basic media metadata.

Expected: the model receives both audio/text and visual context.

- [ ] **Step 3: Call video understanding model**

Prompt the model to return JSON containing:

- overall summary;
- chapters;
- key concepts;
- claims and supporting timestamps;
- action items;
- unclear or low-confidence segments;
- content-type labels such as tutorial, commentary, review, news, interview, or vlog.

Expected: model output is structured enough to validate and store.

- [ ] **Step 4: Validate and normalize output**

Reject or repair malformed JSON, clamp timestamps to video duration, require evidence for important claims, and mark unsupported inferences as `needs_verification`.

Expected: knowledge store never receives free-floating claims without source references.

## Task 3: Implement Douyin Subscription Discovery

**Files:**
- Create: `src/connectors/douyinConnector.ts`
- Create: `src/subscriptions/subscriptionService.ts`
- Create: `src/subscriptions/subscriptionScheduler.ts`
- Create: `src/compliance/policy.ts`
- Create: `src/compliance/auditLog.ts`

- [ ] **Step 1: Create subscription API**

Allow a user to add, pause, resume, and delete a Douyin creator subscription.

Expected: deleting a subscription stops future discovery and can optionally delete stored derived knowledge.

- [ ] **Step 2: Discover creator videos**

Implement connector methods:

- `resolveCreator(urlOrId)`;
- `listRecentVideos(creatorId, cursor)`;
- `getVideoMetadata(videoId)`;
- `getAuthorizedMedia(videoId)` when allowed.

Expected: discovery uses allowed access paths and records audit events for every platform call.

- [ ] **Step 3: Add conservative scheduling**

Run subscription checks based on `poll_interval_minutes`, exponential backoff on failures, and platform-specific rate limits.

Expected: the scheduler does not hammer creator pages and can recover from temporary failures.

- [ ] **Step 4: Enqueue new videos**

For every newly discovered video, create or update the `videos` row and enqueue `fetch_media` or `understand_video` only when it has not already been processed.

Expected: refreshing a subscription is idempotent.

## Task 4: Implement Worker Queue

**Files:**
- Create: `src/queues/jobs.ts`
- Create: `src/queues/worker.ts`
- Modify services from Tasks 2 and 3 to enqueue jobs.

- [ ] **Step 1: Define job types**

Use explicit job names:

- `discover_creator_videos`
- `fetch_media`
- `prepare_media`
- `understand_video`
- `index_knowledge`
- `notify_user`

Expected: every job has retry metadata, status, failure reason, and idempotency key.

- [ ] **Step 2: Chain jobs safely**

Each worker should update status before and after execution. Failed jobs should not corrupt previous successful output.

Expected: operators can inspect where a video got stuck.

## Task 5: Build Review and Search UI

**Files:**
- Add frontend/API routes appropriate to the host application.

- [ ] **Step 1: Add subscription management page**

Show creator, status, last check time, failure count, and latest processed videos.

Expected: users can understand whether a subscription is healthy.

- [ ] **Step 2: Add video knowledge page**

Show:

- summary;
- chapter outline;
- knowledge items;
- action list;
- low-confidence warnings;
- source timestamps.

Expected: users can click a knowledge item and jump back to the original video timestamp or internal player timestamp when legally available.

- [ ] **Step 3: Add knowledge search**

Search by creator, topic, keyword, and processing date. Rank results by relevance, recency, and confidence.

Expected: knowledge extracted from videos is reusable outside the original video page.

## Task 6: Testing and Acceptance

- [ ] **Unit tests**

Cover:

- subscription deduplication;
- cursor updates;
- rate-limit decisions;
- model-output validation;
- timestamp clamping;
- knowledge-item persistence.

- [ ] **Integration tests**

Use mocked Douyin connector responses and sample videos.

Expected cases:

- first subscription scan finds multiple videos;
- second scan finds no duplicates;
- one new video appears and only that video is processed;
- model output with unsupported claims is marked for verification;
- paused subscription is not polled.

- [ ] **Manual acceptance**

Run an end-to-end test:

1. Add one authorized Douyin creator homepage.
2. Trigger discovery.
3. Confirm new videos are enqueued once.
4. Confirm one video generates summary, chapters, knowledge points, and action items.
5. Confirm each knowledge point includes a source timestamp.
6. Confirm deleting the subscription stops future polling.

## Rollout Milestones

### Milestone 1: Manual video understanding

- Upload or reference one video.
- Generate transcript, keyframes, summary, chapters, and knowledge points.
- Store timestamped evidence.

### Milestone 2: Single creator subscription

- Add one Douyin creator.
- Discover recent videos.
- Deduplicate and enqueue new videos.

### Milestone 3: Knowledge review and search

- Browse extracted notes by creator and video.
- Search across knowledge items.
- Jump from note to timestamp evidence.

### Milestone 4: Production hardening

- Add rate limits, audit logs, retries, deletion workflows, and monitoring dashboards.
