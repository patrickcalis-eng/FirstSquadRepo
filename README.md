# First Squad Repo

Welcome to the first project file for this Squad repository.

## Getting Started

- `squad status` - check the Squad setup
- `copilot --agent squad` - start the Copilot Squad agent
- `git status` - verify repository state

## Project Purpose

This repository is initialized for Squad-based collaboration and AI-assisted development.

## Next Steps

- Add your project source files
- Define Squad agents and roles
- Commit and push changes to GitHub

## Meeting Notes Feature

This repository now includes a simple audio transcription and meeting minutes tool.

Usage:

- Install dependencies: `pip install -r requirements.txt`
- Set `OPENAI_API_KEY` in your environment
- Transcribe audio and save meeting overview:
  `python meeting_notes/cli.py path/to/audio.mp3 --output meeting_overview.json --show`
- Or use an existing transcript text file:
  `python meeting_notes/cli.py transcript.txt --text-mode --output meeting_overview.json --show`
- Review and edit the generated minutes before saving:
  `python meeting_notes/cli.py transcript.txt --text-mode --review --output meeting_overview.json`

The output file contains:

- `transcript`
- `summary`
- `decisions`
- `action_items`
