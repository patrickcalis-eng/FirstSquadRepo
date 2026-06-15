#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

from meeting_notes.transcriber import (
    MeetingMinutes,
    create_meeting_minutes,
    load_overview,
    load_text_file,
    save_overview,
    transcribe_audio,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Transcribe audio and generate meeting minutes with decisions and action items."
    )
    parser.add_argument("input", help="Path to an audio file or transcript text file.")
    parser.add_argument(
        "--output",
        default="meeting_overview.json",
        help="Output JSON file for transcript, decisions, and action items.",
    )
    parser.add_argument(
        "--text-mode",
        action="store_true",
        help="Treat the input as an existing transcript text file instead of audio.",
    )
    parser.add_argument(
        "--model",
        default="whisper-1",
        help="OpenAI transcription model to use when transcribing audio.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Print the transcript, summary, decisions and action items to the console.",
    )
    parser.add_argument(
        "--review",
        action="store_true",
        help="Review and edit summary, decisions and action items before saving.",
    )
    parser.add_argument(
        "--load",
        action="store_true",
        help="Load an existing overview JSON file instead of transcribing.",
    )
    return parser


def print_overview(overview: dict) -> None:
    print("\n=== Meeting Overview ===\n")
    print("Summary:\n", overview.get("summary", ""), "\n")
    print("Decisions:")
    for decision in overview.get("decisions", []):
        print(f"- {decision}")
    print("\nAction Items:")
    for action in overview.get("action_items", []):
        print(f"- {action}")
    print("\nTranscript:\n")
    print(overview.get("transcript", ""))


def create_review_file(overview: dict) -> str:
    lines = [
        "# REVIEW MEETING NOTES",
        "# Edit the summary, decisions, and action items below. Save and close the editor when done.",
        "",
        "## Summary",
        overview.get("summary", ""),
        "",
        "## Decisions",
    ]

    decisions = overview.get("decisions", [])
    if decisions:
        lines.extend(f"- {decision}" for decision in decisions)
    else:
        lines.append("- ")

    lines.extend(["", "## Action Items"])
    actions = overview.get("action_items", [])
    if actions:
        lines.extend(f"- {action}" for action in actions)
    else:
        lines.append("- ")

    lines.extend(["", "## Transcript", overview.get("transcript", "")])
    temp_file = tempfile.NamedTemporaryFile(
        mode="w",
        delete=False,
        suffix=".md",
        encoding="utf-8",
    )
    temp_file.write("\n".join(lines))
    temp_file.close()
    return temp_file.name


def get_editor_command(path: str) -> list[str]:
    editor = os.environ.get("EDITOR")
    if editor:
        return editor.split() + [path]

    if os.name == "nt":
        return ["notepad", path]

    return ["nano", path]


def open_review_editor(path: str) -> None:
    command = get_editor_command(path)
    subprocess.run(command, check=True)


def parse_review_file(path: str) -> dict:
    data = {"summary": "", "decisions": [], "action_items": []}
    section = None

    with open(path, encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.rstrip("\n")
            stripped = line.strip()

            if stripped.startswith("## "):
                title = stripped[3:].lower()
                if title.startswith("summary"):
                    section = "summary"
                elif title.startswith("decisions"):
                    section = "decisions"
                elif title.startswith("action items"):
                    section = "action_items"
                else:
                    section = None
                continue

            if section == "summary":
                if stripped.startswith("#"):
                    continue
                data[section] += f"{raw_line}"
            elif section in {"decisions", "action_items"}:
                if stripped.startswith("-"):
                    item = stripped[1:].strip()
                    if item:
                        data[section].append(item)

    data["summary"] = data["summary"].strip()
    return data


def review_overview(overview: dict) -> dict:
    temp_path = create_review_file(overview)
    try:
        open_review_editor(temp_path)
        reviewed = parse_review_file(temp_path)
        overview["summary"] = reviewed["summary"]
        overview["decisions"] = reviewed["decisions"]
        overview["action_items"] = reviewed["action_items"]
        return overview
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    input_path = Path(args.input)

    if args.load:
        overview = load_overview(str(input_path))
    else:
        if args.text_mode or input_path.suffix.lower() == ".txt":
            transcript = load_text_file(str(input_path))
        else:
            transcript = transcribe_audio(str(input_path), model=args.model)

        minutes = create_meeting_minutes(transcript)
        overview = {
            "transcript": minutes.transcript,
            "summary": minutes.summary,
            "decisions": minutes.decisions,
            "action_items": minutes.action_items,
        }

    if args.review:
        overview = review_overview(overview)

    if args.show or args.review or not args.load:
        print_overview(overview)

    should_save = args.review or not args.load
    if should_save:
        save_overview(
            MeetingMinutes(
                transcript=overview["transcript"],
                summary=overview["summary"],
                decisions=overview["decisions"],
                action_items=overview["action_items"],
            ),
            args.output,
        )
        print(f"\nSaved meeting overview to: {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
