"""Apply the repeatable NBA-I4 report and connection update."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "CODE" / "Dashboard - POWERBI" / "Analisis_NBA_BestTeam"
SECTIONS = PROJECT / "Report" / "sections"
ARCHIVE = ROOT / "DOCS" / "archive" / "powerbi_pre_i4_visuals"

PAGES = {
    "000_Inicio": "Inicio",
    "001_Análisis_1": "Historia y evolución",
    "002_Análisis_2": "Eficiencia y consistencia",
    "003_Análisis_3": "Talento y perfil",
    "004_Insights": "Rachas y actualidad",
    "006_Conclusión": "Metodología y cierre",
}

REPLACEMENTS = {
    "📈 1- Rendimiento histórico": "1 · Historia y evolución",
    "🧮 2- Eficiencia y consistencia": "2 · Eficiencia y consistencia",
    "💪 3-  Talento moderno": "3 · Talento y perfil",
    "Resumen de hallazgos": "Rachas y actualidad",
    "Hallazgos descriptivos": "Rachas y actualidad",
    "Hallazgos importantes": "Rachas y actualidad",
    "Como se compone el": "Dos preguntas complementarias",
    "Talento en la Actualidad": "Talento y perfil",
    "Rendimiento Histórico": "Historia y evolución",
    "Rendimiento histórico de las franquicias NBA": (
        "Victorias históricas por franquicia · 1946–2022 · porcentaje"
    ),
    "Evolución del promedio de puntos por partido en la NBA": (
        "Evolución del PPG de liga · 1940s–2020s · puntos"
    ),
    "Rendimiento en función de la Antiguedad": (
        "Antigüedad y victorias · 1946–2022 · años frente a porcentaje"
    ),
    "Desempeño ->  Local vs Visitante": (
        "Local frente a visitante · 1946–2022 · puntos por partido"
    ),
    "Eficiencia de Tiro vs Pérdidas de balón": (
        "Tiro y pérdidas · 1946–2022 · porcentaje y pérdidas por partido"
    ),
    "Consistencia histórica de las franquicias de NBA": (
        "Consistencia entre temporadas · 1946–2022 · CV de victorias (%)"
    ),
    "Perfil físico promedio de los equipos NBA": (
        "Perfil físico por equipo · muestra disponible · cm y libras"
    ),
    "Eficiencia ofensiva de equipos NBA ": (
        "Contexto ofensivo por equipo · muestra disponible · PPG y FG%"
    ),
    "Racha máxima de victorias consecutivas por franquicia": (
        "Mayor racha observada por franquicia · 1946–2022 · victorias"
    ),
    "Rendimiento en la Actualidad por Equipo": (
        "Rendimiento reciente por equipo · 2013–2022 · PPG y victorias (%)"
    ),
    "altura promedio en pies": "altura promedio en cm",
    "Rango de rachas : ": "Racha observada (victorias): ",
    "Perfil histórico": "Metodología y cierre",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    if path.exists() and read_json(path) == payload:
        return
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def replace_strings(value: object) -> object:
    if isinstance(value, str):
        for old, new in sorted(REPLACEMENTS.items(), key=lambda item: -len(item[0])):
            value = value.replace(old, new)
        return value
    if isinstance(value, list):
        return [replace_strings(item) for item in value]
    if isinstance(value, dict):
        return {key: replace_strings(item) for key, item in value.items()}
    return value


def set_position(directory: Path, *, x: float, y: float, width: float, height: float) -> None:
    config_path = directory / "config.json"
    config = read_json(config_path)
    position = config["layouts"][0]["position"]
    position.update({"x": x, "y": y, "width": width, "height": height})
    write_json(config_path, config)

    container_path = directory / "visualContainer.json"
    if container_path.exists():
        container = read_json(container_path)
        container.update({"x": x, "y": y, "width": width, "height": height})
        write_json(container_path, container)


def move_once(source: Path, destination: Path) -> None:
    if source.exists() and destination.exists():
        raise RuntimeError(f"Existen origen y destino: {source} / {destination}")
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))


def update_methodology() -> None:
    path = (
        SECTIONS / "006_Conclusión" / "visualContainers" / "04000_textbox (76d01)" / "config.json"
    )
    config = read_json(path)
    paragraphs = [
        "Fuente: seis CSV públicos versionados; 30.638.984 bytes y 161.111 filas de entrada.",
        "Cobertura: 65.642 partidos únicos entre 1946 y 2022; análisis descriptivo.",
        "Calidad: 155 duplicados en cuarentena y 53 equipos históricos sin nombre actual representados explícitamente.",
        "Reproducibilidad: contrato v1.0.0, manifiestos SHA-256, reconciliación SQL y pruebas automatizadas.",
        "Límite: la muestra no es 22 GB, no contiene datos sintéticos y no predice resultados ni retornos financieros.",
        "Última validación integral: 28/08/2026.",
    ]
    style = {"fontWeight": "bold", "fontSize": "12pt", "color": "#e6e6e6"}
    config["singleVisual"]["objects"]["general"][0]["properties"]["paragraphs"] = [
        {"textRuns": [{"value": value, "textStyle": style}]} for value in paragraphs
    ]
    write_json(path, config)


def main() -> int:
    for folder, display_name in PAGES.items():
        path = SECTIONS / folder / "section.json"
        section = read_json(path)
        section["displayName"] = display_name
        write_json(path, section)

    source_visuals = SECTIONS / "003_Análisis_3" / "visualContainers"
    target_visuals = SECTIONS / "004_Insights" / "visualContainers"
    moves = {
        "04000_Racha máxima de victorias consecutivas por franquicia": "11000_Racha histórica",
        "09000_Rendimiento en la Actualidad por Equipo": "12000_Rendimiento reciente",
    }
    for source_name, target_name in moves.items():
        move_once(source_visuals / source_name, target_visuals / target_name)

    set_position(
        target_visuals / "11000_Racha histórica",
        x=25,
        y=180,
        width=620,
        height=500,
    )
    set_position(
        target_visuals / "12000_Rendimiento reciente",
        x=675,
        y=180,
        width=620,
        height=500,
    )

    for name in ("05000_Subtitulo", "07000_textbox (9fccf)"):
        move_once(target_visuals / name, ARCHIVE / "004_Insights" / name)

    for path in sorted((PROJECT / "Report").rglob("*.json")):
        write_json(path, replace_strings(read_json(path)))

    for path in sorted((PROJECT / "Model" / "tables").glob("*.tmdl")):
        text = path.read_text(encoding="utf-8-sig")
        updated = text.replace(
            'Sql.Databases("100.74.116.125,1433")', 'Sql.Databases("localhost,1433")'
        )
        if updated != text:
            path.write_text(updated, encoding="utf-8", newline="\n")

    update_methodology()
    print("I4 aplicado: seis páginas, dos visuales redistribuidos y origen SQL local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
