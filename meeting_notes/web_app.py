import os
import tempfile
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from meeting_notes.transcriber import create_meeting_minutes, transcribe_audio

app = Flask(__name__, template_folder="templates")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/transcribe", methods=["POST"])
def transcribe_route():
    transcript_text = request.form.get("transcript_text", "").strip()
    audio_file = request.files.get("audio_file")

    if not transcript_text and not audio_file:
        return jsonify({"error": "Upload audio of voer een transcriptie in."}), 400

    if audio_file:
        suffix = Path(audio_file.filename).suffix or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name
        try:
            transcript = transcribe_audio(temp_path)
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
    else:
        transcript = transcript_text

    minutes = create_meeting_minutes(transcript)
    return jsonify(
        transcript=minutes.transcript,
        summary=minutes.summary,
        decisions=minutes.decisions,
        action_items=minutes.action_items,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
