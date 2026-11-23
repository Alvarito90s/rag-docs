"""Variantes de evaluación: nombre → cambios sobre Settings."""

from docuchat.config import Settings

VARIANTS: dict[str, dict[str, object]] = {
    "base": {},
    "rerank": {"rerank_enabled": True},
    "sin_rerank": {"rerank_enabled": False},
    "contextual": {"contextual_enabled": True},
    "contextual_sin_rerank": {"contextual_enabled": True, "rerank_enabled": False},
}


def parse_variants(text: str) -> list[str]:
    """'base, rerank' → ['base', 'rerank']; ValueError si vacía, repetida o desconocida."""
    names = [n.strip() for n in text.split(",") if n.strip()]
    if not names:
        raise ValueError("indica al menos una variante")
    seen: set[str] = set()
    result: list[str] = []
    for name in names:
        if name in seen:
            raise ValueError(f"variante repetida: {name}")
        if name not in VARIANTS:
            available = ", ".join(VARIANTS)
            raise ValueError(f"variante desconocida: {name} (disponibles: {available})")
        seen.add(name)
        result.append(name)
    return result


def variant_settings(base: Settings, name: str) -> Settings:
    """Copia de base con los cambios de la variante; ValueError si el nombre
    o algún ajuste no existen."""
    if name not in VARIANTS:
        available = ", ".join(VARIANTS)
        raise ValueError(f"variante desconocida: {name} (disponibles: {available})")
    changes = VARIANTS[name]
    valid_fields = set(Settings.model_fields)
    for clave in changes:
        if clave not in valid_fields:
            raise ValueError(f"ajuste desconocido en la variante {name}: {clave}")
    return base.model_copy(update=dict(changes))
