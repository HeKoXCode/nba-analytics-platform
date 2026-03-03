🏀 NBA Analytics Platform



End-to-End Automated Data Warehouse \& BI Solution (22GB Historical Dataset)

This project consists of a fully automated analytics platform designed to process and model the entire historical NBA dataset (22GB), transforming raw game-level data into a structured Data Warehouse optimized for SQL Server and Power BI.

The objective was not only to build dashboards, but to simulate a real-world BI production architecture: automated ingestion, relational modeling, validation, and performance optimization.





🎯 Business Objective



To analyze how team performance and efficiency metrics impact game results over time using a clean star schema ready for enterprise BI environments.

The platform answers strategic questions such as:

Which franchises show the strongest historical performance?

How do offensive and defensive metrics correlate with wins?

How has league scoring evolved across decades?

What is the impact of home advantage?

Which teams demonstrate long-term performance stability?





🏗 Architecture Overview



Raw Data → Python ETL → SQL Server (Star Schema) → Optimized SQL Views → Power BI (DirectQuery)

Key Features

Automated ingestion with file monitoring trigger

Data cleaning and normalization in Python

Star schema modeling in SQL Server

Performance optimization by migrating heavy DAX calculations to SQL views

DirectQuery configured for low-latency reporting

Fully reproducible pipeline





🖼 Dashboard Preview



![Historical Overview](IMAGES/01_Historical_Performance_Overview.png)

![Efficiency and Consistency](IMAGES/02_Efficiency_and_Consistency.png)

![Current Talent Analysis](IMAGES/03_Current_Talent_Analysis.png)

![Key Findings – Success Model](IMAGES/04_Key_Findings_Success_Model.png)

![Franchise Deep Dive – Spurs](IMAGES/05_Franchise_Deep_Dive_Spurs.png)





📁 Repository Structure



CODE/ → Execution layer (ETL, SQL, Power BI)
DOCS/  → Documentation layer (data sources, model details, validations)
IMAGES/ → Dashboard previews and visual assets

For full technical details, see:
DOCS/technical\_documentation.md





⚙️ Technology Stack



Python → ETL, validation, automation

SQL Server → Data Warehouse (Star Schema)

Power BI → Interactive dashboards (DirectQuery optimized)





▶️ Reproducibility

Download raw data (see DOCS/raw\_data\_sources.txt)

Place files inside CODE/data\_raw

Execute:

CODE/ingesta\_data\_auto.bat

Connect Power BI to the generated SQL database

The dashboard requires connection to the local SQL environment, as designed to simulate a production setup.

🚀 What This Project Demonstrates

End-to-end BI architecture design

Automated ingestion pipelines

Data modeling best practices

Performance optimization strategies

Large-scale analytical storytelling



-----------------------------------------------



Percy Ignacio Marzoratti Hill
Data Analyst | BI \& Analytics Engineering Focus
