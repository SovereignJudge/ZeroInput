#!/usr/bin/env python3
"""ZeroInput profile preview runner.

This utility is intentionally conservative. It reads local JSON profiles,
prints a clear pre-game plan, and can write a session report. It does not
download files, edit the registry, close applications, or change system
services.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONFIG_FILE = ROOT / "booster_config.json"
PROFILES_FILE = ROOT / "profiles.json"
RULES_FILE = ROOT / "optimizer_rules.json"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def collect_environment() -> dict:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
        "cpu_count": os.cpu_count(),
    }


def build_plan(profile_name: str, profiles: dict, rules: dict) -> list[dict]:
    if profile_name not in profiles:
        known = ", ".join(sorted(profiles))
        raise SystemExit(f"Unknown profile '{profile_name}'. Available: {known}")

    selected = profiles[profile_name]
    plan = []
    for rule_id in selected.get("rules", []):
        rule = rules.get(rule_id)
        if not rule:
            plan.append({
                "id": rule_id,
                "title": "Missing rule",
                "detail": "This rule is referenced by the profile but not defined.",
                "risk": "review",
            })
            continue
        plan.append({"id": rule_id, **rule})
    return plan


def print_plan(profile_name: str, mode: str, plan: list[dict]) -> None:
    print(f"ZeroInput profile: {profile_name}")
    print(f"Mode: {mode}")
    print()
    for index, item in enumerate(plan, 1):
        print(f"[{index}] {item['title']}")
        print(f"    {item['detail']}")
        print(f"    risk: {item.get('risk', 'low')}")
    print()


def write_report(path: Path, profile_name: str, mode: str, plan: list[dict]) -> None:
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": profile_name,
        "mode": mode,
        "environment": collect_environment(),
        "planned_steps": plan,
    }
    with path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        f.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview a ZeroInput game booster profile.")
    parser.add_argument("--profile", default="balanced", help="Profile name from profiles.json")
    parser.add_argument("--preview", action="store_true", help="Keep output in preview mode")
    parser.add_argument("--report", default="session_report.json", help="Report path")
    args = parser.parse_args()

    config = load_json(CONFIG_FILE)
    profiles = load_json(PROFILES_FILE)
    rules = load_json(RULES_FILE)

    mode = "preview" if args.preview or config.get("preview_by_default", True) else "plan"
    plan = build_plan(args.profile, profiles, rules)

    print_plan(args.profile, mode, plan)
    report_path = Path(args.report)
    write_report(report_path, args.profile, mode, plan)
    print(f"Report written to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
