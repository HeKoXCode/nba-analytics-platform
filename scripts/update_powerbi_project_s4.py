"""Apply the repeatable S4 cleanup to the extracted pbi-tools project."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "CODE" / "Dashboard - POWERBI" / "Analisis_NBA_BestTeam"
REPORT = PROJECT / "Report"

REPLACEMENTS = {
    "Recomendación Final": "Perfil histórico",
    "~Análisis histórico-estadístico de equipos y jugadores para detectar": (
        "~Análisis histórico y estadístico para comparar"
    ),
    "     el mejor potencial de inversión deportiva.~": (
        "     patrones observados entre equipos NBA.~"
    ),
    "~Como se compone el  ": "~Resumen descriptivo de ",
    "EXITO ~": "hallazgos ~",
    "Hallazgos Importantes": "Hallazgos descriptivos",
    "📊": "",
    "💡": "",
    "🏀": "",
    "🌠": "",
    "🏆": "",
    "🔥 ": "",
    "Buena antigüedad +": "Antigüedad registrada  |",
    "🏆 ": "",
    "Consistencia histórica  + ": "Consistencia histórica  | ",
    "🎯 ": "",
    "Eficiencia ofensiva  → ": "Eficiencia ofensiva",
    "E X I T O": "",
    "Rendimiento sostenible": "Rendimiento histórico observado",
    " y equipos de ese perfil muestran % de victorias históricas altos.": (
        " presentan tasas históricas de victorias altas en la muestra disponible."
    ),
    "Consistencia y riesgo deportivo": "Variabilidad histórica",
    "• Algunas franquicias Miami Heat, Utah Jazz, Spurs. muestran baja variabilidad.": (
        "• Miami Heat, Utah Jazz y Spurs muestran menor variabilidad histórica "
        "en la muestra."
    ),
    "• Baja variabilidad = menor riesgo para el inversor: es más fácil predecir "
    "ingresos deportivos/futuros playoffs.": (
        "• La variabilidad observada no estima riesgo financiero, ingresos ni "
        "clasificación futura a playoffs."
    ),
    "Talento en la actualidad (últimos 10 años)": (
        "Rendimiento reciente (últimos 10 años disponibles)"
    ),
    "• Golden State Warriors aparece como caso modelo moderno: alta eficiencia "
    "ofensiva, rachas largas de victorias y estilo exportable/mercadeable.": (
        "• Golden State Warriors destaca en eficiencia y rachas dentro del periodo "
        "observado; no se evaluó valor de mercado."
    ),
    "🏆San Antonio Spurs🏆": "San Antonio Spurs — perfil histórico",
    "  🌠Mayor consistencia histórica y menor riesgo deportivo.": (
        "Perfil histórico destacado en la muestra disponible."
    ),
    "  📖Cultura ganadora y estructura de gestión de juego estable.": (
        "Tasa histórica de victorias observada: 59,5 %."
    ),
    "  ⚙️En constante construcción con talento joven y proyección alta.": (
        "Promedio observado: 104,5 puntos por partido."
    ),
    "  💡Enfoque sostenible que garantiza retorno a mediano plazo.": (
        "El análisis no estima retorno financiero ni desempeño futuro."
    ),
    "                                                                                                                                                                                                                "
    "~El valor no está solo en ganar hoy, sino en mantener un modelo que gane siempre ~": (
        "~Comparación descriptiva; no es una recomendación de inversión.~"
    ),
}


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


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def dropdown_property() -> list[dict]:
    return [
        {
            "properties": {
                "mode": {"expr": {"Literal": {"Value": "'Dropdown'"}}}
            }
        }
    ]


def convert_slicer(config_path: Path) -> bool:
    config = read_json(config_path)
    visual = config.get("singleVisual", {})
    if visual.get("visualType") != "advancedSlicerVisual":
        return False

    visual["visualType"] = "slicer"
    visual.setdefault("objects", {})["data"] = dropdown_property()
    write_json(config_path, replace_strings(config))

    transforms_path = config_path.with_name("dataTransforms.json")
    if transforms_path.exists():
        transforms = read_json(transforms_path)
        transforms.setdefault("objects", {})["data"] = dropdown_property()
        write_json(transforms_path, replace_strings(transforms))
    return True


def remove_background_image(page_config: Path) -> None:
    config = read_json(page_config)
    for background in config.get("objects", {}).get("background", []):
        background.get("properties", {}).pop("image", None)
    write_json(page_config, config)


def remove_custom_visual_theme_entry() -> None:
    theme_path = (
        PROJECT
        / "StaticResources"
        / "SharedResources"
        / "BaseThemes"
        / "CY24SU10.json"
    )
    theme = read_json(theme_path)
    theme.get("visualStyles", {}).pop("advancedSlicerVisual", None)
    write_json(theme_path, theme)


def main() -> int:
    duplicate = REPORT / "sections" / "005_Duplicado de Conclusión"
    if duplicate.exists():
        raise SystemExit(
            "Elimine primero la carpeta duplicada validada: "
            f"{duplicate.relative_to(ROOT)}"
        )

    json_files = sorted(REPORT.rglob("*.json"))
    for path in json_files:
        write_json(path, replace_strings(read_json(path)))

    slicers = sum(
        convert_slicer(path)
        for path in (REPORT / "sections").rglob("config.json")
    )
    if slicers not in {0, 4}:
        raise SystemExit(f"Se esperaban 0 o 4 slicers pendientes; se encontraron {slicers}.")

    remove_background_image(REPORT / "sections" / "004_Insights" / "config.json")
    remove_background_image(REPORT / "sections" / "006_Conclusión" / "config.json")
    remove_custom_visual_theme_entry()

    conclusion_section = (
        REPORT / "sections" / "006_Conclusión" / "section.json"
    )
    conclusion = read_json(conclusion_section)
    conclusion["ordinal"] = 5
    write_json(conclusion_section, conclusion)

    print(f"S4 aplicado al proyecto Power BI: {len(json_files)} JSON; {slicers} slicers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
