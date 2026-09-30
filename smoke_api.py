import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
key = os.getenv("DEEPSEEK_API_KEY")
if not key or key == "replace_with_your_key":
    raise SystemExit("请先在本地.env配置DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=key,
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    timeout=30.0,
    max_retries=0,
)
response = client.chat.completions.create(
    model=os.getenv("DEEPSEEK_MODEL", "deepseek-flash"),
    messages=[
        {"role": "system", "content": '只输出JSON对象，格式示例：{"status":"ok"}。'},
        {"role": "user", "content": '返回JSON对象{"status":"ok"}。'},
    ],
    response_format={"type": "json_object"},
    extra_body={"thinking": {"type": "disabled"}},
    max_tokens=128,
)
text = response.choices[0].message.content
if response.choices[0].finish_reason == "length":
    raise RuntimeError("响应被截断，请检查max_tokens")
if not text:
    raise RuntimeError("API返回空内容")
data = json.loads(text)
if data.get("status") != "ok":
    raise RuntimeError("返回结构不符合约定")
print(json.dumps(data, ensure_ascii=False))
print("response_model:", response.model)
print("usage:", response.usage)
