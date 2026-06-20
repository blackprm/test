# Failure Recovery

Douyin play URLs are temporary and CDN routing can differ by caller.

Use this order:

1. Refresh the play URL from `aweme/detail`.
2. Verify it resolves to `200 video/mp4`.
3. Call Ark immediately.
4. If Ark fails with `403`, `RemoteDisconnected`, or timeout, refresh the URL and retry.
5. If repeated public URL attempts fail, download the MP4 locally.
6. Compress the local video to a smaller derivative if needed:

```bash
ffmpeg -y -i input.mp4 -vf 'scale=360:-2,fps=1' -an \
  -c:v libx264 -preset veryfast -crf 32 -movflags +faststart low.mp4
```

7. Use the compressed file as a fallback transport if the model endpoint supports local upload or data URLs.

Record fallback use in the summary so future users know the result did not come from a direct public URL pull.
