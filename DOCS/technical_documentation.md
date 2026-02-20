-- Technical Documentation --



NBA Analytics Platform – End-to-End Data Warehouse \& BI Architecture



This document provides a complete technical overview of the NBA Analytics Platform, including data warehouse design, ETL processes, validation logic, and analytical environment configuration.







🏀 General Overview

Project Objective



To analyze how team-level performance and efficiency metrics impact game results across the entire historical NBA dataset (22GB), using a clean, relational star schema designed for SQL Server and Power BI.



The platform was built to simulate a production-ready BI environment, including automation, validation, modeling best practices, and performance optimization.







🎯 Analytical Objectives



Analyze offensive and defensive team performance.



Detect performance patterns and their relationship with wins.



Develop interactive dashboards with key KPIs (points, rebounds, assists, efficiency, etc.).



Enable long-term historical franchise evaluation.



Support scalable business intelligence analysis.







🧱 Data Warehouse Design – Star Schema



The analytical model follows a star schema structure to ensure scalability, performance, and referential integrity.



Fact Tables

Table	Type	Description

fact\_game	Fact	General game-level data (date, season, teams, score).

fact\_team\_game	Fact	Team statistics per game (two rows: home / away).

other\_stats\_final	Fact (backup)	Aggregated metrics per game (wide structure with \*\_home / \*\_away columns).

Dimension Tables

Table	Type	Description

dim\_team	Dimension	Descriptive team information.

dim\_player	Dimension	Basic player attributes.

game\_summary	Auxiliary Dimension	Game logistics (arena, referees, attendance).



The model ensures:



Referential integrity



Efficient joins



Optimized analytical queries



Scalability for future expansions







🔄 ETL – Data Cleaning \& Transformation



The ETL pipeline was developed in Python to standardize and normalize raw NBA data before SQL Server ingestion.



Transformations Implemented



Column name standardization (snake\_case)



Strict data typing (IDs as Int64, dates as datetime64)



Natural primary key deduplication (game\_id, team\_id, etc.)



Historical ID cross-referencing (team\_xref.csv mapping for FK integrity)



Normalization of wide metrics (other\_stats\_final → fact\_team\_game structure)



Final export to /data/final/ ready for SQL Server ingestion



Automated detection of new incoming data files



The goal was to guarantee clean, relational-ready datasets before loading into the warehouse.







⚙️ Automation \& Execution



The ingestion process is triggered using:



CODE/DATA\_AUTO.bat



This script:



Detects new incoming files



Executes the Python ETL pipeline



Applies validation logic



Generates final structured datasets



Prepares data for SQL Server loading



Enables seamless Power BI connection



The automation simulates a production-level ingestion pipeline.









✅ Data Quality \& Validation



Multiple validation layers were implemented to ensure data integrity:



Primary keys validated (no duplicates)



Foreign keys validated (98–100% integrity between fact and dimension tables)



No null values in critical columns



Season-date coherence validation



Automated detection of new data inputs



These controls ensure warehouse reliability and analytical consistency.









⚡ Performance Optimization Strategy



To reduce Power BI DirectQuery overhead:



Heavy calculations were migrated from DAX into SQL views.



Star schema modeling was applied to optimize joins.



DirectQuery was configured for low-latency reporting.



Data normalization reduced redundancy and improved query execution.



This approach improves scalability and reporting performance over large datasets.









🖥 Analytical Environment



Python → ETL, validation, automation



SQL Server → Data Warehouse storage (Star Schema)



Power BI → Interactive dashboards (DirectQuery optimized)



The architecture was designed to reflect real-world BI engineering workflows.







📊 Analytical Scope



The platform supports answering complex historical performance questions such as:



Historical franchise performance analysis



Offensive vs defensive efficiency balance



Long-term stability and consistency



Impact of home advantage



Evolution of league scoring trends



Efficiency vs win correlation







🎯 Architectural Design Goals



Scalability



Performance optimization



Referential integrity



Automation



Reproducibility



Production-like BI simulation







👥 madeBy



Percy Ignacio Marzoratti Hill – Data Analyst

