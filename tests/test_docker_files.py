import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def env_names(text: str) -> set[str]:
    """Devuelve los nombres de variables DOCUCHAT_ capturados por el regex."""
    return {name.lower() for name in re.findall(r"DOCUCHAT_([A-Z_]+)", text)}


@pytest.fixture()
def dockerignore_text() -> str:
    return (ROOT / ".dockerignore").read_text()


@pytest.fixture()
def dockerfile_text() -> str:
    return (ROOT / "Dockerfile").read_text()


@pytest.fixture()
def compose_text() -> str:
    return (ROOT / "compose.yaml").read_text()


# ---------- Test 1: .dockerignore ----------
def test_dockerignore_contents(dockerignore_text: str) -> None:
    lines = {line.strip() for line in dockerignore_text.splitlines() if line.strip()}
    required = {".env", ".env.*", ".venv", "data", ".git"}
    assert required.issubset(lines)


# ---------- Test 2: Dockerfile – ninguna COPY con .env, sin "COPY . .", vars ----------
def test_dockerfile_no_env_copy(dockerfile_text: str) -> None:
    # ninguna línea que empiece por COPY contiene ".env"
    for line in dockerfile_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("COPY") and ".env" in stripped:
            pytest.fail(f"COPY con .env no permitido: {stripped}")

    # no contiene "COPY . ."
    assert "COPY . ." not in dockerfile_text

    assert "DOCUCHAT_API_HOST=0.0.0.0" in dockerfile_text
    assert "USER docuchat" in dockerfile_text


# ---------- Test 3: Dockerfile fija versión de uv ----------
def test_dockerfile_uv_version(dockerfile_text: str) -> None:
    assert re.search(r"ghcr\.io/astral-sh/uv:\d+\.\d+\.\d+ ", dockerfile_text) is not None


# ---------- Test 4: env_names no vacío y subconjunto de Settings ----------
@pytest.mark.parametrize("filename", ["Dockerfile", "compose.yaml"])
def test_env_names_in_settings(filename: str, dockerfile_text: str, compose_text: str) -> None:
    """Los nombres de variables DOCUCHAT_ aparecen en Settings.model_fields."""
    from docuchat.config import Settings

    text = {"Dockerfile": dockerfile_text, "compose.yaml": compose_text}[filename]
    names = env_names(text)
    assert names, f"{filename}: no se encontró ninguna variable DOCUCHAT_"
    assert names.issubset(set(Settings.model_fields))


# ---------- Test 5: compose.yaml contiene strings esperados ----------
def test_compose_yaml_contents(compose_text: str) -> None:
    assert '"127.0.0.1:8001:8001"' in compose_text
    assert '"host.docker.internal:host-gateway"' in compose_text
    assert "required: false" in compose_text
    assert "./samples:/documents:ro" in compose_text


# ---------- Test 6: URLs consistent entre Dockerfile y compose ----------
def test_url_consistency(dockerfile_text: str, compose_text: str) -> None:
    url = "http://host.docker.internal:8000/v1"

    # ambas contienen exactamente 2 veces la URL
    assert dockerfile_text.count(url) == 2, (
        f"Dockerfile: {dockerfile_text.count(url)} ocurrencias (esperado 2)"
    )
    assert compose_text.count(url) == 2, (
        f"compose.yaml: {compose_text.count(url)} ocurrencias (esperado 2)"
    )

    # ninguno contiene "127.0.0.1:8000"
    assert "127.0.0.1:8000" not in dockerfile_text, "Dockerfile no debe referenciar 127.0.0.1:8000"
    assert "127.0.0.1:8000" not in compose_text, "compose.yaml no debe referenciar 127.0.0.1:8000"
