## ⚠️ Data Access \& Replication Notice





The final dashboard does not expose raw data publicly.



All analytical results shown in Power BI require a direct connection to the SQL Server environment, as originally designed in the project architecture.

This was intentionally implemented to:

* Preserve data integrity
* Ensure controlled access
* Maintain performance optimization through DirectQuery
* Simulate a real-world production BI environment
* 

However, the complete data ingestion and processing pipeline is fully reproducible.

By executing the automated script: "DATA\_AUTO.bat"

