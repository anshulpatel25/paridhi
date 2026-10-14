"""Automated verification that README.md and AGENTS.md remain synchronized with codebase."""

from pathlib import Path

import pytest
from fastmcp import FastMCP

from paridhi.core.config import Settings
from paridhi.infrastructure.mock import MockSpatialProvider
from paridhi.presentation.server import create_server

PROJECT_ROOT = Path(__file__).resolve().parent.parent
README_PATH = PROJECT_ROOT / "README.md"
AGENTS_PATH = PROJECT_ROOT / "AGENTS.md"


@pytest.fixture
def test_server() -> FastMCP:
    """Fixture providing a FastMCP server instance configured with MockSpatialProvider."""
    settings = Settings(
        server_name="ParidhiDocTest",
        server_version="0.1.0-test",
        _env_file=None,  # type: ignore[call-arg]
    )
    return create_server(settings=settings, provider=MockSpatialProvider())


def test_documentation_files_exist() -> None:
    """Ensure both README.md and AGENTS.md exist and contain substantial content."""
    assert README_PATH.exists(), f"Missing {README_PATH}"
    assert AGENTS_PATH.exists(), f"Missing {AGENTS_PATH}"

    readme_text = README_PATH.read_text(encoding="utf-8")
    agents_text = AGENTS_PATH.read_text(encoding="utf-8")

    assert len(readme_text.strip()) > 500, "README.md appears truncated or empty"
    assert len(agents_text.strip()) > 500, "AGENTS.md appears truncated or empty"


@pytest.mark.asyncio
async def test_all_tools_are_documented(test_server: FastMCP) -> None:
    """Ensure every FastMCP tool registered on the server is documented.

    Both README.md and AGENTS.md must document all registered tools.
    """
    tools = await test_server.list_tools()
    tool_names = [tool.name for tool in tools]
    assert len(tool_names) > 0, "No tools registered on server"

    readme_text = README_PATH.read_text(encoding="utf-8")
    agents_text = AGENTS_PATH.read_text(encoding="utf-8")

    for tool_name in tool_names:
        assert tool_name in readme_text, (
            f"Tool '{tool_name}' is registered in server.py but missing from README.md!"
        )
        assert tool_name in agents_text, (
            f"Tool '{tool_name}' is registered in server.py but missing from AGENTS.md!"
        )


def test_sequence_diagrams_in_readme() -> None:
    """Ensure README.md contains valid Mermaid sequence diagrams."""
    readme_text = README_PATH.read_text(encoding="utf-8")
    assert "```mermaid" in readme_text, "README.md is missing Mermaid diagrams"
    assert "sequenceDiagram" in readme_text, (
        "README.md is missing Mermaid sequence diagrams for use cases"
    )
    assert "discover_pois" in readme_text
    assert "ping" in readme_text


def test_documentation_sync_policy_documented() -> None:
    """Ensure both files describe the documentation synchronization mandate."""
    readme_text = README_PATH.read_text(encoding="utf-8")
    agents_text = AGENTS_PATH.read_text(encoding="utf-8")

    assert "AGENTS.md" in readme_text, (
        "README.md should reference AGENTS.md for synchronization policy"
    )
    assert "README.md" in agents_text, (
        "AGENTS.md should reference README.md for synchronization mandate"
    )


def test_license_and_release_documentation_exist() -> None:
    """Ensure LICENSE and RELEASE.md exist and contain required content."""
    license_path = PROJECT_ROOT / "LICENSE"
    release_path = PROJECT_ROOT / "RELEASE.md"

    assert license_path.exists(), f"Missing {license_path}"
    assert release_path.exists(), f"Missing {release_path}"

    license_text = license_path.read_text(encoding="utf-8")
    release_text = release_path.read_text(encoding="utf-8")

    assert "MIT License" in license_text
    assert "0.1.0" in release_text
    assert "ghcr.io" in release_text


def test_github_workflows_configuration() -> None:
    """Ensure CI and Docker workflows exist with correct trigger specifications."""
    workflows_dir = PROJECT_ROOT / ".github" / "workflows"
    ci_workflow = workflows_dir / "ci.yml"
    docker_workflow = workflows_dir / "docker-publish.yml"

    assert ci_workflow.exists(), f"Missing {ci_workflow}"
    assert docker_workflow.exists(), f"Missing {docker_workflow}"

    ci_content = ci_workflow.read_text(encoding="utf-8")
    docker_content = docker_workflow.read_text(encoding="utf-8")

    # CI workflow checks (strictly manual trigger)
    assert "create-draft-release" in ci_content
    assert "ruff format" in ci_content
    assert "0.1.0" in ci_content
    assert "workflow_dispatch:" in ci_content
    assert "pull_request:" not in ci_content

    # Docker publish workflow checks (strictly tags, not main branch, arm64 only)
    assert "tags:" in docker_content
    assert "branches:" not in docker_content
    assert "platforms: linux/arm64" in docker_content
    assert "PARIDHI_SERVER_VERSION" in PROJECT_ROOT.joinpath("Dockerfile").read_text(
        encoding="utf-8"
    )
