# Canonical model and ERD

I keep the source tables wide enough to preserve the published dataset, then expose analytical grain through SQL views. The physical model deliberately separates identity dimensions from game-level facts.

```mermaid
erDiagram
    DIM_TEAM ||--o{ FACT_GAME : "home team"
    DIM_TEAM ||--o{ FACT_GAME : "away team"
    DIM_PLAYER ||--o| DIM_PLAYER_PROFILE : describes
    DIM_TEAM ||--o{ DIM_PLAYER_PROFILE : "current/historical label"
    FACT_GAME ||--o| FACT_GAME_SUMMARY : summarizes
    FACT_GAME ||--o| FACT_OTHER_STATS : extends

    DIM_TEAM {
        bigint team_id PK
        string full_name
        string abbreviation
        int year_founded
        boolean is_historical_unmapped
    }
    DIM_PLAYER {
        bigint player_id PK
        string full_name
        boolean is_active
    }
    DIM_PLAYER_PROFILE {
        bigint player_id PK,FK
        bigint team_id FK
        date birthdate
        float height_cm
        float weight
    }
    FACT_GAME {
        bigint game_id PK
        bigint team_id_home FK
        bigint team_id_away FK
        date game_date
        int season_year
        string season_stage
        float pts_home
        float pts_away
    }
    FACT_GAME_SUMMARY {
        bigint game_id PK,FK
        int season_year
        int game_status_id
    }
    FACT_OTHER_STATS {
        bigint game_id PK,FK
        bigint team_id_home FK
        bigint team_id_away FK
        float pts_paint_home
        float pts_paint_away
    }
```

## Analytical bridge

`analytics.vw_team_game` turns each accepted game into exactly two records: one home-team observation and one away-team observation. Every team-season metric and Power BI question derives from that single grain. `analytics.dim_season` and `analytics.vw_bridge_team_season` provide canonical year/decade and team-season relationships without duplicating facts in Python.

For the complete column-level contract, use [`canonical_data_dictionary.md`](canonical_data_dictionary.md) and [`../contracts/schema_v1.0.0.json`](../contracts/schema_v1.0.0.json).
