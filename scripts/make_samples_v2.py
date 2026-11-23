"""Genera el corpus de evaluación v2 en samples_v2/."""

from pathlib import Path

from make_samples import render_docx, render_pdf, write_text
from samples_v2_empresa import PDFS_EMPRESA
from samples_v2_manuales import MANUALES
from samples_v2_textos import DOCXS_V2, TEXT_FILES_V2


def main(out_dir: Path = Path("samples_v2")) -> list[Path]:
    """Genera los 15 documentos del corpus v2 y devuelve sus rutas."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    for spec in [*MANUALES, *PDFS_EMPRESA]:
        paths.append(render_pdf(spec, out_dir))

    for spec in DOCXS_V2:
        paths.append(render_docx(spec, out_dir))

    for filename, content in TEXT_FILES_V2.items():
        paths.append(write_text(filename, content, out_dir))

    return paths


if __name__ == "__main__":
    for p in main():
        print(p)
