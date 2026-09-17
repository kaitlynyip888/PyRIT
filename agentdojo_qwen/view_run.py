"""View an AgentDojo task-result JSON: metadata, injections, and the full conversation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _content_to_text(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if isinstance(block, dict):
            parts.append(str(block.get("content", "")))
        else:
            parts.append(str(block))
    return "\n".join(p for p in parts if p)


def _tool_call_to_str(tc) -> str:
    if isinstance(tc, dict):
        fn = tc.get("function", tc)
        if isinstance(fn, dict):
            return f"{fn.get('name')}({fn.get('arguments')})"
        return str(fn)
    return str(tc)


def view(path: Path, show_messages: bool = True) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    print("=" * 88)
    print(f"file       : {path}")
    print(f"pipeline   : {data.get('pipeline_name')}")
    print(f"suite      : {data.get('suite_name')}")
    print(f"user task  : {data.get('user_task_id')}")
    print(f"inject task: {data.get('injection_task_id')}")
    print(f"attack     : {data.get('attack_type')}")
    print(f"utility    : {data.get('utility')}")
    print(f"security   : {data.get('security')}   (True = injection executed = attack success)")
    print(f"duration   : {data.get('duration')}")
    if data.get("error"):
        print(f"error      : {data['error']}")

    print("\n--- injections ---")
    injections = data.get("injections") or {}
    if not injections:
        print("(none)")
    for placeholder, text in injections.items():
        print(f"[{placeholder}]\n{text}")

    if show_messages:
        print("\n--- conversation ---")
        for i, msg in enumerate(data.get("messages") or []):
            role = msg.get("role")
            print(f"\n[{i}] {role}")
            text = _content_to_text(msg.get("content"))
            if text:
                print(text)
            for tc in msg.get("tool_calls") or []:
                print(f"    -> tool_call: {_tool_call_to_str(tc)}")
            if msg.get("tool_call"):
                print(f"    -> tool_call: {_tool_call_to_str(msg['tool_call'])}")
            if msg.get("error"):
                print(f"    !! error: {msg['error']}")


def main() -> None:
    ap = argparse.ArgumentParser(description="View an AgentDojo task result JSON.")
    ap.add_argument("path", help="path to a task result .json")
    ap.add_argument("--no-messages", action="store_true", help="show metadata only")
    args = ap.parse_args()
    view(Path(args.path), show_messages=not args.no_messages)


if __name__ == "__main__":
    main()
