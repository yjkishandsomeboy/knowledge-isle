import os
import shutil
from dataclasses import dataclass
from pathlib import Path


def _find_codex() -> Path:
    configured = os.getenv("DEV_AGENT_CODEX_PATH")
    if configured:
        return Path(configured)
    candidates = sorted(
        (Path.home() / "AppData/Local/OpenAI/Codex/bin").glob("*/codex.exe"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise RuntimeError("Codex CLI not found; set DEV_AGENT_CODEX_PATH")
    return candidates[0]


def _find_gh() -> str:
    configured = os.getenv("DEV_AGENT_GH_PATH")
    if configured:
        return configured
    discovered = shutil.which("gh")
    if discovered:
        return discovered
    candidates = [
        Path("C:/Program Files/GitHub CLI/gh.exe"),
        Path.home() / "AppData/Local/Programs/GitHub CLI/gh.exe",
    ]
    existing = next((path for path in candidates if path.exists()), None)
    return str(existing) if existing else "gh"


@dataclass(frozen=True)
class AgentSettings:
    repo_root: Path
    data_dir: Path
    codex_path: Path
    gh_path: str
    github_repo: str
    poll_seconds: int
    host: str = "127.0.0.1"
    port: int = 8787

    @classmethod
    def load(cls) -> "AgentSettings":
        repo_root = Path(__file__).resolve().parents[4]
        data_dir = repo_root / "data/dev-agent"
        data_dir.mkdir(parents=True, exist_ok=True)
        worktree_dir = repo_root.parent / "knowledge-isle-agent-worktrees"
        worktree_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            repo_root=repo_root,
            data_dir=data_dir,
            codex_path=_find_codex(),
            gh_path=_find_gh(),
            github_repo=os.getenv(
                "DEV_AGENT_GITHUB_REPO", "yjkishandsomeboy/knowledge-isle"
            ),
            poll_seconds=int(os.getenv("DEV_AGENT_POLL_SECONDS", "600")),
        )

    @property
    def worktree_dir(self) -> Path:
        path = self.repo_root.parent / "knowledge-isle-agent-worktrees"
        path.mkdir(parents=True, exist_ok=True)
        return path
