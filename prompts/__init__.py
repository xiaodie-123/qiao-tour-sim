"""提示词模板加载。"""
from pathlib import Path


def build_prompt(nodes, profiles, profile_id, weather):
    template = (Path(__file__).parent / "visitor_policy.txt").read_text(encoding="utf-8")
    prof = next(p for p in profiles if p["profile_id"] == profile_id)
    lines = []
    for n in nodes:
        if n["kind"] in ("attraction", "service"):
            lines.append("%s %s 遮蔽:%s 容量:%s 基础停留:%s分钟"
                         % (n["node_id"], n["name"], n["sheltered"], n["capacity"], n["dwell_min"]))
    return (template
            .replace("%%PROFILE_NAME%%", prof["name"])
            .replace("%%PROFILE_DESC%%", prof["description"])
            .replace("%%PROFILE_ID%%", profile_id)
            .replace("%%WEATHER%%", weather)
            .replace("%%WEATHER_DESC%%", "下雨" if weather == "rain" else "晴天")
            .replace("%%NODES_BLOCK%%", "\n".join(lines)))
