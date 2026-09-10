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
    "Descifrando el Rendimiento y Evolución de las franquicias NBA": (
        "Rendimiento y evolución de las franquicias NBA"
    ),
    "Eficiencia y Consistencia": "Eficiencia y consistencia",
    "Porcentaje de balones perdidos por partido": "Pérdidas por partido",
    "Total de jugadores fichados": "Mayor muestra de jugadores por equipo",
    "Equipos ->": "Equipo",
    "Equipo ->": "Equipo",
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


def remove_redundant_power_query_renames(text: str) -> str:
    """Use the final SQL aliases directly instead of renaming obsolete source columns."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if '"Columnas con nombre cambiado" = Table.RenameColumns' not in line:
            continue
        if index == 0 or " = NBA_Project{" not in lines[index - 1]:
            raise RuntimeError("No se pudo identificar el paso SQL previo al renombrado.")
        source_step = lines[index - 1].strip().split(" =", 1)[0]
        del lines[index]
        for return_index in range(index, min(index + 4, len(lines))):
            if '#"Columnas con nombre cambiado"' in lines[return_index]:
                indent = lines[return_index][: len(lines[return_index]) - len(lines[return_index].lstrip())]
                lines[return_index] = f"{indent}{source_step}"
                break
        else:
            raise RuntimeError("No se encontró la salida del paso de renombrado.")
        break
    for index, line in enumerate(lines):
        if line.strip() != "in":
            continue
        previous = index - 1
        while previous >= 0 and not lines[previous].strip():
            previous -= 1
        if previous >= 0 and lines[previous].rstrip().endswith(","):
            lines[previous] = lines[previous].rstrip()[:-1]
    return "\n".join(lines) + "\n"


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


def update_column_format(path: Path, column_name: str, format_string: str) -> None:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    column_markers = {f"column {column_name}", f"column '{column_name}'"}
    for index, line in enumerate(lines):
        if line.strip() not in column_markers:
            continue
        block_end = next(
            (
                position
                for position in range(index + 1, len(lines))
                if lines[position].lstrip().startswith(("column ", "measure ", "partition "))
            ),
            len(lines),
        )
        for position in range(index + 1, block_end):
            if lines[position].strip().startswith("formatString:"):
                indent = lines[position][: len(lines[position]) - len(lines[position].lstrip())]
                lines[position] = f"{indent}formatString: {format_string}"
                path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
                return
        raise RuntimeError(f"La columna {column_name} no tiene formato en {path.name}.")
    raise RuntimeError(f"No se encontró la columna {column_name} en {path.name}.")


def update_turnover_visual_formats() -> None:
    page = SECTIONS / "002_Análisis_2" / "visualContainers"
    for directory_name in (
        "01000_Puntos promedio por partido (481ef)",
        "07000_Eficiencia de Tiro vs Pérdidas de balón",
    ):
        path = page / directory_name / "dataTransforms.json"
        payload = read_json(path)
        for item in payload.get("queryMetadata", {}).get("Select", []):
            if "tov_avg" in item.get("Name", ""):
                item["Format"] = "0.0"
        for item in payload.get("selects", []):
            if "tov_avg" in item.get("queryName", ""):
                item["format"] = "0.0"
        write_json(path, payload)


def make_slicer_backgrounds_transparent() -> None:
    for path in sorted((PROJECT / "Report" / "sections").rglob("config.json")):
        config = read_json(path)
        if config.get("singleVisual", {}).get("visualType") != "slicer":
            continue
        config["singleVisual"].setdefault("vcObjects", {})["background"] = [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "false"}}}
                }
            }
        ]
        write_json(path, config)


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
        "Alcance visual: 30 franquicias actuales; rivales internacionales, All-Star y equipos sin mapear permanecen auditables en el núcleo, pero no alteran los rankings comparativos.",
        "Calidad: 155 duplicados en cuarentena y 53 equipos históricos sin nombre actual representados explícitamente.",
        "Reproducibilidad: contrato v1.0.0, manifiestos SHA-256, reconciliación SQL y pruebas automatizadas.",
        "Límite: la muestra no es 22 GB, no contiene datos sintéticos y no predice resultados ni retornos financieros.",
        "Última validación integral: 10/09/2026.",
    ]
    style = {"fontWeight": "bold", "fontSize": "15pt", "color": "#e6e6e6"}
    config["singleVisual"]["objects"]["general"][0]["properties"]["paragraphs"] = [
        {"textRuns": [{"value": value, "textStyle": style}]} for value in paragraphs
    ]
    write_json(path, config)

    set_position(path.parent, x=120, y=215, width=1080, height=450)

    title_path = SECTIONS / "006_Conclusión" / "visualContainers" / "10000_textbox (dc975)"
    title = read_json(title_path / "config.json")
    title["singleVisual"]["objects"]["general"][0]["properties"]["paragraphs"] = [
        {
            "textRuns": [
                {
                    "value": "Metodología y evidencia",
                    "textStyle": {
                        "fontWeight": "bold",
                        "fontSize": "32pt",
                        "color": "#ffffff",
                    },
                }
            ],
            "horizontalTextAlignment": "center",
        }
    ]
    write_json(title_path / "config.json", title)
    set_position(title_path, x=120, y=105, width=1080, height=85)


def update_player_sample_label() -> None:
    path = (
        SECTIONS
        / "003_Análisis_3"
        / "visualContainers"
        / "00000_Subtitulo (66065)"
        / "config.json"
    )
    config = read_json(path)
    config["singleVisual"]["objects"]["general"][0]["properties"]["paragraphs"] = [
        {
            "textRuns": [
                {"value": "Mayor muestra de ", "textStyle": {"fontWeight": "bold"}},
                {"value": "jugadores por equipo"},
            ],
            "horizontalTextAlignment": "center",
        }
    ]
    write_json(path, config)


def update_efficiency_card_labels() -> None:
    page = SECTIONS / "002_Análisis_2" / "visualContainers"
    labels = {
        "00000_Subtitulo (f70c7)": "Pérdidas por partido",
        "00000_Subtitulo (4dab6)": "Eficiencia de tiro",
    }
    for directory_name, label in labels.items():
        path = page / directory_name / "config.json"
        config = read_json(path)
        config["singleVisual"]["objects"]["general"][0]["properties"]["paragraphs"] = [
            {
                "textRuns": [{"value": label, "textStyle": {"fontWeight": "bold"}}],
                "horizontalTextAlignment": "center",
            }
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

    move_once(
        SECTIONS
        / "000_Inicio"
        / "visualContainers"
        / "00000_textbox (e6685)",
        ARCHIVE / "000_Inicio" / "00000_textbox (e6685)",
    )

    conclusion_visuals = SECTIONS / "006_Conclusión" / "visualContainers"
    for name in (
        "05000_Subtitulo",
        "06000_Subtitulo",
        "07000_Subtitulo",
        "08000_Subtitulo",
        "09000_Subtitulo",
        "16000_actionButton (a6ab6)",
        "17000_actionButton (4e465)",
    ):
        move_once(conclusion_visuals / name, ARCHIVE / "006_Conclusión" / name)

    move_once(
        source_visuals / "10000_textbox (849f8)",
        ARCHIVE / "003_Análisis_3" / "10000_textbox (849f8)",
    )

    for path in sorted((PROJECT / "Report").rglob("*.json")):
        write_json(path, replace_strings(read_json(path)))

    for path in sorted((PROJECT / "Model" / "tables").glob("*.tmdl")):
        text = path.read_text(encoding="utf-8-sig")
        updated = text
        for previous_server in ("100.74.116.125,1433", "localhost,1433"):
            updated = updated.replace(
                f'Sql.Databases("{previous_server}")',
                'Sql.Databases(".\\SQLEXPRESS")',
            )
        updated = remove_redundant_power_query_renames(updated)
        if updated != text:
            path.write_text(updated, encoding="utf-8", newline="\n")

    update_column_format(
        PROJECT / "Model" / "tables" / "analytics vw_q7_balance_of_def.tmdl",
        "Balones perdidos",
        "0.0",
    )
    update_turnover_visual_formats()
    make_slicer_backgrounds_transparent()

    set_position(
        SECTIONS
        / "001_Análisis_1"
        / "visualContainers"
        / "08000_advancedSlicerVisual (34242)",
        x=963,
        y=85,
        width=346,
        height=90,
    )
    set_position(
        SECTIONS / "002_Análisis_2" / "visualContainers" / "10000_advancedSlicerVisual (b0ea8)",
        x=995,
        y=85,
        width=314,
        height=90,
    )
    set_position(
        SECTIONS / "002_Análisis_2" / "visualContainers" / "09000_advancedSlicerVisual (fa73f)",
        x=942,
        y=227,
        width=367,
        height=90,
    )
    set_position(
        source_visuals / "05000_Eficiencia ofensiva de equipos NBA",
        x=16,
        y=161,
        width=1279,
        height=324,
    )
    set_position(
        source_visuals / "03000_Perfil físico promedio de los equipos NBA",
        x=16,
        y=500,
        width=900,
        height=249,
    )
    set_position(
        source_visuals / "08000_advancedSlicerVisual (a910c)",
        x=930,
        y=500,
        width=365,
        height=90,
    )

    update_methodology()
    update_player_sample_label()
    update_efficiency_card_labels()
    print("I4 aplicado: seis páginas, dos visuales redistribuidos y origen SQL local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
