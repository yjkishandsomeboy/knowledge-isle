import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def run_command(
    args: list[str],
    *,
    cwd: Path,
    timeout: int = 1800,
    check: bool = True,
    input_text: str | None = None,
) -> CommandResult:
    try:
        completed = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            input=input_text,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as error:
        raise RuntimeError(f"Command not found: {args[0]}") from error
    result = CommandResult(completed.returncode, completed.stdout, completed.stderr)
    if check and result.returncode != 0:
        summary = (result.stderr or result.stdout)[-4000:]
        raise RuntimeError(f"Command failed ({result.returncode}): {args[0]}\n{summary}")
    return result
