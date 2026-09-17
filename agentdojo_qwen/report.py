"""Summarize AgentDojo SuiteResults and write evidence artifacts."""

from __future__ import annotations

import json
from pathlib import Path


def summarize(results) -> dict:
    utility = list(results["utility_results"].values())
    security = list(results["security_results"].values())
    inj = results.get("injection_tasks_utility_results", {})
    return {
        "avg_utility": (sum(utility) / len(utility)) if utility else 0.0,
        "avg_security": (sum(security) / len(security)) if security else 0.0,
        "utility_count": len(utility),
        "security_count": len(security),
        "injection_tasks_passed": sum(inj.values()) if inj else 0,
        "injection_tasks_total": len(inj),
        "utility_results": {f"{u}|{i}": v for (u, i), v in results["utility_results"].items()},
        "security_results": {f"{u}|{i}": v for (u, i), v in results["security_results"].items()},
    }


def write_summary(out_dir, name: str, summary: dict) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"summary.{name}.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    lines = [
        f"# AgentDojo run: {name}",
        "",
        f"- average utility: {summary['avg_utility']:.2%} ({summary['utility_count']} pairs)",
        f"- average security: {summary['avg_security']:.2%} ({summary['security_count']} pairs)",
        f"- injection tasks solved as user tasks: "
        f"{summary['injection_tasks_passed']}/{summary['injection_tasks_total']}",
        "",
        "## utility_results",
        "```json",
        json.dumps(summary["utility_results"], indent=2),
        "```",
        "",
        "## security_results",
        "```json",
        json.dumps(summary["security_results"], indent=2),
        "```",
        "",
    ]
    (out / f"summary.{name}.md").write_text("\n".join(lines), encoding="utf-8")
