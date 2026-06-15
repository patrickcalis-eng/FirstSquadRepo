import json
import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Tuple

try:
    import openai
except ImportError:
    openai = None


@dataclass
class MeetingMinutes:
    transcript: str
    summary: str
    decisions: List[str]
    action_items: List[str]


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text: str) -> List[str]:
    text = normalize_text(text)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def extract_decisions_and_actions(text: str) -> Tuple[List[str], List[str]]:
    sentences = split_sentences(text)
    lower = [s.lower() for s in sentences]

    decision_keywords = [
        "besloten",
        "beslissing",
        "we besluiten",
        "we beslissen",
        "afgesproken",
        "akkoord",
        "goedkeuring",
        "toestemming",
        "vastgelegd",
    ]
    action_keywords = [
        "actie",
        "actiepunt",
        "opvolgen",
        "moet",
        "zal",
        "doen",
        "uitvoeren",
        "verantwoordelijk",
        "plan",
        "taken",
        "deadline",
    ]

    decisions = []
    actions = []

    for sentence, lower_sentence in zip(sentences, lower):
        if any(keyword in lower_sentence for keyword in decision_keywords):
            decisions.append(sentence)
        if any(keyword in lower_sentence for keyword in action_keywords):
            actions.append(sentence)

    # Keep order and remove duplicates
    decisions = list(dict.fromkeys(decisions))
    actions = list(dict.fromkeys(actions))

    return decisions, actions


def summarize_transcript(text: str, max_sentences: int = 3) -> str:
    sentences = split_sentences(text)
    if not sentences:
        return ""
    if len(sentences) <= max_sentences:
        return text
    return " ".join(sentences[:max_sentences])


def transcribe_audio(audio_path: str, model: str = "whisper-1") -> str:
    if openai is None:
        raise RuntimeError(
            "OpenAI SDK is not installed. Install it with `pip install -r requirements.txt`."
        )

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY environment variable.")

    openai.api_key = api_key
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    with audio_path.open("rb") as audio_file:
        response = openai.Audio.transcriptions.create(
            model=model,
            file=audio_file,
            response_format="text",
        )

    text = getattr(response, "text", None) or response.get("text")
    if text is None:
        raise RuntimeError("Transcription failed: no text returned by OpenAI.")
    return normalize_text(text)


def load_text_file(path: str) -> str:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Text file not found: {path}")
    return normalize_text(path.read_text(encoding="utf-8"))


def create_meeting_minutes(transcript: str) -> MeetingMinutes:
    decisions, action_items = extract_decisions_and_actions(transcript)
    summary = summarize_transcript(transcript)
    return MeetingMinutes(
        transcript=transcript,
        summary=summary,
        decisions=decisions,
        action_items=action_items,
    )


def save_overview(minutes: MeetingMinutes, output_path: str) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(asdict(minutes), file, indent=2, ensure_ascii=False)


def load_overview(path: str) -> MeetingMinutes:
    path = Path(path)
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return MeetingMinutes(**data)
