# Contributing

`README.md` and `README.zh.md` are generated. A pull request that edits skill rows in either file will be overwritten the next time the list is rebuilt.

## What to change instead

| Change | Where |
| --- | --- |
| Start-here kit | [`overlay/starter.json`](overlay/starter.json) (`blurb` / `blurb_zh`) |
| Topic merges (duplicate jobs) | [`overlay/merges.json`](overlay/merges.json) (`title` / `title_zh`) |
| Topics to omit | [`overlay/skip.json`](overlay/skip.json) |
| Topics that must appear | [`overlay/pin.json`](overlay/pin.json) |
| Off-topic skill names on a topic | [`overlay/deny.json`](overlay/deny.json) |
| Counts and copy knobs | [`overlay/config.json`](overlay/config.json) |

Rebuild:

```bash
python3 scripts/build.py
```

The script reads SkillPicker's published `website.json` (default: `../SkillPicker/skillpicker-web/data/website.json`) and writes both the English README and the Chinese `README.zh.md`. Skill blurbs in Chinese come from SkillPicker's `description_i18n` / `reason_i18n` fields.

## Suggesting an agent skill or a job

Open an issue with:

- The job (role, task, output, tool, or agent)
- The agent skill name and repo (`owner/repo@skill`)
- Why it belongs on that job, in one sentence

The live index — search, filters, evidence, and the full ranked lists — is **[skillpicker.xyz](https://skillpicker.xyz)** ([中文](https://skillpicker.xyz/zh/)). This repository is a curated snapshot of that index.

Agent skills are listed for relevance to a job. That is not a safety review and not an endorsement. Read the upstream `SKILL.md` before you run anything.
