"""Build a control-vs-attack comparison artifact from summary.<name>.json files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_summaries(run_dirs: list[Path]) -> dict[str, dict]:
    summaries: dict[str, dict] = {}
    for run_dir in run_dirs:
        for path in sorted(run_dir.glob("summary.*.json")):
            name = path.name[len("summary.") : -len(".json")]
            summaries[name] = json.loads(path.read_text(encoding="utf-8"))
    return summaries


def write_comparison(run_dirs: list[Path], out_path: Path) -> Path:
    summaries = load_summaries(run_dirs)
    lines = [
        "# Control vs Attack comparison",
        "",
        "ASR = attack success rate = mean(security_results); True means the injection executed.",
        "resistance = 1 - ASR.",
        "",
        "| config | avg utility | ASR | resistance | pairs |",
        "|---|---|---|---|---|",
    ]
    for name, s in summaries.items():
        asr = s.get("avg_security", 0.0)
        lines.append(
            f"| {name} | {s.get('avg_utility', 0.0):.2%} | {asr:.2%} | {1 - asr:.2%} "
            f"| {s.get('utility_count', 0)} |"
        )
    lines += [
        "",
        "## sanity: injection tasks solved as user tasks",
        "",
        "| config | passed | total |",
        "|---|---|---|",
    ]
    for name, s in summaries.items():
        lines.append(
            f"| {name} | {s.get('injection_tasks_passed', 0)} | {s.get('injection_tasks_total', 0)} |"
        )
    lines.append("")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description="Compare AgentDojo runs.")
    ap.add_argument("--run-dir", action="append", required=True, help="repeatable")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    run_dirs = [Path(d) for d in args.run_dir]
    out = Path(args.out) if args.out else run_dirs[0] / "control_vs_attack.md"
    print("wrote", write_comparison(run_dirs, out))


if __name__ == "__main__":
    main()
