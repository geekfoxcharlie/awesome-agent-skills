#!/usr/bin/env python3
"""Generate README.md and README.zh.md from SkillPicker website.json."""

from __future__ import annotations

import argparse
import ctypes
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = (
    ROOT.parent / "SkillPicker" / "skillpicker-web" / "data" / "website.json"
)
SITE_DEFAULT = "https://skillpicker.xyz"

# Job first, then who does it, the software, the agent that runs the skill,
# the artifact, and getting started. Mirrors SkillPicker's homepage browse order.
AXIS_ORDER = ["task", "role", "tool", "agent", "deliverable", "beginner"]

COPY = {
    "en": {
        "title": "Awesome Agent Skills",
        "tagline": "**The right agent skill for the job.**",
        "lede": "A curated list of Agent Skills — SKILL.md packages for Claude Code, Codex, Cursor, and other coding agents — organized by role, task, and output.",
        "agents": "Claude Code · Codex · Cursor · Gemini CLI · Copilot · OpenCode",
        "browse": "**Browse the live directory → [{host}]({home})**",
        "lang_nav": "[English](README.md) · [简体中文](README.zh.md)",
        "start_here": "Start here",
        "start_intro": (
            "Ten agent skills worth installing this week. Not the ten highest install counts — "
            "the ones that pay off across jobs. Full lists live on [{host}]({home})."
        ),
        "contents": "Contents",
        "jobs_suffix": "jobs",
        "how_heading": "How this list is made",
        "axis": {
            "role": "By role",
            "deliverable": "By output",
            "task": "By task",
            "tool": "By tool",
            "agent": "By agent",
            "beginner": "Getting started",
        },
        "axis_intro": {
            "role": "Agent skills for a job title.",
            "deliverable": "Agent skills for a thing you need to ship.",
            "task": "Agent skills for a job to be done.",
            "tool": "Agent skills for a product you already use.",
            "agent": "Agent skills for a coding agent or CLI.",
            "beginner": "Agent skills for first-week setup and keeping context small.",
        },
        "topic_blurb": "Agent skills for {name}.",
        "also_covers": " Also covers {names}.",
        "also_join": ", ",
        "see_all": "**[See all on SkillPicker →]({url})**",
        "how_body": (
            "These are Agent Skills: folders with a `SKILL.md` that a coding agent loads for a specific job. "
            "Topics come from observed search demand. "
            "A skill appears here only when it matches that job directly. "
            "Ranking uses relevance first, then reported popularity — never safety, and never as an endorsement."
        ),
        "how_snapshot": (
            "This README is a curated snapshot ({date}). Duplicate job names are merged, "
            "clone-named skills are collapsed, and each skill appears in at most a few sections. "
            "The rest of the index — search, filters, evidence excerpts, and every ranked list — is on **[{host}]({home})**."
        ),
        "disclaimer": (
            "> Agent skills are reviewed for **relevance, not safety**. Read the upstream `SKILL.md` before you run one."
        ),
        "contributing": "Contributing",
        "contributing_body": (
            "The README is generated. Edit [`overlay/`](overlay/) or open an issue — see [CONTRIBUTING.md](CONTRIBUTING.md). "
            "Want the full index? **[{host}]({home})**."
        ),
        "footer": "Built from [SkillPicker]({home}). Skill names and trademarks belong to their owners.",
        "fallback_blurb": "See the SkillPicker page for what this skill covers.",
        "blurb_limit": 118,
    },
    "zh": {
        "title": "Awesome Agent Skills",
        "tagline": "**为这件事找到对的 Agent Skill。**",
        "lede": "一份 Agent Skill 精选清单——给 Claude Code、Codex、Cursor 等编程 Agent 用的 SKILL.md 技能包，按角色、任务和产出整理。",
        "agents": "Claude Code · Codex · Cursor · Gemini CLI · Copilot · OpenCode",
        "browse": "**浏览在线目录 → [{host}]({home})**",
        "lang_nav": "[English](README.md) · [简体中文](README.zh.md)",
        "start_here": "从这里开始",
        "start_intro": (
            "本周值得安装的十个 Agent Skill。不是安装量最高的十个，而是跨工作最能用上的。完整列表在 [{host}]({home})。"
        ),
        "contents": "目录",
        "jobs_suffix": "个工作",
        "how_heading": "这份列表怎么来的",
        "axis": {
            "role": "按角色",
            "deliverable": "按产出",
            "task": "按任务",
            "tool": "按工具",
            "agent": "按 Agent",
            "beginner": "入门",
        },
        "axis_intro": {
            "role": "面向职位的 Agent Skills。",
            "deliverable": "面向你要交付的东西。",
            "task": "面向一件要完成的工作。",
            "tool": "面向你已经在用的产品。",
            "agent": "面向某个编程 Agent 或 CLI。",
            "beginner": "面向第一周上手，以及把上下文保持得小。",
        },
        "topic_blurb": "面向「{name}」的 Agent Skills。",
        "also_covers": "同时覆盖{names}。",
        "also_join": "、",
        "see_all": "**[在 SkillPicker 查看全部 →]({url})**",
        "how_body": (
            "这里列出的是 Agent Skills：带 `SKILL.md` 的文件夹，编程 Agent 会为某项工作加载它们。"
            "主题来自观察到的搜索需求。"
            "Skill 只有在与该工作直接匹配时才会出现在这里。"
            "排序先看相关性，再看报告的流行度——不代表安全性审查，也不代表推荐。"
        ),
        "how_snapshot": (
            "本 README 是一份精选快照（{date}）。重复的工作名称已合并，近名 Skill 已折叠，每个 Skill 最多只出现在少数几个章节。"
            "其余索引——搜索、筛选、证据摘录和完整排序列表——在 **[{host}]({home})**。"
        ),
        "disclaimer": (
            "> Agent Skill 只审核**相关性，不审核安全性**。运行前请阅读上游 `SKILL.md`。"
        ),
        "contributing": "贡献",
        "contributing_body": (
            "README 由脚本生成。请改 [`overlay/`](overlay/) 或开 issue——见 [CONTRIBUTING.md](CONTRIBUTING.md)。"
            "需要完整索引？**[{host}]({home})**。"
        ),
        "footer": "基于 [SkillPicker]({home}) 构建。Skill 名称和商标归其所有者所有。",
        "fallback_blurb": "该 Skill 的覆盖范围见 SkillPicker 页面。",
        "blurb_limit": 80,
    },
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def slugify(value: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", value.lower())
    s = s.strip("-")[:56]
    return s or "skill"


def _imul32(a: int, b: int) -> int:
    return ctypes.c_int32(int(a) * int(b)).value


def stable_hash(value: str) -> str:
    h = 2166136261
    for ch in value:
        h = _imul32(h ^ ord(ch), 16777619)
    n = h & 0xFFFFFFFF
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    if n == 0:
        return "0"
    out = []
    while n:
        n, r = divmod(n, 36)
        out.append(digits[r])
    return "".join(reversed(out))


def locale_prefix(locale: str) -> str:
    return "" if locale == "en" else f"/{locale}"


def skill_path(name: str, candidate_id: str, locale: str = "en") -> str:
    return f"{locale_prefix(locale)}/skill/{slugify(name)}-{stable_hash(candidate_id)}/"


def topic_path(axis: str, slug: str, locale: str = "en") -> str:
    return f"{locale_prefix(locale)}/for/{axis}/{slug}/"


def home_url(site: str, locale: str) -> str:
    base = site.rstrip("/")
    return base if locale == "en" else f"{base}{locale_prefix(locale)}/"


def gh_anchor(heading: str) -> str:
    keep = []
    for ch in heading.lower():
        if ch.isalnum() or ch.isspace() or ch == "-":
            keep.append(ch)
    out = "".join(keep).strip()
    while "  " in out:
        out = out.replace("  ", " ")
    return out.replace(" ", "-")


CJK_RE = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")
TRIGGER_RE = re.compile(
    r"^(when the user|use when |use this skill|this skill should be used|"
    r"the user (needs|requests|asks|wants)|helps users |transform claude)",
    re.I,
)
GENERIC_NAME_TOKENS = {
    "a",
    "an",
    "and",
    "assistant",
    "builder",
    "creator",
    "expert",
    "for",
    "generator",
    "guru",
    "helper",
    "optimizer",
    "skill",
    "skills",
    "the",
    "workflow",
    "workflows",
}


def is_non_english(text: str) -> bool:
    cjk = len(CJK_RE.findall(text or ""))
    latin = len(re.findall(r"[A-Za-z]", text or ""))
    return cjk >= 6 and cjk >= latin * 0.25


def is_locale_locked(name: str, text: str) -> bool:
    n = (name or "").lower()
    blob = f"{name} {text}".lower()
    if re.search(r"(^|[-_])(zh|cn)$", n) or "chinese-novel" in n:
        return True
    if re.search(
        r"vietnamese|vi-vn|简体|中文|chinese-legal|chinese-content|"
        r"[-_]zh\b|\bzh[-_]|"
        r"korean-law|\bkorean\b|hangul|한국어",
        blob,
    ):
        return True
    return is_non_english(name) or is_non_english(text)


def looks_like_trigger(text: str) -> bool:
    return bool(TRIGGER_RE.search((text or "").strip()))


def one_line(text: str, limit: int = 118) -> str:
    raw = (text or "").strip()
    raw = re.sub(r"^>+\s*", "", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    raw = re.sub(
        r"^Use this skill(?: any time| whenever| when)?\s+",
        "",
        raw,
        flags=re.I,
    )
    raw = re.sub(r"^When the user wants to\s+", "", raw, flags=re.I)
    raw = re.sub(r"^Helps users\s+", "", raw, flags=re.I)
    raw = re.sub(r"^The user (needs|wants|requests) to\s+", "", raw, flags=re.I)
    if raw and raw[0].isascii() and raw[0].isalpha():
        raw = raw[0].upper() + raw[1:]
    parts = re.split(r"(?<=[.!?。！？])\s+", raw, maxsplit=1)
    s = parts[0] if parts else raw
    s = s.strip(" -—")
    if len(s) > limit:
        cut = s[: limit - 1]
        if " " in cut and not CJK_RE.search(cut[-12:]):
            s = cut.rsplit(" ", 1)[0]
            s = re.sub(r"[,:;–—-]\s*(and|or|including|with|to|for)?$", "", s)
            s = s.rstrip(" ,;:") + "…"
        else:
            s = re.sub(r"[，,;:、。\s]+$", "", cut) + "…"
    return s


def localized_field(skill: dict, field: str, locale: str) -> str:
    if locale != "en":
        i18n = skill.get(f"{field}_i18n") or {}
        val = i18n.get(locale)
        if val:
            return val
    return skill.get(field) or ""


def display_name_for(entry: dict, locale: str) -> str:
    if locale != "en":
        loc = (entry.get("localized_display_names") or {}).get(locale)
        if loc:
            return loc
    return entry.get("display_name") or ""


def family_title(fam: dict | None, entry: dict, locale: str) -> str:
    if fam:
        if locale == "zh" and fam.get("title_zh"):
            return fam["title_zh"]
        if locale == "en" and fam.get("title"):
            return fam["title"]
        if fam.get("title") and locale == "en":
            return fam["title"]
    return display_name_for(entry, locale)


def norm_name(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip().lower())


def blurb_for(skill: dict, locale: str, fallback: str, limit: int) -> str:
    desc = localized_field(skill, "description", locale)
    reason = localized_field(skill, "reason", locale)
    en_desc = skill.get("description") or ""
    en_reason = skill.get("reason") or ""
    if locale == "en":
        if is_non_english(en_desc) and en_reason and not is_non_english(en_reason):
            return one_line(en_reason, limit)
        if looks_like_trigger(en_desc) and en_reason:
            return one_line(en_reason, limit)
        line = one_line(en_desc, limit)
        if len(line) < 24:
            line = one_line(en_reason or en_desc, limit)
        return line or fallback
    line = one_line(desc, limit)
    if len(line) < 12:
        line = one_line(reason or desc, limit)
    return line or fallback


def core_tokens(name: str) -> frozenset[str]:
    toks = re.findall(r"[a-z0-9]+", norm_name(name))
    return frozenset(t for t in toks if t not in GENERIC_NAME_TOKENS and len(t) > 1)


SYNONYM_GROUPS = (
    (frozenset({"cv", "resume", "curriculum"}), "cv"),
    (frozenset({"ppt", "pptx", "powerpoint", "presentation", "presentations"}), "ppt"),
    (frozenset({"copy", "copywriting", "copywrite"}), "copy"),
    (frozenset({"post", "posts"}), "post"),
    (frozenset({"writer", "writing", "write"}), "write"),
    (frozenset({"review", "reviewer"}), "review"),
    (frozenset({"story", "stories"}), "story"),
    (frozenset({"modeling", "modelling"}), "model"),
)


def canonical_core(name: str, *, collapse_cv: bool = False) -> frozenset[str]:
    core = set(core_tokens(name))
    if collapse_cv and core & {"cv", "resume", "curriculum"}:
        return frozenset({"cv"})
    for group, canon in SYNONYM_GROUPS:
        if core & group:
            core = (core - group) | {canon}
    return frozenset(core)


def topic_name_key(name: str) -> str:
    return norm_name(name).replace(" ", "-")


def is_name_clone(
    name: str,
    seen_cores: list[frozenset[str]],
    seen_names: list[str],
    *,
    collapse_cv: bool = False,
    topic_slug: str | None = None,
) -> bool:
    core = canonical_core(name, collapse_cv=collapse_cv)
    if not core:
        return False
    nkey = topic_name_key(name)
    exact = bool(topic_slug and nkey == topic_slug)
    for other, other_name in zip(seen_cores, seen_names):
        other_exact = bool(topic_slug and topic_name_key(other_name) == topic_slug)
        if exact or other_exact:
            if core == other:
                return True
            continue
        if core == other:
            return True
        if len(core) >= 2 and len(other) >= 2:
            if core <= other or other <= core:
                return True
            if len(core & other) / len(core | other) >= 0.6:
                return True
    return False


def install_cmd(source: str, name: str) -> str | None:
    if not source or "/" not in source:
        return None
    pkg = f"{source}@{name}"
    if re.search(r"\s", pkg):
        return f'`npx skills add "{pkg}"`'
    return f"`npx skills add {pkg}`"


def pick_key(skill: dict, *, canonical: str | None = None, topic_slug: str | None = None) -> tuple:
    # SkillPicker 1.9+ ranks by relevance first. Follow that order; installs
    # only break ties. Merged topics prefer the canonical demand's own ranks.
    rank = skill.get("rank") or 99
    installs = skill.get("installs") or 0
    from_canonical = 0 if (canonical and skill.get("demand_id") == canonical) else 1
    exact = 0 if topic_slug and topic_name_key(skill.get("name") or "") == topic_slug else 1
    return (from_canonical, exact, rank, -installs, skill.get("name") or "")


def unique_picks(
    skills: list[dict],
    *,
    limit: int,
    deny: set[str],
    used: dict[str, int],
    max_appearances: int,
    featured_rank_max: int,
    collapse_cv: bool = False,
    canonical: str | None = None,
    topic_slug: str | None = None,
) -> list[dict]:
    yes = []
    for s in skills:
        if s.get("match") != "yes":
            continue
        name = s.get("name") or ""
        if norm_name(name) in deny:
            continue
        desc = s.get("description") or ""
        reason = s.get("reason") or ""
        if not (desc or reason):
            continue
        if is_locale_locked(name, desc) and (not reason or is_locale_locked(name, reason)):
            continue
        yes.append(s)
    featured = [s for s in yes if (s.get("rank") or 99) <= featured_rank_max]
    pool = featured or yes

    def take(rows: list[dict], already: list[dict]) -> list[dict]:
        seen = {norm_name(s.get("name") or "") for s in already}
        seen_names = [s.get("name") or "" for s in already]
        cores = [
            canonical_core(s.get("name") or "", collapse_cv=collapse_cv)
            for s in already
        ]
        out: list[dict] = []
        ordered = sorted(
            rows, key=lambda s: pick_key(s, canonical=canonical, topic_slug=topic_slug)
        )
        for s in ordered:
            n = norm_name(s.get("name") or "")
            if not n or n in seen:
                continue
            if used.get(n, 0) >= max_appearances:
                continue
            if is_name_clone(
                s.get("name") or "",
                cores,
                seen_names,
                collapse_cv=collapse_cv,
                topic_slug=topic_slug,
            ):
                continue
            seen.add(n)
            seen_names.append(s.get("name") or "")
            cores.append(
                canonical_core(s.get("name") or "", collapse_cv=collapse_cv)
            )
            out.append(s)
            if len(already) + len(out) >= limit:
                break
        return out

    picked = take(pool, [])
    if len(picked) < limit:
        picked.extend(take(yes, picked))
    return picked[:limit]


def resolve_starter(skills: list[dict], starter_spec: list[dict], locale: str) -> list[dict]:
    by_id: dict[str, dict] = {}
    for s in skills:
        cid = s.get("candidate_id")
        if cid and cid not in by_id:
            by_id[cid] = s
        if s.get("match") == "yes" and cid:
            by_id[cid] = s
    out = []
    missing = []
    for item in starter_spec:
        cid = item["candidate_id"]
        row = by_id.get(cid)
        if not row:
            missing.append(cid)
            continue
        merged = dict(row)
        if locale == "zh" and item.get("blurb_zh"):
            merged["_blurb"] = item["blurb_zh"]
        elif item.get("blurb"):
            merged["_blurb"] = item["blurb"]
        out.append(merged)
    if missing:
        print("starter missing candidate_id:", *missing, sep="\n  ", file=sys.stderr)
    return out


def render_skill_bullet(
    skill: dict,
    site: str,
    locale: str,
    copy: dict,
    *,
    blurb: str | None = None,
) -> list[str]:
    name = skill["name"]
    url = site + skill_path(name, skill["candidate_id"], locale)
    text = blurb or skill.get("_blurb") or blurb_for(
        skill, locale, copy["fallback_blurb"], int(copy["blurb_limit"])
    )
    lines = [f"- **[{name}]({url})** — {text}"]
    cmd = install_cmd(skill.get("source") or "", name)
    if cmd:
        lines.append(f"  {cmd}")
    return lines


def snapshot_date(generated_at: str) -> str:
    if not generated_at:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        return generated_at[:10]
    except Exception:
        return generated_at


def fmt(template: str, **kwargs) -> str:
    return template.format(**kwargs)


def build(source: Path, overlay_dir: Path, locale: str = "en") -> tuple[str, dict]:
    if locale not in COPY:
        sys.exit(f"unsupported locale: {locale}")
    copy = COPY[locale]
    data = load_json(source)
    config = load_json(overlay_dir / "config.json")
    starter_spec = load_json(overlay_dir / "starter.json")["skills"]
    skip = set(load_json(overlay_dir / "skip.json"))
    pin = set(load_json(overlay_dir / "pin.json"))
    families = load_json(overlay_dir / "merges.json")["families"]
    deny_map = {
        k: {norm_name(n) for n in v}
        for k, v in load_json(overlay_dir / "deny.json").get("topic_names", {}).items()
    }

    site = config.get("site") or SITE_DEFAULT
    home = home_url(site, locale)
    host = home.replace("https://", "").rstrip("/")
    picks_n = int(config.get("picks_per_topic", 5))
    min_picks = int(config.get("min_picks", 3))
    max_appearances = int(config.get("max_appearances", 3))
    featured_rank_max = int(config.get("featured_rank_max", 8))
    max_per_axis = config.get("max_per_axis") or {}

    entries = data["demand_map"]["entries"]
    skills = data["skills"]
    generated_at = data.get("generated_at") or ""

    entry_by_id = {f"{e['axis']}/{e['slug']}": e for e in entries}
    skills_by_demand: dict[str, list] = defaultdict(list)
    for s in skills:
        skills_by_demand[s["demand_id"]].append(s)

    fold_of: dict[str, str] = {}
    family_by_canonical: dict[str, dict] = {}
    for fam in families:
        canonical = fam["canonical"]
        family_by_canonical[canonical] = fam
        for folded in fam.get("fold") or []:
            fold_of[folded] = canonical

    hidden = set(skip) | set(fold_of)

    used_names: dict[str, int] = defaultdict(int)

    def demand_ids_for(canonical: str) -> list[str]:
        ids = [canonical]
        fam = family_by_canonical.get(canonical)
        if fam:
            ids.extend(fam.get("fold") or [])
        return [i for i in ids if i not in skip]

    candidates = []
    for did, entry in entry_by_id.items():
        if did in hidden:
            continue
        if not entry.get("source_queries") and did not in family_by_canonical:
            continue
        candidates.append(entry)

    for fam in families:
        can = fam["canonical"]
        if can in skip:
            continue
        if can not in {f"{e['axis']}/{e['slug']}" for e in candidates}:
            if can in entry_by_id:
                candidates.append(entry_by_id[can])

    seen_ids = set()
    uniq = []
    for e in candidates:
        did = f"{e['axis']}/{e['slug']}"
        if did in seen_ids:
            continue
        seen_ids.add(did)
        uniq.append(e)
    candidates = uniq

    def topic_priority(entry: dict) -> int:
        did = f"{entry['axis']}/{entry['slug']}"
        fam = family_by_canonical.get(did)
        pri = entry.get("priority") or 0
        if not fam:
            return pri
        for folded in fam.get("fold") or []:
            other = entry_by_id.get(folded)
            if other:
                pri = max(pri, other.get("priority") or 0)
        return pri

    by_axis: dict[str, list] = defaultdict(list)
    for e in candidates:
        by_axis[e["axis"]].append(e)
    for ax in by_axis:
        items = by_axis[ax]
        items.sort(key=lambda e: (-topic_priority(e), e["display_name"].lower()))
        cap = max_per_axis.get(ax)
        if cap:
            cap_n = int(cap)
            pinned = [
                e for e in items if f"{e['axis']}/{e['slug']}" in pin
            ]
            rest = [
                e for e in items if f"{e['axis']}/{e['slug']}" not in pin
            ]
            kept = pinned + rest[: max(0, cap_n - len(pinned))]
            kept.sort(
                key=lambda e: (-topic_priority(e), e["display_name"].lower())
            )
            by_axis[ax] = kept
        else:
            by_axis[ax] = items

    starter = resolve_starter(skills, starter_spec, locale)

    topics_out = []
    for ax in AXIS_ORDER:
        for entry in by_axis.get(ax, []):
            did = f"{entry['axis']}/{entry['slug']}"
            pool = []
            for member in demand_ids_for(did):
                pool.extend(skills_by_demand.get(member, []))
            deny = set()
            for member in demand_ids_for(did):
                deny |= deny_map.get(member, set())
            collapse_cv = not did.startswith("deliverable/resume") and did not in {
                "deliverable/cv",
                "deliverable/cover-letter",
            }
            picks = unique_picks(
                pool,
                limit=picks_n,
                deny=deny,
                used=used_names,
                max_appearances=max_appearances,
                featured_rank_max=featured_rank_max,
                collapse_cv=collapse_cv,
                canonical=did,
                topic_slug=entry["slug"],
            )
            if len(picks) < min_picks:
                continue
            for s in picks:
                used_names[norm_name(s["name"])] += 1
            fam = family_by_canonical.get(did)
            title = family_title(fam, entry, locale)
            folded_names = []
            if fam:
                for folded in fam.get("fold") or []:
                    fe = entry_by_id.get(folded)
                    if fe and folded not in skip:
                        folded_names.append(display_name_for(fe, locale))
            topics_out.append(
                {
                    "axis": ax,
                    "id": did,
                    "title": title,
                    "entry": entry,
                    "picks": picks,
                    "folded_names": folded_names,
                    "yes_count": sum(1 for s in pool if s.get("match") == "yes"),
                }
            )

    date = snapshot_date(generated_at)
    topic_count = len(topics_out)
    skill_rows = sum(len(t["picks"]) for t in topics_out)
    L: list[str] = []
    ctx = {"host": host, "home": home, "date": date}

    L.append('<div align="center">')
    L.append("")
    L.append(f"# {copy['title']}")
    L.append("")
    L.append(copy["tagline"])
    L.append("")
    L.append(copy["lede"])
    L.append("")
    L.append(
        "[![Awesome](https://awesome.re/badge.svg)](https://awesome.re) "
        f"![Topics](https://img.shields.io/badge/topics-{topic_count}-0A66C2) "
        f"![Picks](https://img.shields.io/badge/curated_picks-{skill_rows}-0A66C2) "
        "[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)"
    )
    L.append("")
    L.append(copy["agents"])
    L.append("")
    L.append(fmt(copy["browse"], **ctx))
    L.append("")
    L.append(copy["lang_nav"])
    L.append("")
    L.append("</div>")
    L.append("")
    L.append("---")
    L.append("")
    L.append(f"## {copy['start_here']}")
    L.append("")
    L.append(fmt(copy["start_intro"], **ctx))
    L.append("")
    for s in starter:
        L.extend(render_skill_bullet(s, site, locale, copy, blurb=s.get("_blurb")))
        L.append("")
    L.append(f"## {copy['contents']}")
    L.append("")
    axis_counts = defaultdict(int)
    for t in topics_out:
        axis_counts[t["axis"]] += 1
    for ax in AXIS_ORDER:
        if axis_counts[ax]:
            heading = copy["axis"][ax]
            L.append(
                f"- [{heading}](#{gh_anchor(heading)}) — {axis_counts[ax]} {copy['jobs_suffix']}"
            )
    L.append(f"- [{copy['how_heading']}](#{gh_anchor(copy['how_heading'])})")
    L.append("")

    current_axis = None
    for t in topics_out:
        if t["axis"] != current_axis:
            current_axis = t["axis"]
            L.append(f"## {copy['axis'][current_axis]}")
            L.append("")
            L.append(copy["axis_intro"][current_axis])
            L.append("")
        entry = t["entry"]
        topic_url = site + topic_path(entry["axis"], entry["slug"], locale)
        display = t["title"]
        query_name = display_name_for(entry, locale)
        L.append(f"### {display}")
        L.append("")
        blurb = fmt(copy["topic_blurb"], name=query_name)
        if t["folded_names"]:
            also = copy["also_join"].join(t["folded_names"])
            blurb += fmt(copy["also_covers"], names=also)
        L.append(blurb)
        L.append("")
        L.append(fmt(copy["see_all"], url=topic_url))
        L.append("")
        for s in t["picks"]:
            L.extend(render_skill_bullet(s, site, locale, copy))
            L.append("")

    L.append(f"## {copy['how_heading']}")
    L.append("")
    L.append(copy["how_body"])
    L.append("")
    L.append(fmt(copy["how_snapshot"], **ctx))
    L.append("")
    L.append(copy["disclaimer"])
    L.append("")
    L.append(f"## {copy['contributing']}")
    L.append("")
    L.append(fmt(copy["contributing_body"], **ctx))
    L.append("")
    L.append("---")
    L.append("")
    L.append('<div align="center">')
    L.append("")
    L.append(fmt(copy["footer"], **ctx))
    L.append("")
    L.append("</div>")
    L.append("")

    stats = {
        "topics": topic_count,
        "picks": skill_rows,
        "starter": len(starter),
        "generated_at": generated_at,
        "axis": dict(axis_counts),
        "topic_ids": [t["id"] for t in topics_out],
        "names": [s["name"] for t in topics_out for s in t["picks"]],
        "locale": locale,
    }
    return "\n".join(L), stats


def self_check():
    got = skill_path(
        "frontend-design",
        "github:anthropics/skills/skills/frontend-design/SKILL.md",
    )
    expect = "/skill/frontend-design-bruzsa/"
    if got != expect:
        sys.exit(f"skill path hash mismatch: {got} != {expect}")
    got_zh = skill_path(
        "frontend-design",
        "github:anthropics/skills/skills/frontend-design/SKILL.md",
        "zh",
    )
    if got_zh != "/zh/skill/frontend-design-bruzsa/":
        sys.exit(f"zh skill path mismatch: {got_zh}")


def print_stats(label: str, stats: dict) -> None:
    print(f"built {label}")
    print(f"  topics:       {stats['topics']}")
    print(f"  curated rows: {stats['picks']}")
    print(f"  starter:      {stats['starter']}")
    print(f"  generated_at: {stats['generated_at']}")
    print("  by axis:", stats["axis"])
    print("  topics:", ", ".join(stats["topic_ids"]))


def main():
    self_check()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        default=DEFAULT_SOURCE,
        help="Path to SkillPicker website.json",
    )
    parser.add_argument(
        "--locale",
        choices=("en", "zh", "all"),
        default="all",
        help="Which README to write (default: both)",
    )
    args = parser.parse_args()
    source = args.source
    if not source.exists():
        sys.exit(f"source not found: {source}")
    overlay = ROOT / "overlay"
    locales = ["en", "zh"] if args.locale == "all" else [args.locale]
    outputs = {"en": ROOT / "README.md", "zh": ROOT / "README.zh.md"}
    for locale in locales:
        readme, stats = build(source, overlay, locale=locale)
        outputs[locale].write_text(readme, encoding="utf-8")
        print_stats(outputs[locale].name, stats)


if __name__ == "__main__":
    main()
