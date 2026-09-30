"""游客偏好策略:LLM 优先、规则兜底;读取与校验。"""
import hashlib
import json
import time

RANGES = {"attraction_weights": (0.0, 1.0), "crowd_aversion": (0.0, 2.0),
          "shelter_bonus": (0.0, 2.0), "dwell_multiplier": (0.5, 1.5)}


def _attraction_ids(nodes):
    return [n["node_id"] for n in nodes if n["kind"] in ("attraction", "service")]


def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def rule_policies(nodes, profiles):
    """透明默认规则(未调用 LLM 时的兜底,演示假设)。"""
    ids = _attraction_ids(nodes)
    profile_meta = {p["profile_id"]: p for p in profiles}
    keyword_bias = {
        "family": {"花园": 0.3, "民俗": 0.2, "戏台": 0.15, "茶": 0.1},
        "senior": {"花园": 0.25, "砖雕": 0.15, "茶": 0.15, "影壁": 0.1, "祠堂": 0.1},
        "individual": {"堂": 0.15, "馆": 0.15, "珍宝": 0.15, "票号": 0.1, "灯": 0.1, "镜": 0.1, "书房": 0.1},
    }
    base = {
        "family": {"crowd_aversion": 1.2, "shelter_bonus": 1.0, "dwell_multiplier": 0.8},
        "senior": {"crowd_aversion": 1.4, "shelter_bonus": 1.2, "dwell_multiplier": 1.1},
        "individual": {"crowd_aversion": 0.8, "shelter_bonus": 0.5, "dwell_multiplier": 1.0},
    }
    groups = {}
    for pid in profile_meta:
        for w in ("clear", "rain"):
            weights = {}
            for n in nodes:
                if n["node_id"] not in ids:
                    continue
                w0 = 0.6
                for kw, bias in keyword_bias[pid].items():
                    if kw in n["name"]:
                        w0 += bias
                if w == "rain":
                    if "花园" in n["name"] or "戏台" in n["name"]:
                        w0 -= 0.15  # 露天节点雨天吸引力下降
                    if n["sheltered"]:
                        w0 += 0.05
                weights[n["node_id"]] = round(min(1.0, max(0.2, w0)), 2)
            shelter = base[pid]["shelter_bonus"] * (1.3 if w == "rain" else 1.0)
            groups[pid + "|" + w] = {
                "profile_id": pid,
                "weather": w,
                "attraction_weights": weights,
                "crowd_aversion": round(base[pid]["crowd_aversion"] * (1.1 if w == "rain" else 1.0), 2),
                "shelter_bonus": round(min(2.0, shelter), 2),
                "dwell_multiplier": round(base[pid]["dwell_multiplier"] * (0.9 if w == "rain" else 1.0), 2),
                "summary": "%s%s策略(规则兜底默认值,演示假设,未调用LLM)"
                           % (profile_meta[pid]["name"], "雨天" if w == "rain" else "晴天"),
                "source": "rule_fallback",
                "model": "rule_fallback(未调用LLM)",
                "prompt_version": "v1-rule",
                "generated_at": _now(),
            }
    return groups


def _validate_group(profile_id, weather, data, nodes):
    if not isinstance(data, dict):
        raise ValueError("输出不是 JSON 对象")
    ids = _attraction_ids(nodes)
    weights = data.get("attraction_weights")
    if not isinstance(weights, dict):
        raise ValueError("attraction_weights 缺失或不是对象")
    if set(weights.keys()) != set(ids):
        raise ValueError("attraction_weights 未覆盖全部非出入口节点")
    for k, v in weights.items():
        if not isinstance(v, (int, float)) or not (0.0 <= float(v) <= 1.0):
            raise ValueError("attraction_weights 数值越界: %s" % k)
    out = {"profile_id": profile_id, "weather": weather,
           "attraction_weights": {k: float(v) for k, v in weights.items()}}
    for f in ("crowd_aversion", "shelter_bonus"):
        v = data.get(f)
        if not isinstance(v, (int, float)) or not (0.0 <= float(v) <= 2.0):
            raise ValueError("%s 越界" % f)
        out[f] = float(v)
    v = data.get("dwell_multiplier")
    if not isinstance(v, (int, float)) or not (0.5 <= float(v) <= 1.5):
        raise ValueError("dwell_multiplier 越界")
    out["dwell_multiplier"] = float(v)
    out["summary"] = str(data.get("summary", ""))[:200]
    return out


def build_policies(nodes, profiles):
    """尝试 LLM 生成 6 组策略;每组失败(无密钥/超时/格式错)就用规则兜底并如实标注。"""
    groups = rule_policies(nodes, profiles)
    try:
        from llm_client import call_deepseek
        from prompts import build_prompt
    except Exception:
        return groups
    for pid in {p["profile_id"] for p in profiles}:
        for w in ("clear", "rain"):
            ok = False
            for _attempt in range(2):  # 每组最多一次重试,共 12 次请求上限
                try:
                    prompt = build_prompt(nodes, profiles, pid, w)
                    data, meta = call_deepseek(prompt)
                    g = _validate_group(pid, w, data, nodes)
                    g.update({"source": "llm",
                              "model": meta.get("response_model", "unknown"),
                              "prompt_version": "v1",
                              "generated_at": _now(),
                              "usage": meta.get("usage")})
                    groups[pid + "|" + w] = g
                    ok = True
                    break
                except Exception:
                    continue
            if not ok:
                groups[pid + "|" + w]["source"] = "rule_fallback"
    return groups


def _validate_group_fields(g):
    for f in ("profile_id", "weather", "attraction_weights", "summary"):
        if f not in g:
            raise ValueError("策略组缺字段: %s" % f)
    for k, v in g["attraction_weights"].items():
        if not (0.0 <= float(v) <= 1.0):
            raise ValueError("attraction_weights 越界: %s" % k)
    for f, (lo, hi) in RANGES.items():
        if f == "attraction_weights":
            continue
        if f in g and not (lo <= float(g[f]) <= hi):
            raise ValueError("字段越界: %s=%s" % (f, g[f]))
    return g


def load_policies(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    groups = data["groups"] if isinstance(data, dict) and "groups" in data else data
    for k, g in groups.items():
        _validate_group_fields(g)
    return {"groups": groups, "meta": data.get("meta", {})}


def policy_hash(groups):
    core = {}
    for k, g in sorted(groups.items()):
        core[k] = {f: g.get(f) for f in
                   ("profile_id", "weather", "attraction_weights",
                    "crowd_aversion", "shelter_bonus", "dwell_multiplier")}
    payload = json.dumps(core, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
