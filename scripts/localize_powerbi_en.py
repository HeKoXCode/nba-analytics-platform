# ruff: noqa: E501, RUF001
"""Apply the reviewed English copy and model display names after storytelling.

Run after update_powerbi_storytelling.py. The SQL query identifiers and original
source-column names are retained except for the explicit q10 contract migration.
This stage is idempotent: it changes the extracted project, never the PBIX.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POWERBI = ROOT / "CODE" / "Dashboard - POWERBI"
PROJECT = POWERBI / "Analisis_NBA_BestTeam"
CONTRACT = json.loads((POWERBI / "english_content_contract.json").read_text(encoding="utf-8"))

# Model display names and their references in report JSON. The sourceColumn
# mappings of existing SQL views remain unchanged (see localize_model()).
FIELDS = {
    "Porcentaje de victorias ultimos 10 años": "Win rate (last 10 seasons)",
    "Puntos por partido ultimos 10 años": "Points per game (last 10 seasons)",
    "Década de temporada": "Season decade",
    "Puntos como visitante": "Away points per game",
    "Puntos como Local": "Home points per game",
    "Porcentaje de acierto": "Field-goal percentage (FG%)",
    "Eficiencia de tiro": "Field-goal percentage (FG%)",
    "Balones perdidos": "Turnovers per game",
    "Puntos por partido": "Points per game (PPG)",
    "Franquicia": "Team",
}

# Exact copy produced by the historical generator plus retained visible labels.
# Longest-match replacement prevents a generic field name from corrupting copy.
COPY = {
    "De seis fuentes versionadas a una historia ejecutiva sobre rendimiento, contexto y evolución de la NBA.":
        "Six versioned sources become a clear view of team performance, context and change.",
    "De 161.111 filas fuente a 65.642 partidos auditables, con ETL versionado, SQL Server y DirectQuery.":
        "From 161,111 source rows to 65,642 auditable games, with a versioned ETL, SQL Server and DirectQuery.",
    "Panorama histórico  →  ventaja y estabilidad  →  perfil y ofensiva  →  pico y actualidad  →  evidencia":
        "Historical performance  →  home context  →  player profiles  →  peak vs. 2013–2022  →  evidence",
    "PREGUNTA  ¿Quién sostuvo el mejor rendimiento y cómo evolucionó el ritmo de anotación?":
        "QUESTION  Which team led the historical win-rate ranking, and how did scoring change by decade?",
    "PREGUNTA  ¿Cuánto cambia el desempeño por localía y qué equipos varían menos entre temporadas?":
        "QUESTION  How does home court relate to scoring, and which teams vary less across seasons?",
    "PREGUNTA  ¿Qué relación muestran el contexto ofensivo y el perfil físico de la muestra?":
        "QUESTION  What do offensive context and the available historical player profiles show together?",
    "PREGUNTA  ¿El pico histórico coincide con el mejor rendimiento de la última década disponible?":
        "QUESTION  Do the longest observed streak and the highest 2013–2022 win rate belong to the same team?",
    "Spurs lidera el win rate histórico: 59,53% en 4.077 partidos.":
        "The Spurs lead the historical win rate: 59.53% across 4,077 games.",
    "El PPG de liga pasa de 76,23 (1940s) a 112,07 (2020s).":
        "Eligible team-game scoring rises from 76.23 PPG in the 1940s to 112.07 in the 2020s.",
    "61,20% de victorias en casa frente a 37,36% como visitante.":
        "Home scoring averages 104.69 PPG versus 101.11 PPG away.",
    "La localía agrega 3,58 PPG; Pelicans presenta el menor CV de win rate (20,81%).":
        "The difference is about 3.6 PPG across team-seasons; the Pelicans have the lowest win-rate CV (20.81%).",
    "3.225 perfiles: 199,24 cm y 213,36 lb de promedio entre franquicias.":
        "3,225 historical profiles: team-average means of 199.24 cm and 213.36 lb.",
    "La muestra más amplia por franquicia reúne 197 perfiles históricos.":
        "The largest team sample contains 197 historical player profiles.",
    "Lakers registra la mayor racha histórica (33); Warriors lidera 2013–2022 con 64,20% y 112,03 PPG.":
        "The Lakers have the longest observed streak (33); the Warriors lead 2013–2022 at 66.53% (656/986 games).",
    "El revisor puede ejecutar el pipeline, cargar el modelo, contrastar el snapshot y recorrer la misma historia en DirectQuery.":
        "A reviewer can run the ETL, load the model, reconcile the snapshot and inspect the same DirectQuery report.",
    "6 CSV VERSIONADOS    ·    161.111 FILAS FUENTE    ·    65.642 PARTIDOS    ·    11 PRUEBAS":
        "6 VERSIONED CSVs    ·    161,111 SOURCE ROWS    ·    65,642 GAMES    ·    13 TESTS",
    "6 VERSIONED CSVs    ·    161,111 SOURCE ROWS    ·    65,642 GAMES    ·    11 TESTS":
        "6 VERSIONED CSVs    ·    161,111 SOURCE ROWS    ·    65,642 GAMES    ·    13 TESTS",
    "6 CSV versionados  →  contrato v1.0.0  →  ETL Python  →  SQL Server  →  15 objetos analíticos  →  Power BI DirectQuery":
        "6 versioned CSVs  →  contract v1.0.0  →  Python ETL  →  SQL Server  →  15 analytical objects  →  Power BI DirectQuery",
    "ETL Python reproducible  ·  modelo SQL Server  ·  consultas de reconciliación  ·  PBIT compilada  ·  fuente pbi-tools":
        "Reproducible Python ETL  ·  SQL Server model  ·  reconciliation queries  ·  compiled PBIT  ·  pbi-tools source",
    "6 CSV · 161.111 filas": "6 CSVs · 161,111 rows",
    "65.642 partidos únicos · temporadas 1946–2022": "65,642 unique games · seasons 1946–2022",
    "30 franquicias comparables · 0 huérfanos entre tablas": "30 mapped teams · zero cross-table orphans",
    "11 pruebas · 89,92%": "13 tests · 89.92% core ETL coverage",
    "11 tests · 89.92% core ETL coverage": "13 tests · 89.92% core ETL coverage",
    "Reconciliación SQL · carga idempotente · controles de contrato":
        "SQL reconciliation · idempotent load · schema checks",
    "Manifiestos, snapshot de resultados y fuente Power BI versionada":
        "Manifests, result snapshot and versioned Power BI source",
    "Python ETL  →  SQL Server  →  15 objetos analíticos  →  Power BI DirectQuery":
        "Python ETL  →  SQL Server  →  15 analytical objects  →  Power BI DirectQuery",
    "Rendimiento histórico | 1946–2022 | win rate": "Historical win rate | seasons 1946–2022",
    "Evolución anotadora | década de temporada | PPG": "Scoring by season decade | points per game (PPG)",
    "Antigüedad vs rendimiento reciente | 2020–2022 | win rate":
        "Franchise age vs. win rate | seasons 2020–2022",
    "Estabilidad intertemporada | 1946–2022 | CV del win rate":
        "Season-to-season consistency | 1946–2022 | win-rate CV",
    "Efecto localía | 1946–2022 | PPG local vs visitante":
        "Home vs. away scoring | 1946–2022 | team-season PPG",
    "Eficiencia vs riesgo | 1946–2022 | FG% y pérdidas por partido":
        "Shooting vs. turnovers | 1946–2022 | FG% and turnovers/game",
    "Top 12 contexto ofensivo | muestra histórica | PPG y FG%":
        "Offensive context: top 12 | historical sample | PPG and FG%",
    "Perfil físico | 3.225 perfiles | altura (cm) y peso (lb)":
        "Player profiles | 3,225 historical records | height (cm), weight (lb)",
    "Pico histórico | 1946–2022 | racha máxima de victorias":
        "Historical peak | 1946–2022 | longest winning streak",
    "Ventana reciente | 2013–2022 | win rate y PPG":
        "Recent window | 2013–2022 | top 12 by win rate",
    "01 · HISTORIA": "01 · HISTORY",
    "02 · CONTEXTO": "02 · CONTEXT",
    "03 · PERFIL": "03 · PROFILES",
    "04 · ACTUALIDAD": "04 · PEAK",
    "01 HISTORIA": "01 HISTORY",
    "02 CONTEXTO": "02 CONTEXT",
    "03 PERFIL": "03 PROFILES",
    "04 ACTUALIDAD": "04 PEAK",
    "05 MÉTODO": "05 METHOD",
    "RECORRIDO ANALÍTICO": "ANALYTICAL PATH",
    "Dominio histórico y evolución anotadora": "Historical performance and scoring",
    "Localía, estabilidad y eficiencia": "Home context, consistency and shooting",
    "Contexto ofensivo y perfil físico": "Offense and historical player profiles",
    "Pico histórico frente a ventana reciente": "Historical peak vs. 2013–2022",
    "01 · Panorama histórico": "01 · Historical Performance",
    "02 · Ventaja y estabilidad": "02 · Home Advantage & Consistency",
    "03 · Perfil y ofensiva": "03 · Player Profiles & Offense",
    "04 · Pico y actualidad": "04 · Historical Peak vs. 2013–2022",
    "05 · Método y evidencia": "05 · Method & Evidence",
    "Metodología y cierre": "Method & Evidence",
    "1 · Historia y evolución": "1 · Historical performance",
    "2 · Eficiencia y consistencia": "2 · Home context and consistency",
    "3 · Talento y perfil": "3 · Player profiles",
    "Abrir 05 método": "Open method and evidence",
    "Abrir 04 actualidad": "Open historical peak",
    "Abrir 03 perfil": "Open player profiles",
    "Abrir 02 contexto": "Open home context",
    "Abrir 01 historia": "Open historical performance",
    "Abrir inicio": "Open overview",
    "HALLAZGO CLAVE": "KEY FINDING · FULL SAMPLE",
    "ENTREGABLES PARA REPRODUCIBILIDAD Y REVISIÓN TÉCNICA": "REVIEW & REPRODUCTION",
    "INICIO": "OVERVIEW",
    "MÉTODO": "EVIDENCE",
    "ANÁLISIS": "EXPLORE",
    "Abrir panorama histórico": "Open historical performance",
    "DATOS": "DATA",
    "15 objetos analíticos": "15 analytical objects",
    "30 franquicias comparables": "30 mapped teams",
    "MODELO": "MODEL",
    "CALIDAD": "QUALITY",
    "TRAZABILIDAD": "LINEAGE",
    "SHA-256 + evidencia": "SHA-256 + evidence",
    "Mayor muestra de perfiles": "Largest profile sample",
    "Cantidad de victorias consecutivas": "Consecutive wins",
    "Racha observada (victorias): ": "Observed streak (wins): ",
    "Button Inicio": "Home button",
    "-> Equipo": "-> Team",
    "Equipo": "Team",
    "altura promedio en cm": "average height (cm)",
    "peso promedio en libras": "average weight (lb)",
    "Puntos promedio por partido": "Average points per game",
    "Promedio de puntos por partido (PPG)": "Average PPG",
    "Average of puntos por partido": "Average points per game (PPG)",
    "Rachas y actualidad": "Historical peak and 2013–2022",
    "Promedio de Points per game (PPG)": "Average PPG",
    "Promedio de Field-goal percentage (FG%)": "Average FG%",
    "Promedio de Home points per game": "Average home PPG",
    "Promedio de Away points per game": "Average away PPG",
    "Promedio de Win rate (last 10 seasons)": "Average recent win rate",
    "Promedio de Points per game (last 10 seasons)": "Average recent PPG",
    "Promedio de": "Average of",
    "Suma de": "Sum of",
    "Recuento de": "Count of",
    "Máx. de": "Max of",
    "Pérdidas medias por partido": "Average turnovers per game",
    "Pérdidas por partido": "Turnovers per game",
    "Porcentaje de Victorias (Histórico)": "Historical win rate",
    "Porcentaje de Victorias": "Win rate",
    "Promedio de Puntos Histórico": "Historical mean points",
    "Variación promedio de victorias entre temporadas (%)": "Season-to-season win-rate CV (%)",
    "Años desde fundación": "Years since founding",
    "Máx. de franchise_age": "Max franchise age",
    "Máx. de n_players": "Max player profiles",
    "Año": "Season decade",
    "Ventaja local (PPG)": "Home scoring gap (PPG)",
    "FG% medio": "Average FG%",
    "PPG histórico medio": "Historical mean PPG",
    "PPG reciente (2013–2022)": "Recent PPG (2013–2022)",
    "Win rate histórico medio": "Historical mean win rate",
    "Win rate reciente medio": "Recent win rate",
    "Edad máxima de franquicia (años)": "Oldest franchise age (years)",
    "hallazgos ~": "findings ~",
    "Dos preguntas complementarias": "Two complementary questions",
    "Subtitulo": "Subtitle",
    "Botón X": "Button X",
    "Cerrar ✖️": "Close ✖️",
    "Conclusión": "Evidence",
    "análisis": "analysis",
    "Botón": "Button",
    "Menú": "Menu",
    "Análisis": "Analysis",
}


def substitute(value: str) -> str:
    for old, new in sorted(COPY.items(), key=lambda item: len(item[0]), reverse=True):
        value = value.replace(old, new)
    for old, new in sorted(FIELDS.items(), key=lambda item: len(item[0]), reverse=True):
        value = value.replace(old, new)
    return value


def localize_model() -> int:
    count = 0
    for path in sorted((PROJECT / "Model" / "tables").glob("*.tmdl")):
        before = path.read_text(encoding="utf-8-sig")
        lines = []
        for line in before.splitlines(keepends=True):
            if line.lstrip().startswith("sourceColumn:"):
                if path.name == "analytics vw_q10_recent_top.tmdl":
                    line = line.replace(
                        "Porcentaje de victorias ultimos 10 años", "win_rate_10y"
                    ).replace("Puntos por partido ultimos 10 años", "ppg_10y")
            else:
                for old, new in sorted(FIELDS.items(), key=lambda item: len(item[0]), reverse=True):
                    line = line.replace(old, new)
            lines.append(line)
        after = "".join(lines).replace("PBI_NavigationStepName = Navegación", "PBI_NavigationStepName = Navigation")
        if path.name == "analytics vw_q10_recent_top.tmdl":
            after = after.replace("sourceProviderType: decimal(38, 12)", "sourceProviderType: decimal(24, 12)")
        # Source values are fractions: escaped-percent format strings were
        # literal percent signs and did not apply the required x100 display.
        after = after.replace("0.0\\ %;-0.0\\ %;0.0\\ %", "0.0%")
        after = after.replace("0\\ %;-0\\ %;0\\ %", "0.00%")
        if after != before:
            path.write_text(after, encoding="utf-8", newline="\n")
            count += 1
    relationships = PROJECT / "Model" / "relationships.tmdl"
    before = relationships.read_text(encoding="utf-8-sig")
    after = before
    for old, new in FIELDS.items():
        after = after.replace(old, new)
    if after != before:
        relationships.write_text(after, encoding="utf-8", newline="\n")
        count += 1
    return count


def localize_report() -> int:
    count = 0
    for page in CONTRACT["pages"]:
        found = list((PROJECT / "Report" / "sections").glob("*/section.json"))
        matching = [path for path in found if json.loads(path.read_text(encoding="utf-8"))["name"] == page["page_id"]]
        if len(matching) != 1:
            raise RuntimeError(f"Page ID is not unique: {page['page_id']}")
        path = matching[0]
        source = json.loads(path.read_text(encoding="utf-8"))
        source["displayName"] = page["english_title"]
        new = json.dumps(source, ensure_ascii=False, indent=2) + "\n"
        if path.read_text(encoding="utf-8") != new:
            path.write_text(new, encoding="utf-8", newline="\n")
            count += 1

    for path in sorted((PROJECT / "Report").rglob("*.json")):
        before = path.read_text(encoding="utf-8-sig")
        after = substitute(before)
        json.loads(after)
        if after != before:
            path.write_text(after, encoding="utf-8", newline="\n")
            count += 1
    return count


def reduce_scatter_label_clutter() -> int:
    """Keep dense team scatters readable; team names remain in hover details."""

    count = 0
    visual_dirs = (
        "002_Análisis_2/visualContainers/07000_Eficiencia de Tiro vs Pérdidas de balón",
        "003_Análisis_3/visualContainers/03000_Perfil físico promedio de los equipos NBA",
    )
    for directory in visual_dirs:
        for filename in ("config.json", "dataTransforms.json"):
            path = PROJECT / "Report" / "sections" / directory / filename
            before = path.read_text(encoding="utf-8")
            payload = json.loads(before)
            visual = payload.get("singleVisual", payload)
            visual["objects"]["categoryLabels"][0]["properties"]["show"]["expr"]["Literal"]["Value"] = "false"
            after = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
            if after != before:
                path.write_text(after, encoding="utf-8", newline="\n")
                count += 1
    return count


def enforce_recent_visual_top_twelve() -> int:
    """Reproduce the visual-level filter saved and tested in Desktop QA6.

    The SQL view still exposes all 30 teams: other report visuals reuse it.
    The filter below was extracted from ArchivoGuardado.pbix on 2026-09-30.
    """

    directory = (
        PROJECT
        / "Report"
        / "sections"
        / "004_Insights"
        / "visualContainers"
        / "12000_Rendimiento reciente"
    )
    entity = "analytics vw_q10_recent_top"
    rank = {
        "Column": {
            "Expression": {"SourceRef": {"Entity": entity}},
            "Property": "rk_recent",
        }
    }
    where = [
        {
            "Condition": {
                "Comparison": {
                    "ComparisonKind": 4,  # less than or equal to
                    "Left": {
                        "Column": {
                            "Expression": {"SourceRef": {"Source": "a"}},
                            "Property": "rk_recent",
                        }
                    },
                    "Right": {"Literal": {"Value": "12L"}},
                }
            }
        }
    ]
    visual_filter = {
        "name": "41de3bf47e045ce8899b",
        "expression": deepcopy(rank),
        "filter": {
            "Version": 2,
            "From": [{"Name": "a", "Entity": entity, "Type": 0}],
            "Where": deepcopy(where),
        },
        "type": "Advanced",
        "howCreated": 1,
    }
    changes = 0
    query_path = directory / "query.json"
    query = json.loads(query_path.read_text(encoding="utf-8"))
    command = query["Commands"][0]["SemanticQueryDataShapeCommand"]
    command["Query"]["Where"] = deepcopy(where)
    changes += write_if_changed(query_path, query)

    filters_path = directory / "filters.json"
    changes += write_if_changed(filters_path, [visual_filter])

    transforms_path = directory / "dataTransforms.json"
    transforms = json.loads(transforms_path.read_text(encoding="utf-8"))
    select = command["Query"]["Select"]
    transforms["queryMetadata"]["Filters"] = [
        {"type": 2, "expression": deepcopy(select[0]["Aggregation"])},
        {"type": 2, "expression": deepcopy(select[1]["Aggregation"])},
        {"type": 0, "expression": deepcopy(select[2]["Column"])},
        {"type": 2, "expression": deepcopy(rank)},
    ]
    changes += write_if_changed(transforms_path, transforms)
    return changes


def write_if_changed(path: Path, payload: object) -> int:
    after = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if path.read_text(encoding="utf-8") == after:
        return 0
    path.write_text(after, encoding="utf-8", newline="\n")
    return 1


def exclude_blank_profile_team() -> int:
    """Hide Power BI's relationship-generated blank member in the team slicer.

    This exact advanced-filter shape was extracted from the Desktop-tested QA9
    template. The SQL team names themselves are non-null; the filter changes
    only the available slicer choices, not the underlying analytical views.
    """
    directory = (
        PROJECT
        / "Report"
        / "sections"
        / "003_Análisis_3"
        / "visualContainers"
        / "08000_advancedSlicerVisual (a910c)"
    )
    payload = [
        {
            "expression": {
                "Column": {
                    "Expression": {"SourceRef": {"Entity": "analytics vw_teams"}},
                    "Property": "Team",
                }
            },
            "filter": {
                "Version": 2,
                "From": [{"Name": "a", "Entity": "analytics vw_teams", "Type": 0}],
                "Where": [
                    {
                        "Condition": {
                            "Not": {
                                "Expression": {
                                    "Comparison": {
                                        "ComparisonKind": 0,
                                        "Left": {
                                            "Column": {
                                                "Expression": {"SourceRef": {"Source": "a"}},
                                                "Property": "Team",
                                            }
                                        },
                                        "Right": {"Literal": {"Value": "null"}},
                                    }
                                }
                            }
                        }
                    }
                ],
            },
            "type": "Advanced",
            "howCreated": 0,
            "isHiddenInViewMode": False,
        }
    ]
    return write_if_changed(directory / "filters.json", payload)


def main() -> int:
    model_count = localize_model()
    report_count = localize_report()
    report_count += reduce_scatter_label_clutter()
    report_count += enforce_recent_visual_top_twelve()
    report_count += exclude_blank_profile_team()
    print(f"English stage: {model_count} model files and {report_count} report JSON files updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
