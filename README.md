# LocalCore Lite

> **Want offline voice, local PDF Q&A, clipboard debugging, and 1-click installers?**
> Upgrade to [**LocalCore Pro**](../localcore-pro), the complete desktop experience.

LocalCore Lite is a free, open-source, text-only terminal assistant powered by Ollama.

## Features

- Streaming local chat
- Automatic RAM-aware 4B/8B/14B model selection
- CPU thread limits that preserve operating-system responsiveness
- `/paste` support for large code blocks and multi-line text
- `/clear` and `/exit` commands

## Quickstart

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Install Ollama from <https://ollama.com/download> before the first run.
