from collections import deque
from dataclasses import dataclass
import subprocess
import sys
import time
from typing import Any, Iterator, Mapping

import ollama

from core.config import HardwareProfile, detect_hardware


@dataclass(frozen=True)
class StreamChunk:
    kind: str
    text: str


class LocalLLMEngine:
    def __init__(self, profile: HardwareProfile | None = None) -> None:
        self.profile = profile or detect_hardware()
        self.model = self.profile.model
        self.history: deque[dict[str, str]] = deque(maxlen=20)
        self.tokens_per_second = 0.0

    def ensure_model_ready(self) -> None:
        try:
            response = ollama.list()
        except Exception as exc:
            print("[Setup] Starting Ollama background service...")
            try:
                if sys.platform == "win32":
                    subprocess.Popen(
                        ["ollama", "serve"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW
                        | subprocess.DETACHED_PROCESS,
                    )
                else:
                    subprocess.Popen(
                        ["ollama", "serve"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True,
                    )
            except FileNotFoundError as not_found:
                raise RuntimeError(
                    "Ollama is not installed. Install Ollama, then try again."
                ) from not_found

            deadline = time.monotonic() + 15.0
            while time.monotonic() < deadline:
                time.sleep(0.5)
                try:
                    response = ollama.list()
                    break
                except Exception:
                    continue
            else:
                raise RuntimeError("Ollama did not start within 15 seconds.") from exc

        models = getattr(response, "models", None)
        if models is None and isinstance(response, Mapping):
            models = response.get("models", [])
        available: set[str] = set()
        for model in models or []:
            name = getattr(model, "model", None)
            if name is None and isinstance(model, Mapping):
                name = model.get("model") or model.get("name")
            if name:
                available.add(str(name).split(":")[0])
        base_name = self.model.split(":")[0]
        if self.model not in available and base_name not in available:
            ollama.pull(self.model)

    def clear_history(self) -> None:
        self.history.clear()

    @staticmethod
    def _field(chunk: Any, name: str) -> Any:
        if isinstance(chunk, Mapping):
            return chunk.get(name)
        return getattr(chunk, name, None)

    def stream(self, prompt: str) -> Iterator[StreamChunk]:
        self.history.append({"role": "user", "content": prompt})
        start = time.monotonic()
        generated_tokens = 0
        answer_parts: list[str] = []
        stream = ollama.chat(
            model=self.model,
            messages=list(self.history),
            stream=True,
            options={
                "num_ctx": self.profile.num_ctx,
                "num_thread": self.profile.cpu_threads,
            },
        )
        for chunk in stream:
            message = self._field(chunk, "message")
            thinking = self._field(message, "thinking")
            content = self._field(message, "content")
            if thinking:
                yield StreamChunk(kind="thinking", text=str(thinking))
            if content:
                text = str(content)
                answer_parts.append(text)
                generated_tokens += len(text.split())
                elapsed = max(time.monotonic() - start, 0.001)
                self.tokens_per_second = generated_tokens / elapsed
                yield StreamChunk(kind="content", text=text)
            eval_count = self._field(chunk, "eval_count")
            if eval_count:
                elapsed = max(time.monotonic() - start, 0.001)
                self.tokens_per_second = int(eval_count) / elapsed
        answer = "".join(answer_parts).strip()
        if answer:
            self.history.append({"role": "assistant", "content": answer})
