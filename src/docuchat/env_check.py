import time
from collections.abc import Iterable
from dataclasses import dataclass

from openai import OpenAI, OpenAIError

from docuchat.config import Settings, get_settings

MISSING_API_KEY = "sin-clave"  # marcador: el servidor responderá 401 en vez de romper


@dataclass(frozen=True)
class CheckResult:
    """Resultado de una comprobación."""

    name: str
    ok: bool
    detail: str


def make_client(base_url: str, settings: Settings) -> OpenAI:
    """Crea un cliente OpenAI contra base_url con la api_key y el timeout de settings."""
    return OpenAI(
        base_url=base_url,
        api_key=settings.llm_api_key or MISSING_API_KEY,
        timeout=settings.request_timeout,
    )


def model_available(wanted: str, available: Iterable[str]) -> bool:
    """Indica si el id del modelo está exactamente en la lista."""
    return wanted in available


def check_model_listed(client: OpenAI, model: str, name: str) -> CheckResult:
    """Comprueba que el servidor lista el modelo."""
    try:
        ids = [m.id for m in client.models.list()]
    except OpenAIError as e:
        return CheckResult(name, False, f"{type(e).__name__}: {e}")
    if model_available(model, ids):
        return CheckResult(name, True, f"{model} disponible")
    lista = ", ".join(sorted(ids)) if ids else "ninguno"
    return CheckResult(name, False, f"{model} no encontrado; disponibles: {lista}")


def check_embedding(client: OpenAI, model: str) -> CheckResult:
    """Pide un embedding de prueba y comprueba que no está vacío."""
    try:
        emb = client.embeddings.create(model=model, input=["prueba de embeddings"])
    except OpenAIError as e:
        return CheckResult("embedding", False, f"{type(e).__name__}: {e}")
    data = emb.data
    if not data or not data[0].embedding:
        return CheckResult("embedding", False, "respuesta vacía")
    vector = data[0].embedding
    return CheckResult("embedding", True, f"dim={len(vector)}")


def check_chat(client: OpenAI, model: str) -> CheckResult:
    """Pide una respuesta corta al LLM y mide el tiempo."""
    try:
        start = time.perf_counter()
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Responde solo con la palabra OK."}],
            max_tokens=200,
        )
        segundos = time.perf_counter() - start
    except OpenAIError as e:
        return CheckResult("chat", False, f"{type(e).__name__}: {e}")
    choices = resp.choices
    if not choices:
        return CheckResult("chat", False, "respuesta vacía")
    return CheckResult("chat", True, f"respuesta en {segundos:.1f} s")


def run_checks(
    settings: Settings,
    llm_client: OpenAI,
    embedding_client: OpenAI,
    rerank_client: OpenAI | None = None,
) -> list[CheckResult]:
    """Ejecuta las cuatro comprobaciones; añade la del reranker si está activado."""
    results = [
        check_model_listed(llm_client, settings.llm_model, "llm_model"),
        check_model_listed(embedding_client, settings.embedding_model, "embedding_model"),
        check_embedding(embedding_client, settings.embedding_model),
        check_chat(llm_client, settings.llm_model),
    ]
    if settings.rerank_enabled:
        if rerank_client is None:
            results.append(CheckResult("rerank_model", False, "sin cliente de rerank"))
        else:
            results.append(check_model_listed(rerank_client, settings.rerank_model, "rerank_model"))
    return results


def format_result(result: CheckResult) -> str:
    """Formatea un resultado en una línea."""
    tag = "[OK]" if result.ok else "[FAIL]"
    return f"{tag} {result.name}: {result.detail}"


def main() -> int:
    """Punto de entrada: imprime los resultados y devuelve 0 si todo ok, 1 si no."""
    settings = get_settings()
    if not settings.llm_api_key:
        print("Aviso: DOCUCHAT_LLM_API_KEY está vacía; ponla en .env.")
    llm_client = make_client(settings.llm_base_url, settings)
    embedding_client = make_client(settings.embedding_base_url, settings)
    rerank_client: OpenAI | None = None
    if settings.rerank_enabled:
        rerank_client = make_client(settings.rerank_base_url, settings)
    results = run_checks(settings, llm_client, embedding_client, rerank_client)
    for r in results:
        print(format_result(r))
    if all(r.ok for r in results):
        print("Entorno listo.")
        return 0
    print("Hay comprobaciones fallidas.")
    return 1
