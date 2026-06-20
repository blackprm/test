# Ark Prompt

The bundled prompt asks Ark VLM to output Markdown, not JSON.

Required model settings:

- `model`: user-supplied Ark endpoint, e.g. `ep-20260513103751-6d9f9`
- `fps`: `5` by default
- `reasoning.effort`: `high`

Prompt intent:

- Extract transferable teaching knowledge.
- Ignore generic video commentary.
- Avoid timestamps and source-location evidence in the final context pack.
- Make `核心方法` detailed enough for downstream LLM use.

The `核心方法` section must force operation cards. Each card should contain:

- why this step exists;
- required input materials;
- exact operation;
- parameters or prompt fragments;
- what the output should look like;
- how to adjust if it fails.

Do not add `response_format=json_object`.
