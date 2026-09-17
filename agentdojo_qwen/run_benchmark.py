"""Run AgentDojo benchmark suites against the remote Qwen pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from agentdojo.attacks.attack_registry import load_attack
from agentdojo.benchmark import benchmark_suite_with_injections, benchmark_suite_without_injections
from agentdojo.task_suite.load_suites import get_suite

from agentdojo_qwen.config import load_config
from agentdojo_qwen.pipeline import build_pipeline
from agentdojo_qwen.report import summarize, write_summary


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run AgentDojo against the local Qwen pipeline.")
    p.add_argument("--suite", default="workspace")
    p.add_argument("--benchmark-version", default=None)
    p.add_argument("--user-task", action="append", default=[])
    p.add_argument("--injection-task", action="append", default=[])
    p.add_argument("--mode", choices=["no-attack", "attack"], default="no-attack")
    p.add_argument("--attack", default="important_instructions_no_names")
    p.add_argument("--out", default=None)
    p.add_argument("--list", action="store_true", help="List task ids and exit")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config()
    version = args.benchmark_version or cfg.benchmark_version
    suite = get_suite(version, args.suite)

    if args.list:
        print("user tasks     :", list(suite.user_tasks.keys()))
        print("injection tasks:", list(suite.injection_tasks.keys()))
        return

    out_dir = Path(args.out) if args.out else Path(cfg.log_dir)
    pipeline = build_pipeline(cfg, name_anchor=(args.mode == "attack"))

    user_tasks = args.user_task or None
    injection_tasks = args.injection_task or None

    if args.mode == "no-attack":
        results = benchmark_suite_without_injections(
            pipeline,
            suite,
            logdir=out_dir,
            force_rerun=True,
            user_tasks=user_tasks,
            benchmark_version=version,
        )
        name = "no-attack"
    else:
        attacker = load_attack(args.attack, suite, pipeline)
        attacker.model_name = cfg.victim_model  # address the victim by its real name
        results = benchmark_suite_with_injections(
            pipeline,
            suite,
            attacker,
            logdir=out_dir,
            force_rerun=True,
            user_tasks=user_tasks,
            injection_tasks=injection_tasks,
            benchmark_version=version,
        )
        name = args.attack

    summary = summarize(results)
    write_summary(out_dir, name, summary)
    print(f"=== {args.suite} / {name} ===")
    print(f"average utility : {summary['avg_utility']:.2%} ({summary['utility_count']} pairs)")
    if args.mode == "attack":
        print(f"average security: {summary['avg_security']:.2%} ({summary['security_count']} pairs)")
        print(
            "injection tasks solved as user tasks: "
            f"{summary['injection_tasks_passed']}/{summary['injection_tasks_total']}"
        )


if __name__ == "__main__":
    main()
