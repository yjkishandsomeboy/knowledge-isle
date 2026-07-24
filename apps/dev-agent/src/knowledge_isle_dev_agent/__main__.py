import uvicorn

from knowledge_isle_dev_agent.config import AgentSettings


def main() -> None:
    settings = AgentSettings.load()
    uvicorn.run(
        "knowledge_isle_dev_agent.app:app",
        host=settings.host,
        port=settings.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
