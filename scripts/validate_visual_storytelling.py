# ruff: noqa: E501, RUF001
"""Validate the NBA Power BI storytelling redesign and compiled PBIT."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "CODE" / "Dashboard - POWERBI" / "Analisis_NBA_BestTeam"
SECTIONS = PROJECT / "Report" / "sections"
MODEL = PROJECT / "Model"
PBIT = ROOT / "CODE" / "Dashboard - POWERBI" / "Analisis_NBA_BestTeam.pbit"
SNAPSHOT = ROOT / "evidence" / "NBA-Visual-Storytelling" / "insight_snapshot.json"

EXPECTED_PAGES = {
    "Inicio": 0,
    "01 · Panorama histórico": 1,
    "02 · Ventaja y estabilidad": 2,
    "03 · Perfil y ofensiva": 3,
    "04 · Pico y actualidad": 4,
    "05 · Método y evidencia": 5,
}
EXPECTED_PBIT_BYTES = 6_377_058
EXPECTED_PBIT_SHA256 = "BFB581E8D43A404A6C87AE1BFB8FD59304911F38503431C9BDE928652996A368"
PAGE_IDS = {
    "000_Inicio": "85fd596523722c787dd8",
    "001_Análisis_1": "127f8fdec9d1ce997d14",
    "002_Análisis_2": "5080f8c0f82e46569dea",
    "003_Análisis_3": "eec7a94c9605ce1092d5",
    "004_Insights": "aa123345b8a05cd846e4",
    "006_Conclusión": "9aefac1bb66f2b6b0df9",
}
NAV_ITEMS = (
    ("000_Inicio", "INICIO"),
    ("001_Análisis_1", "01 HISTORIA"),
    ("002_Análisis_2", "02 CONTEXTO"),
    ("003_Análisis_3", "03 PERFIL"),
    ("004_Insights", "04 ACTUALIDAD"),
    ("006_Conclusión", "05 MÉTODO"),
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def find_queries(value: object) -> list[dict]:
    found: list[dict] = []
    if isinstance(value, dict):
        if isinstance(value.get("From"), list):
            found.append(value)
        for child in value.values():
            found.extend(find_queries(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(find_queries(child))
    return found


def position(directory: Path) -> tuple[float, float, float, float]:
    payload = read_json(directory / "config.json")
    value = payload["layouts"][0]["position"]
    return value["x"], value["y"], value["width"], value["height"]


def visible_title(directory: Path) -> str:
    payload = read_json(directory / "config.json")
    value = payload["singleVisual"]["vcObjects"]["title"][0]["properties"]["text"][
        "expr"
    ]["Literal"]["Value"]
    return value.strip("'")


def require_no_overlap(page: str, folders: list[str]) -> None:
    rectangles = {
        folder: position(SECTIONS / page / "visualContainers" / folder) for folder in folders
    }
    for index, left_name in enumerate(folders):
        left_x, left_y, left_w, left_h = rectangles[left_name]
        for right_name in folders[index + 1 :]:
            right_x, right_y, right_w, right_h = rectangles[right_name]
            overlap_x = min(left_x + left_w, right_x + right_w) - max(left_x, right_x)
            overlap_y = min(left_y + left_h, right_y + right_h) - max(left_y, right_y)
            require(
                overlap_x <= 0 or overlap_y <= 0,
                f"Visible overlap on {page}: {left_name} with {right_name}",
            )


def validate_pages() -> None:
    report_config = read_json(PROJECT / "Report" / "config.json")
    require(report_config["activeSectionIndex"] == 0, "The PBIT does not open on Inicio")
    state = {}
    for path in SECTIONS.glob("*/section.json"):
        section = read_json(path)
        state[section["displayName"]] = section["ordinal"]
    require(state == EXPECTED_PAGES, f"Unexpected source page order: {state}")


def validate_json_and_story() -> None:
    json_files = sorted((PROJECT / "Report").rglob("*.json"))
    require(len(json_files) >= 879, f"Unexpected report extraction size: {len(json_files)} JSON")
    for path in json_files:
        read_json(path)

    source_text = "\n".join(path.read_text(encoding="utf-8-sig") for path in json_files)
    for emoji in ("🏠", "🏁", "ℹ️", "⭐", "🔺", "🔄", "🧠"):
        require(emoji not in source_text, f"Decorative emoji remains: {emoji}")
    for phrase in (
        "PREGUNTA  ¿Quién sostuvo el mejor rendimiento",
        "PREGUNTA  ¿Cuánto cambia el desempeño por localía",
        "PREGUNTA  ¿Qué relación muestran el contexto ofensivo",
        "PREGUNTA  ¿El pico histórico coincide",
        "Spurs lidera el win rate histórico: 59,53% en 4.077 partidos.",
        "61,20% de victorias en casa frente a 37,36% como visitante.",
        "3.225 perfiles: 199,24 cm y 213,36 lb",
        "Lakers registra la mayor racha histórica (33)",
        "11 pruebas · 89,92%",
    ):
        require(phrase in source_text, f"Story evidence is missing: {phrase}")
    require(
        source_text.count("PREGUNTA  ¿") == 4, "The report must contain four analytical questions"
    )
    require(source_text.count("HALLAZGO CLAVE") == 4, "The report must contain four takeaways")
    require(
        "ENTREGABLES PARA REPRODUCIBILIDAD Y REVISIÓN TÉCNICA" in source_text,
        "Reviewer handoff is missing",
    )

    theme = read_json(
        PROJECT / "StaticResources" / "RegisteredResources" / "Custom0009385818418090608.json"
    )
    require(theme["name"] == "NBA Executive Story", "Unexpected report theme")
    require(theme["dataColors"][:3] == ["#1D4ED8", "#F28C28", "#38BDF8"], "Palette changed")


def validate_visual_semantics() -> None:
    cover = SECTIONS / "000_Inicio" / "visualContainers"
    require(position(cover / "07000_SoyHenry")[0] >= 1400, "Henry branding remains visible")
    require(position(cover / "03000_Menú Análisis")[0] >= 1400, "Legacy menu remains visible")
    require(
        position(cover / "09000_image (40f57)") == (1000, 132, 220, 220),
        "The user-selected analytics mark is not in the approved hero position",
    )

    for page_name in PAGE_IDS:
        page = SECTIONS / page_name / "visualContainers"
        for index, (target_page, label) in enumerate(NAV_ITEMS):
            directory = page / f"90000_nav_{index:02d}"
            require(directory.is_dir(), f"Navigation item is missing: {page_name}/{label}")
            config = read_json(directory / "config.json")
            visual = config["singleVisual"]
            require(visual["visualType"] == "actionButton", f"Invalid nav type: {label}")
            text_value = visual["objects"]["text"][1]["properties"]["text"]["expr"][
                "Literal"
            ]["Value"].strip("'")
            target = visual["vcObjects"]["visualLink"][0]["properties"][
                "navigationSection"
            ]["expr"]["Literal"]["Value"].strip("'")
            require(text_value == label, f"Unexpected navigation label: {text_value}")
            require(target == PAGE_IDS[target_page], f"Wrong navigation target: {label}")
            require(
                position(directory) == (360 + index * 150, 14, 146, 38),
                f"Navigation geometry changed: {page_name}/{label}",
            )

        for directory in page.iterdir():
            if not directory.is_dir() or directory.name.startswith("90000_nav_"):
                continue
            config = read_json(directory / "config.json")
            if config.get("singleVisual", {}).get("visualType") == "actionButton":
                require(position(directory)[0] >= 1400, f"Legacy action remains: {directory}")

    public_layouts = {
        "001_Análisis_1": [
            "16000_Titulo",
            "20000_story_question",
            "03000_Rendimiento histórico de las franquicias NBA",
            "08000_advancedSlicerVisual (34242)",
            "21000_story_answer",
            "04000_Evolución del promedio de puntos por partido en la NBA",
            "05000_Rendimiento en función de la Antiguedad",
        ],
        "002_Análisis_2": [
            "02000_Titulo",
            "20000_story_question",
            "08000_Consistencia histórica de las franquicias de NBA",
            "10000_advancedSlicerVisual (b0ea8)",
            "09000_advancedSlicerVisual (fa73f)",
            "21000_story_answer",
            "04000_Desempeño -%3E  Local vs Visitante",
            "07000_Eficiencia de Tiro vs Pérdidas de balón",
        ],
        "003_Análisis_3": [
            "15000_Titulo",
            "20000_story_question",
            "05000_Eficiencia ofensiva de equipos NBA",
            "03000_Perfil físico promedio de los equipos NBA",
            "08000_advancedSlicerVisual (a910c)",
            "21000_story_answer",
        ],
    }
    for page, folders in public_layouts.items():
        require_no_overlap(page, folders)

    for page, folders in {
        "001_Análisis_1": ["10000_Tarjetas"],
        "002_Análisis_2": ["14000_Tarjeta1", "15000_Tarjeta1", "16000_Tarjeta1"],
        "003_Análisis_3": ["17000_Tarjeta1", "18000_Tarjeta1", "19000_Tarjeta1"],
    }.items():
        for folder in folders:
            require(
                position(SECTIONS / page / "visualContainers" / folder)[0] >= 1400,
                f"Redundant KPI group remains visible: {page}/{folder}",
            )

    slicer_fields = {
        "001_Análisis_1/08000_advancedSlicerVisual (34242)": (
            "Franquicia",
            "team_name",
        ),
        "002_Análisis_2/10000_advancedSlicerVisual (b0ea8)": (
            "Década de temporada",
            "decade",
        ),
        "002_Análisis_2/09000_advancedSlicerVisual (fa73f)": (
            "Franquicia",
            "team_name",
        ),
        "003_Análisis_3/08000_advancedSlicerVisual (a910c)": (
            "Franquicia",
            "team_name",
        ),
    }
    for relative, (expected, technical) in slicer_fields.items():
        page, folder = relative.split("/", 1)
        directory = SECTIONS / page / "visualContainers" / folder
        require(
            visible_title(directory) == expected,
            f"Business slicer label changed: {relative}",
        )
        slicer = read_json(directory / "config.json")["singleVisual"]
        title_state = slicer["vcObjects"]["title"][0]["properties"]["show"][
            "expr"
        ]["Literal"]["Value"]
        require(
            title_state == "false",
            f"Duplicate visual title remains visible: {relative}",
        )
        require(
            all(
                "show" not in item.get("properties", {})
                for item in slicer.get("objects", {}).get("value", [])
            ),
            f"Unsupported slicer header override remains: {relative}",
        )
        slicer_text = "\n".join(
            path.read_text(encoding="utf-8-sig")
            for path in directory.glob("*.json")
        )
        require(
            f'"Property": "{expected}"' in slicer_text,
            f"Business model field is missing: {relative}",
        )
        require(
            f'analytics vw_teams.{technical}' not in slicer_text
            and f'analytics dim_season.{technical}' not in slicer_text,
            f"Technical slicer model reference remains: {relative}",
        )

    teams_model = (MODEL / "tables" / "analytics vw_teams.tmdl").read_text(
        encoding="utf-8"
    )
    season_model = (MODEL / "tables" / "analytics dim_season.tmdl").read_text(
        encoding="utf-8"
    )
    relationships = (MODEL / "relationships.tmdl").read_text(encoding="utf-8")
    require("\tcolumn Franquicia\n" in teams_model, "Business team field is missing")
    require("\tsourceColumn: team_name\n" in teams_model, "Team source mapping changed")
    require(
        "\tcolumn 'Década de temporada'\n" in season_model,
        "Business decade field is missing",
    )
    require("\tsourceColumn: decade\n" in season_model, "Decade source mapping changed")
    require(
        "'analytics vw_teams'.team_name" not in relationships
        and "'analytics dim_season'.decade" not in relationships,
        "Technical model relationship remains",
    )
    history_slicer = read_json(
        SECTIONS
        / "001_Análisis_1"
        / "visualContainers"
        / "08000_advancedSlicerVisual (34242)"
        / "config.json"
    )["singleVisual"]
    require(
        set(history_slicer["projections"]) == {"Values"},
        "The history slicer still contains an inherited tooltip",
    )
    require(
        [item["Entity"] for item in history_slicer["prototypeQuery"]["From"]]
        == ["analytics vw_teams"],
        "The history slicer depends on more than the team dimension",
    )

    q3_query = read_json(
        SECTIONS
        / "003_Análisis_3"
        / "visualContainers"
        / "05000_Eficiencia ofensiva de equipos NBA"
        / "query.json"
    )
    q3_counts: list[int] = []

    def collect_window_counts(value: object) -> None:
        if isinstance(value, dict):
            window = value.get("Window")
            if isinstance(window, dict) and isinstance(window.get("Count"), int):
                q3_counts.append(window["Count"])
            for child in value.values():
                collect_window_counts(child)
        elif isinstance(value, list):
            for child in value:
                collect_window_counts(child)

    collect_window_counts(q3_query)
    require(12 in q3_counts, f"The offensive chart is not limited to Top 12: {q3_counts}")
    analytics_sql = (ROOT / "CODE" / "SQL" / "20_analytics_views.sql").read_text(
        encoding="utf-8"
    )
    require("ROW_NUMBER() OVER" in analytics_sql, "q3 SQL ranking is missing")
    require(
        "performance.offensive_rank <= 12" in analytics_sql,
        "q3 SQL does not enforce the displayed Top 12",
    )

    q7 = (
        SECTIONS
        / "002_Análisis_2"
        / "visualContainers"
        / "07000_Eficiencia de Tiro vs Pérdidas de balón"
    )
    q7_config = read_json(q7 / "config.json")
    require(q7_config["singleVisual"]["visualType"] == "scatterChart", "q7 is not a scatter plot")
    projections = q7_config["singleVisual"]["projections"]
    require(
        projections["X"][0]["queryRef"].endswith("tov_avg)"),
        "q7 x-axis is not turnovers per game",
    )
    require(
        projections["Y"][0]["queryRef"].endswith("fg_pct_avg)"),
        "q7 y-axis is not shooting efficiency",
    )
    for query in find_queries(q7_config):
        entities = [item["Entity"] for item in query["From"]]
        require(
            entities == ["analytics vw_q7_balance_of_def"], f"q7 has redundant sources: {entities}"
        )

    direct_visuals = {
        "001_Análisis_1/03000_Rendimiento histórico de las franquicias NBA": "analytics vw_q1_hist_perf",
        "001_Análisis_1/05000_Rendimiento en función de la Antiguedad": "analytics vw_q2_age_vs_current",
        "002_Análisis_2/04000_Desempeño -%3E  Local vs Visitante": "analytics vw_q6_home_away_impact",
        "002_Análisis_2/08000_Consistencia histórica de las franquicias de NBA": "analytics vw_q5_consistency",
        "003_Análisis_3/03000_Perfil físico promedio de los equipos NBA": "analytics vw_q9_physical_profile",
        "003_Análisis_3/05000_Eficiencia ofensiva de equipos NBA": "analytics vw_q3_player_context_offense",
        "004_Insights/11000_Racha histórica": "analytics vw_q8_longest_win_streak",
        "004_Insights/12000_Rendimiento reciente": "analytics vw_q10_recent_top",
    }
    for relative, entity in direct_visuals.items():
        config = read_json(
            SECTIONS
            / relative.split("/", 1)[0]
            / "visualContainers"
            / relative.split("/", 1)[1]
            / "config.json"
        )
        for query in find_queries(config):
            entities = {item["Entity"] for item in query["From"]}
            require("analytics vw_teams" not in entities, f"Hidden team join remains: {relative}")
            require(entity in entities, f"Expected source missing for {relative}: {entities}")

    q4_path = (
        SECTIONS
        / "001_Análisis_1"
        / "visualContainers"
        / "04000_Evolución del promedio de puntos por partido en la NBA"
        / "config.json"
    )
    q4 = read_json(q4_path)["singleVisual"]["prototypeQuery"]
    require(q4["OrderBy"][0]["Direction"] == 1, "Decades are not ascending")
    require(
        q4["OrderBy"][0]["Expression"]["Column"]["Property"] == "decade",
        "The scoring trend is not ordered by decade",
    )
    require(
        "plotArea" not in read_json(q4_path)["singleVisual"]["objects"],
        "Decorative plot image remains",
    )


def validate_snapshot() -> None:
    snapshot = read_json(SNAPSHOT)
    require(snapshot["scope"]["first_season"] == 1946, "Story scope start changed")
    require(snapshot["scope"]["last_season"] == 2022, "Story scope end changed")
    require(snapshot["scope"]["unique_games"] == 65_642, "Story game count changed")
    require(snapshot["history"]["leader"]["win_rate_pct"] == 59.53, "History leader changed")
    require(snapshot["efficiency"]["home_ppg_advantage"] == 3.58, "Home advantage changed")
    require(snapshot["profile"]["player_profiles"] == 3_225, "Profile sample changed")
    require(snapshot["peak_and_recent"]["longest_streak"]["wins"] == 33, "Streak changed")


def validate_pbit() -> None:
    require(PBIT.stat().st_size == EXPECTED_PBIT_BYTES, "PBIT byte size changed")
    digest = hashlib.sha256(PBIT.read_bytes()).hexdigest().upper()
    require(digest == EXPECTED_PBIT_SHA256, "PBIT hash changed")
    with zipfile.ZipFile(PBIT) as archive:
        require(archive.testzip() is None, "PBIT ZIP member is corrupt")
        layout = json.loads(archive.read("Report/Layout").decode("utf-16"))
    pages = {item["displayName"]: item["ordinal"] for item in layout["sections"]}
    require(pages == EXPECTED_PAGES, f"Unexpected compiled page order: {pages}")
    raw_layout = json.dumps(layout, ensure_ascii=False)
    require(raw_layout.count("PREGUNTA  ¿") == 4, "Compiled PBIT lacks the four questions")
    require(raw_layout.count("HALLAZGO CLAVE") == 4, "Compiled PBIT lacks the four takeaways")
    require("scatterChart" in raw_layout, "Compiled PBIT lacks the q7 scatter plot")


def main() -> int:
    try:
        validate_pages()
        validate_json_and_story()
        validate_visual_semantics()
        validate_snapshot()
        validate_pbit()
    except (AssertionError, KeyError, OSError, ValueError, zipfile.BadZipFile) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(
        json.dumps(
            {
                "status": "passed",
                "pages": 6,
                "analytical_questions": 4,
                "visual_json_files": len(list((PROJECT / "Report").rglob("*.json"))),
                "pbit_bytes": EXPECTED_PBIT_BYTES,
                "pbit_sha256": EXPECTED_PBIT_SHA256,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
