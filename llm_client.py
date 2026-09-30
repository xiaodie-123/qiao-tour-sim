"""DeepSeek 调用封装:一次调用、超时、用量记录;绝不打印密钥。"""
import json
import os

from dotenv import load_dotenv
from openai import OpenAI


def call_deepseek(prompt, max_tokens=1200, timeout=30.0):
    load_dotenv()
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key or key == "replace_with_your_key":
        raise RuntimeError("缺少 DEEPSEEK_API_KEY:请在本地 .env 中配置")
    client = OpenAI(
        api_key=key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        timeout=timeout,
        max_retries=0,
    )
    resp = client.chat.completions.create(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-flash"),
        messages=[
            {"role": "system", "content": "只输出 JSON 对象,不要输出其他内容。"},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        extra_body={"thinking": {"type": "disabled"}},
        max_tokens=max_tokens,
    )
    choice = resp.choices[0]
    if choice.finish_reason == "length":
        raise RuntimeError("输出被截断(检查 max_tokens)")
    if not choice.message.content:
        raise RuntimeError("API 返回空内容")
    data = json.loads(choice.message.content)
    usage = None
    try:
        u = resp.usage
        usage = {"prompt_tokens": u.prompt_tokens,
                 "completion_tokens": u.completion_tokens,
                 "total_tokens": u.total_tokens}
    except Exception:
        usage = None
    meta = {"request_model": os.getenv("DEEPSEEK_MODEL", "deepseek-flash"),
            "response_model": resp.model, "usage": usage}
    return data, meta
