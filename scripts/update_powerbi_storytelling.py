# ruff: noqa: E501, RUF001
"""Apply the reproducible visual-storytelling redesign to the NBA report.

The script only edits the extracted pbi-tools project.  It keeps the data model
and DirectQuery source unchanged, while making the visual layer auditable:

* one analytical question and one unfiltered takeaway per page;
* consistent page order, titles, periods and units;
* a restrained NBA-inspired palette and fewer decorative elements;
* a scatter plot for shooting efficiency versus turnovers (two real units);
* single-view category references so visuals do not depend on hidden joins.

The final English stage is applied at the end of main() from the reviewed
editorial contract. Regenerating this script must not revert public copy to ES.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "CODE" / "Dashboard - POWERBI" / "Analisis_NBA_BestTeam"
REPORT = PROJECT / "Report"
SECTIONS = REPORT / "sections"
MODEL = PROJECT / "Model"
THEME = PROJECT / "StaticResources" / "RegisteredResources" / "Custom0009385818418090608.json"

PAGES = {
    "000_Inicio": "Inicio",
    "001_Análisis_1": "01 · Panorama histórico",
    "002_Análisis_2": "02 · Ventaja y estabilidad",
    "003_Análisis_3": "03 · Perfil y ofensiva",
    "004_Insights": "04 · Pico y actualidad",
    "006_Conclusión": "05 · Método y evidencia",
}

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

COLORS = {
    "ink": "#0F172A",
    "navy": "#0B132B",
    "blue": "#1D4ED8",
    "sky": "#38BDF8",
    "orange": "#F28C28",
    "orange_soft": "#FFF4E5",
    "paper": "#FFFFFF",
    "canvas": "#F3F6FB",
    "muted": "#64748B",
    "line": "#DCE3EE",
    "green": "#15803D",
    "red": "#C2413B",
}

COLOR_REPLACEMENTS = {
    "#AF1111": COLORS["orange"],
    "#AC0E0E": COLORS["orange"],
    "#D64550": COLORS["red"],
    "#EB895F": "#FDBA74",
    "#194296": COLORS["blue"],
    "#234CB4": COLORS["blue"],
    "#093EA6": COLORS["blue"],
    "#0E1A77": COLORS["navy"],
    "#1888EF": COLORS["sky"],
    "#8299C7": "#93C5FD",
    "#6275A7": "#60A5FA",
    "#5D76BB": "#60A5FA",
    "#E1C233": COLORS["orange"],
}

TEXT_REPLACEMENTS = {
    "DATA - ANALYTICS  N B A": "NBA ANALYTICS · PORTFOLIO",
    "powered by:SoyHenry": "PORTFOLIO · DATA ANALYTICS",
    "Eficiencia y consistencia 🔄": "02 · Ventaja y estabilidad",
    "Talento y perfil 🧠": "03 · Perfil y ofensiva",
    "Historia y evolución": "01 · Panorama histórico",
    "Eficiencia y consistencia": "02 · Ventaja y estabilidad",
    "Talento y perfil": "03 · Perfil y ofensiva",
    "Rachas y actualidad": "04 · Pico y actualidad",
    "🏠": "INICIO",
    "🏁": "MÉTODO",
    "ℹ️": "INFO",
    "⭐": "",
    "🔺": "",
}


def read_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: object) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8-sig") == text:
        return
    path.write_text(text, encoding="utf-8", newline="\n")


def literal(value: str | bool | int | float) -> dict:
    if isinstance(value, bool):
        encoded = "true" if value else "false"
    elif isinstance(value, str):
        encoded = f"'{value}'"
    elif isinstance(value, int):
        encoded = f"{value}L"
    else:
        encoded = f"{value}D"
    return {"expr": {"Literal": {"Value": encoded}}}


def solid(color: str) -> dict:
    return {"solid": {"color": literal(color)}}


def replace_strings(value: object) -> object:
    if isinstance(value, str):
        for old, new in COLOR_REPLACEMENTS.items():
            value = value.replace(old, new).replace(old.lower(), new)
        return value
    if isinstance(value, list):
        return [replace_strings(item) for item in value]
    if isinstance(value, dict):
        return {key: replace_strings(item) for key, item in value.items()}
    return value


def set_position(
    directory: Path,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    z: int | None = None,
) -> None:
    config_path = directory / "config.json"
    config = read_json(config_path)
    position = config["layouts"][0]["position"]
    position.update({"x": x, "y": y, "width": width, "height": height})
    if z is not None:
        position["z"] = z
    write_json(config_path, config)

    container_path = directory / "visualContainer.json"
    if container_path.exists():
        container = read_json(container_path)
        container.update({"x": x, "y": y, "width": width, "height": height})
        if z is not None:
            container["z"] = z
        write_json(container_path, container)


def set_page_background(page: Path) -> None:
    config_path = page / "config.json"
    config = read_json(config_path)
    config["objects"] = {
        "background": [
            {
                "properties": {
                    "transparency": literal(0.0),
                    "color": solid(COLORS["canvas"]),
                }
            }
        ]
    }
    write_json(config_path, config)


def set_textbox(
    directory: Path,
    text: str,
    *,
    font_size: int,
    color: str,
    weight: str = "normal",
    align: str = "left",
) -> None:
    path = directory / "config.json"
    config = read_json(path)
    config["singleVisual"]["objects"]["general"][0]["properties"]["paragraphs"] = [
        {
            "textRuns": [
                {
                    "value": text,
                    "textStyle": {
                        "fontFamily": "Segoe UI",
                        "fontSize": f"{font_size}pt",
                        "fontWeight": weight,
                        "color": color,
                    },
                }
            ],
            "horizontalTextAlignment": align,
        }
    ]
    write_json(path, config)


def create_textbox(
    page: Path,
    folder: str,
    paragraphs: list[tuple[str, int, str, str]],
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    background: str | None = None,
    align: str = "left",
    z: int = 30000,
) -> None:
    directory = page / "visualContainers" / folder
    directory.mkdir(parents=True, exist_ok=True)
    visual_id = hashlib.sha1(f"{page.name}/{folder}".encode()).hexdigest()[:20]
    runs = []
    for text, size, color, weight in paragraphs:
        runs.append(
            {
                "textRuns": [
                    {
                        "value": text,
                        "textStyle": {
                            "fontFamily": "Segoe UI",
                            "fontSize": f"{size}pt",
                            "fontWeight": weight,
                            "color": color,
                        },
                    }
                ],
                "horizontalTextAlignment": align,
            }
        )
    config = {
        "name": visual_id,
        "layouts": [
            {
                "id": 0,
                "position": {
                    "x": x,
                    "y": y,
                    "z": z,
                    "width": width,
                    "height": height,
                    "tabOrder": z,
                },
            }
        ],
        "singleVisual": {
            "visualType": "textbox",
            "drillFilterOtherVisuals": True,
            "objects": {"general": [{"properties": {"paragraphs": runs}}]},
            "vcObjects": {
                "background": [
                    {
                        "properties": {
                            "show": literal(background is not None),
                            **(
                                {
                                    "color": solid(background),
                                    "transparency": literal(0.0),
                                }
                                if background
                                else {}
                            ),
                        }
                    }
                ],
                "border": [
                    {
                        "properties": {
                            "show": literal(background is not None),
                            "color": solid(COLORS["line"]),
                            "radius": literal(10.0),
                        }
                    }
                ],
            },
        },
    }
    write_json(directory / "config.json", config)
    write_json(
        directory / "visualContainer.json",
        {
            "height": height,
            "tabOrder": z,
            "width": width,
            "x": x,
            "y": y,
            "z": z,
        },
    )
    write_json(directory / "filters.json", [])


def style_visual(directory: Path) -> None:
    path = directory / "config.json"
    if not path.exists():
        return
    config = read_json(path)
    visual = config.get("singleVisual")
    if not visual:
        return
    visual_type = visual.get("visualType")
    if visual_type in {"textbox", "shape", "image", "actionButton"}:
        return
    vc = visual.setdefault("vcObjects", {})
    vc["background"] = [
        {
            "properties": {
                "show": literal(True),
                "color": solid(COLORS["paper"]),
                "transparency": literal(0.0),
            }
        }
    ]
    vc["border"] = [
        {
            "properties": {
                "show": literal(True),
                "color": solid(COLORS["line"]),
                "radius": literal(10.0),
            }
        }
    ]
    vc["visualHeader"] = [{"properties": {"show": literal(False)}}]
    vc["dropShadow"] = [{"properties": {"show": literal(False)}}]
    if vc.get("title") and visual_type != "slicer":
        properties = vc["title"][0].setdefault("properties", {})
        properties["show"] = literal(True)
        properties["fontSize"] = literal(12.0)
        properties["fontFamily"] = literal("Segoe UI Semibold")
        properties["fontColor"] = solid(COLORS["ink"])
    visual.get("objects", {}).pop("plotArea", None)
    write_json(path, config)


def set_chart_title(directory: Path, text: str) -> None:
    path = directory / "config.json"
    config = read_json(path)
    vc = config["singleVisual"].setdefault("vcObjects", {})
    title = vc.setdefault("title", [{"properties": {}}])
    if not title:
        title.append({"properties": {}})
    properties = title[0].setdefault("properties", {})
    properties.update(
        {
            "text": literal(text),
            "show": literal(True),
            "fontSize": literal(12.0),
            "fontFamily": literal("Segoe UI Semibold"),
            "fontColor": solid(COLORS["ink"]),
        }
    )
    write_json(path, config)


def hide_visual(directory: Path) -> None:
    """Move one exact legacy visual or group outside the report canvas."""

    if directory.exists():
        set_position(directory, x=1500, y=900, width=10, height=10)


def rename_visible_field(directory: Path, source_label: str, display_label: str) -> None:
    """Rename user-facing field captions without changing the model column."""

    visible_keys = {"NativeReferenceName", "Restatement", "displayName"}

    def rename(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in visible_keys and child == source_label:
                    value[key] = display_label
                else:
                    rename(child)
        elif isinstance(value, list):
            for child in value:
                rename(child)

    for filename in ("config.json", "query.json", "dataTransforms.json"):
        path = directory / filename
        if path.exists():
            payload = read_json(path)
            rename(payload)
            write_json(path, payload)


def use_business_slicer_header(directory: Path) -> None:
    """Use the renamed model field as the one visible slicer heading."""

    config_path = directory / "config.json"
    config = read_json(config_path)
    for item in config["singleVisual"].get("objects", {}).get("value", []):
        item.get("properties", {}).pop("show", None)
    title = config["singleVisual"].setdefault("vcObjects", {}).setdefault(
        "title", [{"properties": {}}]
    )
    title[0].setdefault("properties", {})["show"] = literal(False)
    write_json(config_path, config)

    transforms_path = directory / "dataTransforms.json"
    if transforms_path.exists():
        transforms = read_json(transforms_path)
        for item in transforms.get("objects", {}).get("value", []):
            item.get("properties", {}).pop("show", None)
        write_json(transforms_path, transforms)


def keep_only_slicer_value(directory: Path, query_ref: str, entity: str) -> None:
    """Remove inherited tooltip fields so a slicer depends on one business column."""

    config_path = directory / "config.json"
    config = read_json(config_path)
    visual = config["singleVisual"]
    visual["projections"] = {"Values": [{"queryRef": query_ref}]}
    prototype = visual["prototypeQuery"]
    prototype["From"] = [item for item in prototype["From"] if item["Entity"] == entity]
    prototype["Select"] = [item for item in prototype["Select"] if item["Name"] == query_ref]
    write_json(config_path, config)

    query_path = directory / "query.json"
    query = read_json(query_path)
    command = query["Commands"][0]["SemanticQueryDataShapeCommand"]
    semantic_query = command["Query"]
    semantic_query["From"] = [
        item for item in semantic_query["From"] if item["Entity"] == entity
    ]
    semantic_query["Select"] = [
        item for item in semantic_query["Select"] if item["Name"] == query_ref
    ]
    binding = command["Binding"]
    binding["Primary"]["Groupings"][0]["Projections"] = [0]
    binding.pop("SuppressedJoinPredicates", None)
    write_json(query_path, query)

    transforms_path = directory / "dataTransforms.json"
    transforms = read_json(transforms_path)
    transforms["projectionOrdering"] = {"Values": [0]}
    transforms["queryMetadata"]["Select"] = [
        item for item in transforms["queryMetadata"]["Select"] if item["Name"] == query_ref
    ]
    transforms["selects"] = [
        item for item in transforms["selects"] if item["queryName"] == query_ref
    ]
    transforms["visualElements"][0]["DataRoles"] = [
        {"Name": "Values", "Projection": 0, "isActive": False}
    ]
    write_json(transforms_path, transforms)


def rename_slicer_model_columns() -> None:
    """Replace technical slicer captions with stable business-facing names."""

    table_replacements = {
        MODEL / "tables" / "analytics vw_teams.tmdl": (
            "\tcolumn team_name\n",
            "\tcolumn Team\n",
        ),
        MODEL / "tables" / "analytics dim_season.tmdl": (
            "\tcolumn decade\n",
            "\tcolumn 'Season decade'\n",
        ),
    }
    for path, (old, new) in table_replacements.items():
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")

    relationships = MODEL / "relationships.tmdl"
    text = relationships.read_text(encoding="utf-8")
    text = text.replace("'analytics vw_teams'.team_name", "'analytics vw_teams'.Team")
    text = text.replace(
        "'analytics dim_season'.decade",
        "'analytics dim_season'.'Season decade'",
    )
    relationships.write_text(text, encoding="utf-8", newline="\n")

    slicers = {
        SECTIONS
        / "001_Análisis_1"
        / "visualContainers"
        / "08000_advancedSlicerVisual (34242)": (
            "analytics vw_teams",
            "team_name",
            "Team",
        ),
        SECTIONS
        / "002_Análisis_2"
        / "visualContainers"
        / "09000_advancedSlicerVisual (fa73f)": (
            "analytics vw_teams",
            "team_name",
            "Team",
        ),
        SECTIONS
        / "003_Análisis_3"
        / "visualContainers"
        / "08000_advancedSlicerVisual (a910c)": (
            "analytics vw_teams",
            "team_name",
            "Team",
        ),
        SECTIONS
        / "002_Análisis_2"
        / "visualContainers"
        / "10000_advancedSlicerVisual (b0ea8)": (
            "analytics dim_season",
            "decade",
            "Season decade",
        ),
    }

    def rename(value: object, entity: str, old: str, new: str) -> object:
        if isinstance(value, str):
            return value.replace(f"{entity}.{old}", f"{entity}.{new}")
        if isinstance(value, list):
            return [rename(item, entity, old, new) for item in value]
        if isinstance(value, dict):
            updated = {
                key: rename(item, entity, old, new) for key, item in value.items()
            }
            if updated.get("Property") == old:
                updated["Property"] = new
            return updated
        return value

    for directory, (entity, old, new) in slicers.items():
        for filename in ("config.json", "query.json", "dataTransforms.json", "filters.json"):
            path = directory / filename
            if path.exists():
                write_json(path, rename(read_json(path), entity, old, new))


def set_primary_window(directory: Path, count: int) -> None:
    """Limit a sorted categorical visual to a deliberate, readable window."""

    path = directory / "query.json"
    payload = read_json(path)

    def update(value: object) -> None:
        if isinstance(value, dict):
            data_reduction = value.get("DataReduction")
            if isinstance(data_reduction, dict):
                primary = data_reduction.get("Primary")
                if isinstance(primary, dict) and isinstance(primary.get("Window"), dict):
                    primary["Window"]["Count"] = count
            for child in value.values():
                update(child)
        elif isinstance(value, list):
            for child in value:
                update(child)

    update(payload)
    write_json(path, payload)


def set_page_navigation_button(directory: Path, text: str, section_id: str) -> None:
    """Replace the legacy bookmark menu with a direct page action."""

    path = directory / "config.json"
    config = read_json(path)
    visual = config.get("singleVisual", {})
    for state in visual.get("objects", {}).get("text", []):
        properties = state.get("properties", {})
        if "text" in properties:
            properties["text"] = literal(text)
    link = visual.setdefault("vcObjects", {}).setdefault(
        "visualLink", [{"properties": {}}]
    )
    properties = link[0].setdefault("properties", {})
    properties.update(
        {
            "show": literal(True),
            "type": literal("PageNavigation"),
            "tooltip": literal("Abrir panorama histórico"),
            "showDefaultTooltip": literal(False),
            "navigationSection": literal(section_id),
        }
    )
    properties.pop("bookmark", None)
    write_json(path, config)


def create_navigation_button(
    page: Path,
    folder: str,
    text: str,
    section_id: str,
    *,
    x: float,
    active: bool,
) -> None:
    """Create one text-first, image-free page-navigation button."""

    directory = page / "visualContainers" / folder
    directory.mkdir(parents=True, exist_ok=True)
    visual_id = hashlib.sha1(f"{page.name}/{folder}".encode()).hexdigest()[:20]
    color = COLORS["orange"] if active else "#F8FAFC"
    z = 49000
    config = {
        "name": visual_id,
        "layouts": [
            {
                "id": 0,
                "position": {
                    "x": x,
                    "y": 14,
                    "z": z,
                    "width": 146,
                    "height": 38,
                    "tabOrder": z,
                },
            }
        ],
        "singleVisual": {
            "visualType": "actionButton",
            "drillFilterOtherVisuals": True,
            "objects": {
                "icon": [
                    {
                        "properties": {"shapeType": literal("blank")},
                        "selector": {"id": "default"},
                    }
                ],
                "shape": [
                    {
                        "properties": {"tileShape": literal("rectangleRounded")},
                        "selector": {"id": "default"},
                    }
                ],
                "fill": [{"properties": {"show": literal(False)}}],
                "outline": [{"properties": {"show": literal(False)}}],
                "text": [
                    {"properties": {"show": literal(True)}},
                    {
                        "properties": {
                            "text": literal(text),
                            "fontColor": solid(color),
                            "fontFamily": literal("Segoe UI Semibold"),
                            "fontSize": literal(9.0 if active else 8.0),
                            "bold": literal(True),
                            "horizontalAlignment": literal("center"),
                            "verticalAlignment": literal("middle"),
                            "topMargin": literal(0),
                            "bottomMargin": literal(0),
                            "leftMargin": literal(0),
                            "rightMargin": literal(0),
                        },
                        "selector": {"id": "default"},
                    },
                ],
            },
            "vcObjects": {
                "visualLink": [
                    {
                        "properties": {
                            "show": literal(True),
                            "type": literal("PageNavigation"),
                            "tooltip": literal(f"Abrir {text.lower()}"),
                            "showDefaultTooltip": literal(False),
                            "navigationSection": literal(section_id),
                        }
                    }
                ],
                "visualHeader": [{"properties": {"show": literal(False)}}],
            },
        },
        "howCreated": "InsertVisualButton",
    }
    write_json(directory / "config.json", config)
    write_json(
        directory / "visualContainer.json",
        {
            "height": 38,
            "tabOrder": z,
            "width": 146,
            "x": x,
            "y": 14,
            "z": z,
        },
    )
    write_json(directory / "filters.json", [])


def add_navigation_bar() -> None:
    """Retire the mixed bookmark header and add six direct page actions."""

    for page_name, _display_name in PAGES.items():
        page = SECTIONS / page_name
        visuals = page / "visualContainers"

        # Keep only the full-width header layer, NBA mark and portfolio label.
        # Everything else located in the old 84 px header is legacy navigation.
        for directory in sorted(visuals.iterdir()):
            if not directory.is_dir() or directory.name.startswith("90000_nav_"):
                continue
            config_path = directory / "config.json"
            if not config_path.exists():
                continue
            config = read_json(config_path)
            position = config.get("layouts", [{}])[0].get("position", {})
            x = float(position.get("x", 0))
            y = float(position.get("y", 0))
            width = float(position.get("width", 0))
            height = float(position.get("height", 0))
            visual_type = config.get("singleVisual", {}).get("visualType")
            group_name = str(
                config.get("singleVisualGroup", {}).get("displayName", "")
            ).lower()
            if visual_type == "actionButton" or any(
                token in group_name for token in ("botón", "menu", "menú")
            ):
                hide_visual(directory)
                continue
            if y >= 85 or height <= 0:
                continue
            keep = (
                (visual_type == "image" and (width >= 1000 or width <= 110))
                or (visual_type == "textbox" and 80 <= x <= 120 and width <= 220)
                or ("singleVisualGroup" in config and width >= 1000)
            )
            if not keep:
                hide_visual(directory)

        for index, (target_page, label) in enumerate(NAV_ITEMS):
            create_navigation_button(
                page,
                f"90000_nav_{index:02d}",
                label,
                PAGE_IDS[target_page],
                x=360 + index * 150,
                active=target_page == page_name,
            )


def rewrite_text_runs() -> None:
    for path in sorted(SECTIONS.rglob("config.json")):
        config = read_json(path)

        def visit(value: object) -> None:
            if isinstance(value, dict):
                if "value" in value and isinstance(value["value"], str):
                    text = value["value"]
                    for old, new in TEXT_REPLACEMENTS.items():
                        text = text.replace(old, new)
                    value["value"] = text
                for item in value.values():
                    visit(item)
            elif isinstance(value, list):
                for item in value:
                    visit(item)

        visit(config)
        write_json(path, config)


def style_header_labels() -> None:
    for path in sorted(SECTIONS.rglob("config.json")):
        config = read_json(path)
        visual = config.get("singleVisual", {})
        if visual.get("visualType") != "textbox":
            continue
        paragraphs = (
            visual.get("objects", {})
            .get("general", [{}])[0]
            .get("properties", {})
            .get("paragraphs", [])
        )
        text = "".join(
            str(run.get("value", ""))
            for paragraph in paragraphs
            for run in paragraph.get("textRuns", [])
        ).strip()
        if text == "NBA ANALYTICS · PORTFOLIO":
            size, color, weight = 11, COLORS["paper"], "bold"
        elif text in {"INICIO", "MÉTODO", "INFO"}:
            size, color, weight = 8, COLORS["paper"], "bold"
        elif text == "PORTFOLIO · DATA ANALYTICS":
            size, color, weight = 8, "#CBD5E1", "normal"
        else:
            continue
        for paragraph in paragraphs:
            paragraph["horizontalTextAlignment"] = "center"
            for run in paragraph.get("textRuns", []):
                run["textStyle"] = {
                    "fontFamily": "Segoe UI",
                    "fontSize": f"{size}pt",
                    "fontWeight": weight,
                    "color": color,
                }
        write_json(path, config)


def sort_decades_chronologically() -> None:
    path = (
        SECTIONS
        / "001_Análisis_1"
        / "visualContainers"
        / "04000_Evolución del promedio de puntos por partido en la NBA"
        / "config.json"
    )
    config = read_json(path)
    query = config["singleVisual"]["prototypeQuery"]
    source = next(
        item["Name"] for item in query["From"] if item["Entity"] == "analytics vw_q4_ppg_by_decade"
    )
    query["OrderBy"] = [
        {
            "Direction": 1,
            "Expression": {
                "Column": {
                    "Expression": {"SourceRef": {"Source": source}},
                    "Property": "decade",
                }
            },
        }
    ]
    write_json(path, config)


def normalize_visual_team_source(directory: Path, entity: str) -> None:
    """Use ``team_name`` from the analytical view itself.

    The canonical views already expose this label, so visuals do not need a
    second table or a hidden relationship merely to render a category.
    """

    def normalize(payload: object) -> object:
        if isinstance(payload, str):
            return payload.replace("analytics vw_teams.team_name", f"{entity}.team_name")
        if isinstance(payload, list):
            return [normalize(item) for item in payload]
        if not isinstance(payload, dict):
            return payload

        updated = {key: normalize(item) for key, item in payload.items()}
        sources = updated.get("From")
        if isinstance(sources, list):
            target_source = next(
                (source.get("Name") for source in sources if source.get("Entity") == entity),
                None,
            )
            team_source = next(
                (
                    source.get("Name")
                    for source in sources
                    if source.get("Entity") == "analytics vw_teams"
                ),
                None,
            )
            if target_source and team_source:
                updated["From"] = [
                    source for source in sources if source.get("Entity") != "analytics vw_teams"
                ]

                def swap_source(value: object) -> None:
                    if isinstance(value, dict):
                        if value.get("Source") == team_source:
                            value["Source"] = target_source
                        for child in value.values():
                            swap_source(child)
                    elif isinstance(value, list):
                        for child in value:
                            swap_source(child)

                swap_source(updated)
            current_sources = updated.get("From", sources)
            same_entity = [source for source in current_sources if source.get("Entity") == entity]
            if len(same_entity) > 1:
                preferred = same_entity[0].get("Name")
                duplicate_names = {
                    source.get("Name") for source in same_entity[1:] if source.get("Name")
                }
                updated["From"] = [
                    source
                    for source in current_sources
                    if source.get("Name") not in duplicate_names
                ]

                def collapse_source(value: object) -> None:
                    if isinstance(value, dict):
                        if value.get("Source") in duplicate_names:
                            value["Source"] = preferred
                        for child in value.values():
                            collapse_source(child)
                    elif isinstance(value, list):
                        for child in value:
                            collapse_source(child)

                collapse_source(updated)
        if updated.get("Entity") == "analytics vw_teams":
            updated["Entity"] = entity
        return updated

    for filename in ("config.json", "query.json", "dataTransforms.json"):
        path = directory / filename
        if path.exists():
            write_json(path, normalize(read_json(path)))


def convert_efficiency_to_scatter(target: Path, source: Path) -> None:
    """Reuse the proven physical-profile scatter grammar for q7."""

    target_config = read_json(target / "config.json")
    source_config = copy.deepcopy(read_json(source / "config.json"))
    source_config["name"] = target_config["name"]
    source_config["layouts"] = target_config["layouts"]
    if "parentGroupName" in target_config:
        source_config["parentGroupName"] = target_config["parentGroupName"]
    source_config["howCreated"] = target_config.get("howCreated", "InsertVisual")

    mappings = {
        "analytics vw_q9_physical_profile": "analytics vw_q7_balance_of_def",
        "analytics vw_teams.team_name": "analytics vw_q7_balance_of_def.team_name",
        "avg_height": "tov_avg",
        "avg_weight": "fg_pct_avg",
        "n_players": "balance_score",
        "altura promedio en cm": "Pérdidas por partido",
        "peso promedio en libras": "Eficiencia de tiro (FG%)",
        "average height (cm)": "Pérdidas por partido",
        "average weight (lb)": "Eficiencia de tiro (FG%)",
        "Suma de": "Promedio de",
        "Sum(analytics vw_q7_balance_of_def": "Avg(analytics vw_q7_balance_of_def",
    }

    def transform(value: object) -> object:
        if isinstance(value, str):
            for old, new in mappings.items():
                value = value.replace(old, new)
            return value
        if isinstance(value, list):
            return [transform(item) for item in value]
        if isinstance(value, dict):
            updated = {key: transform(item) for key, item in value.items()}
            if updated.get("Property") == "tov_avg":
                updated["Property"] = "Balones perdidos"
            elif updated.get("Property") == "fg_pct_avg":
                updated["Property"] = "Eficiencia de tiro"
            column = updated.get("Column")
            if isinstance(column, dict):
                source_ref = column.get("Expression", {}).get("SourceRef", {})
                prop = column.get("Property")
                if (
                    prop in {"Balones perdidos", "Eficiencia de tiro", "balance_score"}
                    and (
                        source_ref.get("Entity") == "analytics vw_q7_balance_of_def"
                        or source_ref.get("Source") in {"a1", "a"}
                    )
                    and "Aggregation" in updated
                ):
                    updated["Aggregation"]["Function"] = 1
            aggregation = updated.get("Aggregation")
            if isinstance(aggregation, dict):
                prop = aggregation.get("Expression", {}).get("Column", {}).get("Property")
                if prop in {"Balones perdidos", "Eficiencia de tiro", "balance_score"}:
                    aggregation["Function"] = 1
            return updated
        return value

    write_json(target / "config.json", transform(source_config))
    for filename in ("query.json", "dataTransforms.json"):
        write_json(target / filename, transform(read_json(source / filename)))
    write_json(target / "filters.json", [])
    normalize_visual_team_source(target, "analytics vw_q7_balance_of_def")


def hide_legacy_panels() -> None:
    targets = {
        "001_Análisis_1": ["06000_shape (cf2ba)", "07000_shape (0b7ce)"],
        "002_Análisis_2": ["05000_shape (6e0b0)", "06000_shape (9b113)"],
        "003_Análisis_3": ["06000_shape (7c406)", "07000_shape (8ad05)"],
    }
    for page_name, folders in targets.items():
        for folder in folders:
            directory = SECTIONS / page_name / "visualContainers" / folder
            if directory.exists():
                set_position(directory, x=1500, y=900, width=10, height=10)


def update_cover() -> None:
    page = SECTIONS / "000_Inicio"
    visuals = page / "visualContainers"

    # Preserve the user's manual cleanup: Henry branding is retired and the
    # bespoke analytics mark becomes part of the hero rather than a hidden
    # decoration behind other objects.
    for folder in (
        "04000_Titulo",
        "02000_Subtitulo",
        "03000_Subtitulo",
        "03000_Menú Análisis",
        "20000_story_path",
    ):
        hide_visual(visuals / folder)
    set_position(
        visuals / "09000_image (40f57)",
        x=1000,
        y=132,
        width=220,
        height=220,
        z=21000,
    )
    for folder in ("00000_Botón X", "02000_actionButton (28a9e)"):
        set_page_navigation_button(
            visuals / folder,
            "ANÁLISIS",
            "127f8fdec9d1ce997d14",
        )

    create_textbox(
        page,
        "19000_hero_title",
        [
            ("PORTFOLIO CASE STUDY", 12, COLORS["orange"], "bold"),
            ("NBA Analytics Platform", 34, COLORS["ink"], "bold"),
            (
                "De seis fuentes versionadas a una historia ejecutiva sobre rendimiento, contexto y evolución de la NBA.",
                16,
                COLORS["muted"],
                "normal",
            ),
        ],
        x=72,
        y=145,
        width=820,
        height=205,
    )
    story_cards = (
        (
            "20000_story_01",
            72,
            "01 · HISTORIA",
            "Dominio histórico y evolución anotadora",
        ),
        (
            "20100_story_02",
            374,
            "02 · CONTEXTO",
            "Localía, estabilidad y eficiencia",
        ),
        (
            "20200_story_03",
            676,
            "03 · PERFIL",
            "Contexto ofensivo y perfil físico",
        ),
        (
            "20300_story_04",
            978,
            "04 · ACTUALIDAD",
            "Pico histórico frente a ventana reciente",
        ),
    )
    for folder, x, title, description in story_cards:
        create_textbox(
            page,
            folder,
            [
                (title, 11, COLORS["orange"], "bold"),
                (description, 14, COLORS["ink"], "bold"),
            ],
            x=x,
            y=405,
            width=270,
            height=125,
            background=COLORS["paper"],
        )
    create_textbox(
        page,
        "21000_scope_badges",
        [
            (
                "6 CSV VERSIONADOS    ·    161.111 FILAS FUENTE    ·    65.642 PARTIDOS    ·    11 PRUEBAS",
                14,
                COLORS["blue"],
                "bold",
            ),
            (
                "Python ETL  →  SQL Server  →  15 objetos analíticos  →  Power BI DirectQuery",
                12,
                COLORS["muted"],
                "normal",
            ),
        ],
        x=72,
        y=576,
        width=1176,
        height=105,
        background=COLORS["paper"],
        align="center",
    )


def update_history() -> None:
    page = SECTIONS / "001_Análisis_1"
    visuals = page / "visualContainers"
    for folder in ("01000_textbox (fe1a0)", "02000_textbox (5d67d)"):
        set_textbox(
            visuals / folder,
            "01 · Panorama histórico",
            font_size=26,
            color=COLORS["ink"],
            weight="bold",
        )
    set_position(visuals / "16000_Titulo", x=24, y=88, width=1272, height=56)
    set_position(
        visuals / "03000_Rendimiento histórico de las franquicias NBA",
        x=27,
        y=204,
        width=880,
        height=300,
    )
    set_position(
        visuals / "04000_Evolución del promedio de puntos por partido en la NBA",
        x=25,
        y=524,
        width=616,
        height=225,
    )
    set_position(
        visuals / "05000_Rendimiento en función de la Antiguedad",
        x=661,
        y=524,
        width=636,
        height=225,
    )
    set_position(
        visuals / "08000_advancedSlicerVisual (34242)",
        x=927,
        y=204,
        width=372,
        height=75,
    )
    hide_visual(visuals / "10000_Tarjetas")
    hide_visual(visuals / "09000_textbox (b0213)")
    set_chart_title(visuals / "08000_advancedSlicerVisual (34242)", "Franquicia")
    rename_visible_field(
        visuals / "08000_advancedSlicerVisual (34242)", "team_name", "Franquicia"
    )
    keep_only_slicer_value(
        visuals / "08000_advancedSlicerVisual (34242)",
        "analytics vw_teams.Team",
        "analytics vw_teams",
    )
    use_business_slicer_header(visuals / "08000_advancedSlicerVisual (34242)")
    set_chart_title(
        visuals / "03000_Rendimiento histórico de las franquicias NBA",
        "Rendimiento histórico | 1946–2022 | win rate",
    )
    set_chart_title(
        visuals / "04000_Evolución del promedio de puntos por partido en la NBA",
        "Evolución anotadora | década de temporada | PPG",
    )
    set_chart_title(
        visuals / "05000_Rendimiento en función de la Antiguedad",
        "Antigüedad vs rendimiento reciente | 2020–2022 | win rate",
    )
    create_textbox(
        page,
        "20000_story_question",
        [
            (
                "PREGUNTA  ¿Quién sostuvo el mejor rendimiento y cómo evolucionó el ritmo de anotación?",
                13,
                COLORS["muted"],
                "bold",
            )
        ],
        x=24,
        y=145,
        width=1272,
        height=36,
    )
    create_textbox(
        page,
        "21000_story_answer",
        [
            ("HALLAZGO CLAVE", 10, COLORS["orange"], "bold"),
            (
                "Spurs lidera el win rate histórico: 59,53% en 4.077 partidos.",
                14,
                COLORS["ink"],
                "bold",
            ),
            (
                "El PPG de liga pasa de 76,23 (1940s) a 112,07 (2020s).",
                11,
                COLORS["muted"],
                "normal",
            ),
        ],
        x=927,
        y=303,
        width=372,
        height=164,
        background=COLORS["orange_soft"],
    )


def update_efficiency() -> None:
    page = SECTIONS / "002_Análisis_2"
    visuals = page / "visualContainers"
    for folder in ("00000_textbox (e4aa8)", "01000_textbox (90110)"):
        set_textbox(
            visuals / folder,
            "02 · Ventaja y estabilidad",
            font_size=26,
            color=COLORS["ink"],
            weight="bold",
        )
    set_position(visuals / "02000_Titulo", x=24, y=88, width=1272, height=56)
    for folder in ("14000_Tarjeta1", "15000_Tarjeta1", "16000_Tarjeta1"):
        hide_visual(visuals / folder)
    set_position(
        visuals / "08000_Consistencia histórica de las franquicias de NBA",
        x=24,
        y=198,
        width=760,
        height=287,
    )
    set_position(
        visuals / "04000_Desempeño -%3E  Local vs Visitante",
        x=24,
        y=505,
        width=616,
        height=230,
    )
    set_position(
        visuals / "07000_Eficiencia de Tiro vs Pérdidas de balón",
        x=660,
        y=505,
        width=636,
        height=230,
    )
    set_position(
        visuals / "10000_advancedSlicerVisual (b0ea8)",
        x=804,
        y=198,
        width=492,
        height=70,
    )
    set_position(
        visuals / "09000_advancedSlicerVisual (fa73f)",
        x=804,
        y=275,
        width=492,
        height=70,
    )
    set_chart_title(
        visuals / "08000_Consistencia histórica de las franquicias de NBA",
        "Estabilidad intertemporada | 1946–2022 | CV del win rate",
    )
    set_chart_title(
        visuals / "04000_Desempeño -%3E  Local vs Visitante",
        "Efecto localía | 1946–2022 | PPG local vs visitante",
    )
    set_chart_title(
        visuals / "07000_Eficiencia de Tiro vs Pérdidas de balón",
        "Eficiencia vs riesgo | 1946–2022 | FG% y pérdidas por partido",
    )
    set_chart_title(
        visuals / "10000_advancedSlicerVisual (b0ea8)", "Década de temporada"
    )
    rename_visible_field(
        visuals / "10000_advancedSlicerVisual (b0ea8)", "decade", "Década de temporada"
    )
    use_business_slicer_header(visuals / "10000_advancedSlicerVisual (b0ea8)")
    set_chart_title(visuals / "09000_advancedSlicerVisual (fa73f)", "Franquicia")
    rename_visible_field(
        visuals / "09000_advancedSlicerVisual (fa73f)", "team_name", "Franquicia"
    )
    use_business_slicer_header(visuals / "09000_advancedSlicerVisual (fa73f)")
    create_textbox(
        page,
        "20000_story_question",
        [
            (
                "PREGUNTA  ¿Cuánto cambia el desempeño por localía y qué equipos varían menos entre temporadas?",
                13,
                COLORS["muted"],
                "bold",
            )
        ],
        x=24,
        y=150,
        width=1272,
        height=36,
    )
    create_textbox(
        page,
        "21000_story_answer",
        [
            ("HALLAZGO CLAVE", 10, COLORS["orange"], "bold"),
            (
                "61,20% de victorias en casa frente a 37,36% como visitante.",
                14,
                COLORS["ink"],
                "bold",
            ),
            (
                "La localía agrega 3,58 PPG; Pelicans presenta el menor CV de win rate (20,81%).",
                11,
                COLORS["muted"],
                "normal",
            ),
        ],
        x=804,
        y=352,
        width=492,
        height=133,
        background=COLORS["orange_soft"],
    )


def update_profile() -> None:
    page = SECTIONS / "003_Análisis_3"
    visuals = page / "visualContainers"
    for folder in ("00000_textbox (6b135)", "01000_textbox (153c6)"):
        set_textbox(
            visuals / folder,
            "03 · Perfil y ofensiva",
            font_size=26,
            color=COLORS["ink"],
            weight="bold",
        )
    set_position(visuals / "15000_Titulo", x=24, y=88, width=1272, height=56)
    for folder in ("17000_Tarjeta1", "18000_Tarjeta1", "19000_Tarjeta1"):
        hide_visual(visuals / folder)
    set_position(
        visuals / "05000_Eficiencia ofensiva de equipos NBA",
        x=24,
        y=200,
        width=1272,
        height=280,
    )
    set_position(
        visuals / "03000_Perfil físico promedio de los equipos NBA",
        x=24,
        y=490,
        width=790,
        height=245,
    )
    set_position(
        visuals / "08000_advancedSlicerVisual (a910c)",
        x=834,
        y=490,
        width=462,
        height=70,
    )
    set_primary_window(visuals / "05000_Eficiencia ofensiva de equipos NBA", 12)
    set_chart_title(
        visuals / "05000_Eficiencia ofensiva de equipos NBA",
        "Top 12 contexto ofensivo | muestra histórica | PPG y FG%",
    )
    set_chart_title(
        visuals / "03000_Perfil físico promedio de los equipos NBA",
        "Perfil físico | 3.225 perfiles | altura (cm) y peso (lb)",
    )
    set_chart_title(visuals / "08000_advancedSlicerVisual (a910c)", "Franquicia")
    rename_visible_field(
        visuals / "08000_advancedSlicerVisual (a910c)", "team_name", "Franquicia"
    )
    use_business_slicer_header(visuals / "08000_advancedSlicerVisual (a910c)")
    create_textbox(
        page,
        "20000_story_question",
        [
            (
                "PREGUNTA  ¿Qué relación muestran el contexto ofensivo y el perfil físico de la muestra?",
                13,
                COLORS["muted"],
                "bold",
            )
        ],
        x=24,
        y=150,
        width=1272,
        height=36,
    )
    create_textbox(
        page,
        "21000_story_answer",
        [
            ("HALLAZGO CLAVE", 10, COLORS["orange"], "bold"),
            (
                "3.225 perfiles: 199,24 cm y 213,36 lb de promedio entre franquicias.",
                14,
                COLORS["ink"],
                "bold",
            ),
            (
                "La muestra más amplia por franquicia reúne 197 perfiles históricos.",
                11,
                COLORS["muted"],
                "normal",
            ),
        ],
        x=834,
        y=575,
        width=462,
        height=160,
        background=COLORS["orange_soft"],
    )


def update_recent() -> None:
    page = SECTIONS / "004_Insights"
    visuals = page / "visualContainers"
    for folder in ("01000_textbox (0c735)", "02000_textbox (018ef)"):
        set_textbox(
            visuals / folder,
            "04 · Pico y actualidad",
            font_size=26,
            color=COLORS["ink"],
            weight="bold",
        )
    set_position(visuals / "03000_Titulo", x=24, y=88, width=850, height=56)
    hide_visual(visuals / "00000_Subtitulo")
    set_position(
        visuals / "11000_Racha histórica",
        x=24,
        y=203,
        width=620,
        height=447,
    )
    set_position(
        visuals / "12000_Rendimiento reciente",
        x=664,
        y=203,
        width=632,
        height=447,
    )
    set_chart_title(
        visuals / "11000_Racha histórica",
        "Pico histórico | 1946–2022 | racha máxima de victorias",
    )
    set_chart_title(
        visuals / "12000_Rendimiento reciente",
        "Ventana reciente | 2013–2022 | win rate y PPG",
    )
    create_textbox(
        page,
        "20000_story_question",
        [
            (
                "PREGUNTA  ¿El pico histórico coincide con el mejor rendimiento de la última década disponible?",
                13,
                COLORS["muted"],
                "bold",
            )
        ],
        x=24,
        y=150,
        width=1272,
        height=36,
    )
    create_textbox(
        page,
        "21000_story_answer",
        [
            ("HALLAZGO CLAVE", 10, COLORS["orange"], "bold"),
            (
                "Lakers registra la mayor racha histórica (33); Warriors lidera 2013–2022 con 64,20% y 112,03 PPG.",
                13,
                COLORS["ink"],
                "bold",
            ),
        ],
        x=24,
        y=670,
        width=1272,
        height=64,
        background=COLORS["orange_soft"],
        align="center",
    )


def update_method() -> None:
    page = SECTIONS / "006_Conclusión"
    visuals = page / "visualContainers"
    set_textbox(
        visuals / "10000_textbox (dc975)",
        "05 · Método y evidencia",
        font_size=28,
        color=COLORS["ink"],
        weight="bold",
        align="left",
    )
    set_position(visuals / "10000_textbox (dc975)", x=24, y=95, width=1272, height=64)
    set_textbox(
        visuals / "04000_textbox (76d01)",
        "6 CSV versionados  →  contrato v1.0.0  →  ETL Python  →  SQL Server  →  15 objetos analíticos  →  Power BI DirectQuery",
        font_size=16,
        color=COLORS["blue"],
        weight="bold",
        align="center",
    )
    set_position(visuals / "04000_textbox (76d01)", x=24, y=212, width=1272, height=80)
    cards = (
        (
            "20000_scope_card",
            24,
            "DATOS",
            "6 CSV · 161.111 filas",
            "65.642 partidos únicos · temporadas 1946–2022",
        ),
        (
            "21000_quality_card",
            345,
            "MODELO",
            "15 objetos analíticos",
            "30 franquicias comparables · 0 huérfanos entre tablas",
        ),
        (
            "22000_repro_card",
            666,
            "CALIDAD",
            "11 pruebas · 89,92%",
            "Reconciliación SQL · carga idempotente · controles de contrato",
        ),
        (
            "22100_lineage_card",
            987,
            "TRAZABILIDAD",
            "SHA-256 + evidencia",
            "Manifiestos, snapshot de resultados y fuente Power BI versionada",
        ),
    )
    for folder, x, label, value, detail in cards:
        create_textbox(
            page,
            folder,
            [
                (label, 11, COLORS["orange"], "bold"),
                (value, 18, COLORS["ink"], "bold"),
                (detail, 11, COLORS["muted"], "normal"),
            ],
            x=x,
            y=310,
            width=309,
            height=170,
            background=COLORS["paper"],
        )
    create_textbox(
        page,
        "23000_limits_card",
        [
            (
                "ENTREGABLES PARA REPRODUCIBILIDAD Y REVISIÓN TÉCNICA",
                11,
                COLORS["orange"],
                "bold",
            ),
            (
                "ETL Python reproducible  ·  modelo SQL Server  ·  consultas de reconciliación  ·  PBIT compilada  ·  fuente pbi-tools",
                17,
                COLORS["ink"],
                "bold",
            ),
            (
                "El revisor puede ejecutar el pipeline, cargar el modelo, contrastar el snapshot y recorrer la misma historia en DirectQuery.",
                13,
                COLORS["muted"],
                "normal",
            ),
        ],
        x=24,
        y=523,
        width=1272,
        height=159,
        background=COLORS["orange_soft"],
        align="center",
    )


def update_theme() -> None:
    theme = {
        "name": "NBA Executive Story",
        "dataColors": [
            COLORS["blue"],
            COLORS["orange"],
            COLORS["sky"],
            COLORS["navy"],
            COLORS["green"],
            COLORS["red"],
            "#7C3AED",
            "#0F766E",
        ],
        "background": COLORS["paper"],
        "foreground": COLORS["ink"],
        "tableAccent": COLORS["orange"],
        "good": COLORS["green"],
        "neutral": COLORS["blue"],
        "bad": COLORS["red"],
        "minimum": "#DBEAFE",
        "center": COLORS["sky"],
        "maximum": COLORS["orange"],
    }
    write_json(THEME, theme)


def main() -> int:
    update_theme()
    rename_slicer_model_columns()
    report_config_path = REPORT / "config.json"
    report_config = read_json(report_config_path)
    report_config["activeSectionIndex"] = 0
    write_json(report_config_path, report_config)
    for folder, display_name in PAGES.items():
        page = SECTIONS / folder
        section_path = page / "section.json"
        section = read_json(section_path)
        section["displayName"] = display_name
        write_json(section_path, section)
        set_page_background(page)

    rewrite_text_runs()
    style_header_labels()
    hide_legacy_panels()
    sort_decades_chronologically()

    q7 = (
        SECTIONS
        / "002_Análisis_2"
        / "visualContainers"
        / "07000_Eficiencia de Tiro vs Pérdidas de balón"
    )
    q9 = (
        SECTIONS
        / "003_Análisis_3"
        / "visualContainers"
        / "03000_Perfil físico promedio de los equipos NBA"
    )
    convert_efficiency_to_scatter(q7, q9)

    visual_sources = {
        SECTIONS
        / "001_Análisis_1"
        / "visualContainers"
        / "03000_Rendimiento histórico de las franquicias NBA": "analytics vw_q1_hist_perf",
        SECTIONS
        / "001_Análisis_1"
        / "visualContainers"
        / "05000_Rendimiento en función de la Antiguedad": "analytics vw_q2_age_vs_current",
        SECTIONS
        / "002_Análisis_2"
        / "visualContainers"
        / "08000_Consistencia histórica de las franquicias de NBA": "analytics vw_q5_consistency",
        SECTIONS
        / "002_Análisis_2"
        / "visualContainers"
        / "04000_Desempeño -%3E  Local vs Visitante": "analytics vw_q6_home_away_impact",
        q7: "analytics vw_q7_balance_of_def",
        SECTIONS
        / "003_Análisis_3"
        / "visualContainers"
        / "05000_Eficiencia ofensiva de equipos NBA": "analytics vw_q3_player_context_offense",
        q9: "analytics vw_q9_physical_profile",
        SECTIONS
        / "004_Insights"
        / "visualContainers"
        / "11000_Racha histórica": "analytics vw_q8_longest_win_streak",
        SECTIONS
        / "004_Insights"
        / "visualContainers"
        / "12000_Rendimiento reciente": "analytics vw_q10_recent_top",
    }
    for directory, entity in visual_sources.items():
        normalize_visual_team_source(directory, entity)

    update_cover()
    update_history()
    update_efficiency()
    update_profile()
    update_recent()
    update_method()
    add_navigation_bar()

    for path in sorted(REPORT.rglob("*.json")):
        write_json(path, replace_strings(read_json(path)))
    for directory in sorted(SECTIONS.glob("*/visualContainers/*")):
        if directory.is_dir():
            style_visual(directory)

    from localize_powerbi_en import main as apply_english_contract

    apply_english_contract()

    print(
        "Storytelling visual aplicado: seis páginas, cuatro preguntas analíticas, "
        "unidades consistentes y evidencia reproducible."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
