import sys

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from core.config import detect_hardware
from core.llm_engine import LocalLLMEngine


console = Console()


def read_paste_block() -> str:
    console.print(
        "[dim]Paste multi-line text, then type END on a new line "
        "(or press Ctrl+Z then Enter / Ctrl+D).[/dim]"
    )
    lines: list[str] = []
    while True:
        try:
            line = sys.stdin.readline()
        except (EOFError, KeyboardInterrupt):
            break
        if line == "":
            break
        if line.rstrip("\r\n") == "END":
            break
        lines.append(line.rstrip("\r\n"))
    return "\n".join(lines).strip()


def stream_reply(engine: LocalLLMEngine, prompt: str) -> str:
    answer = Text()
    thinking = Text()
    full_answer = ""
    with Live(
        console=console,
        refresh_per_second=12,
        transient=False,
        vertical_overflow="visible",
    ) as live:
        for chunk in engine.stream(prompt):
            if chunk.kind == "thinking":
                thinking.append(chunk.text)
            else:
                answer.append(chunk.text)
                full_answer += chunk.text
            live.update(
                Group(
                    Panel(thinking, title="Thinking", border_style="yellow")
                    if thinking
                    else Text(),
                    Panel(answer, title="LocalCore Lite", border_style="cyan"),
                )
            )
    console.print(
        f"[dim]{engine.tokens_per_second:.1f} tokens/sec[/dim]",
        justify="right",
    )
    return full_answer


def main() -> None:
    console.print(
        Panel(
            "[bold cyan]LocalCore Lite[/bold cyan]\n"
            "Free text-only chat | Commands: /paste /clear /exit",
            border_style="cyan",
        )
    )
    try:
        engine = LocalLLMEngine(detect_hardware())
        engine.ensure_model_ready()
    except RuntimeError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise SystemExit(1)

    while True:
        try:
            prompt = console.input("\n[bold green]You>[/bold green]")
        except (EOFError, KeyboardInterrupt):
            break
        prompt = prompt.strip()
        if not prompt:
            continue
        if prompt == "/exit":
            break
        if prompt == "/clear":
            engine.clear_history()
            console.print("[dim]Conversation history cleared.[/dim]")
            continue
        if prompt == "/paste":
            pasted = read_paste_block()
            if pasted:
                stream_reply(engine, pasted)
            else:
                console.print("[yellow]No text entered.[/yellow]")
            continue
        stream_reply(engine, prompt)


if __name__ == "__main__":
    main()
