import json
import time
import re
import urllib.error
import urllib.request


DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"


class ArkVideoKnowledgeClient:
    def __init__(
        self,
        api_key,
        model,
        fps=5,
        reasoning_effort="high",
        base_url=DEFAULT_BASE_URL,
        opener=None,
        retry_sleep=None,
    ):
        if not api_key:
            raise ValueError("Ark API key is required.")
        if not model:
            raise ValueError("Ark model or endpoint id is required.")
        self.api_key = api_key
        self.model = model
        self.fps = fps
        self.reasoning_effort = reasoning_effort
        self.base_url = base_url.rstrip("/")
        self.opener = opener or urllib.request.urlopen
        self.retry_sleep = retry_sleep or time.sleep

    def build_payload(self, video_url, prompt=None):
        return {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt or knowledge_prompt()},
                        {
                            "type": "video_url",
                            "video_url": {"url": video_url, "fps": self.fps},
                        },
                    ],
                }
            ],
            "reasoning": {"effort": self.reasoning_effort},
        }

    def extract(self, video_url, prompt=None, timeout=180, max_attempts=3):
        payload = self.build_payload(video_url, prompt=prompt)
        request = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": "Bearer {0}".format(self.api_key),
                "Content-Type": "application/json",
            },
        )
        for attempt in range(1, max_attempts + 1):
            try:
                with self.opener(request, timeout=timeout) as response:
                    result = json.loads(response.read().decode("utf-8", "replace"))
                break
            except (ConnectionError, TimeoutError, urllib.error.URLError):
                if attempt == max_attempts:
                    raise
                self.retry_sleep(min(attempt * 2, 10))
        return parse_chat_completion_content(result)


def parse_chat_completion_content(response):
    choices = response.get("choices") or []
    if not choices:
        raise RuntimeError("Ark response did not include choices.")
    message = choices[0].get("message") or {}
    content = message.get("content") or ""
    if isinstance(content, list):
        content = "".join(
            item.get("text", "") for item in content if isinstance(item, dict)
        )
    return strip_markdown_fence(content)


def strip_markdown_fence(text):
    stripped = text.strip()
    if stripped.startswith("```"):
        match = re.search(r"```(?:markdown|md)?\s*(.*?)```", stripped, flags=re.DOTALL)
        if match:
            return match.group(1).strip()
    return stripped


def knowledge_prompt():
    return (
        "你是教学知识蒸馏器。只提取视频中可迁移、可复用的教学知识，"
        "输出一段可直接粘贴进其他 LLM 上下文的 Markdown。"
        "不要输出泛泛总结，不要评价视频，不要写来源位置，不要编造视频中没有教的内容。"
        "只保留必要信息，语言要压缩、清楚、可执行。\n\n"
        "# 教学知识包\n\n"
        "## 教学目标\n"
        "用 1-2 句话说明学完后能做什么。\n\n"
        "## 适用场景\n"
        "说明这套方法适合解决什么任务，必要时写不适合的边界。\n\n"
        "## 核心方法\n"
        "不要只写概念性步骤。按复现顺序列出 3-8 个操作卡，"
        "每个操作卡必须包含：为什么做、输入材料、具体操作、"
        "参数或提示词片段、产出长什么样、失败时怎么调。"
        "如果视频展示了前后对比、界面设置、镜头运动、素材组织、"
        "提示词结构或工作流顺序，必须把这些细节写进对应操作卡。"
        "每个步骤要让没看过视频的人也能照着做。\n\n"
        "## 可复用模板\n"
        "提炼视频里的 prompt、参数、镜头语言、工作流或操作模式。"
        "模板要能被另一个 LLM 直接复用。\n\n"
        "## 关键判断\n"
        "写做对/做错的判断标准，以及什么时候需要调整。\n\n"
        "## 注意事项\n"
        "只写会影响复现效果的坑、限制和安全边界。"
    )
