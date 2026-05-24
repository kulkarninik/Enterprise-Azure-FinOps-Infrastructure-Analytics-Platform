# Enterprise-Azure-FinOps-Infrastructure-Analytics-Platform

## 📌 Project Overview
An end-to-end Azure data engineering project focused on Cloud Financial Operations (FinOps) and IT Infrastructure monitoring. This platform ingests cloud billing and performance data, processes it using a Medallion Architecture (Bronze/Silver/Gold), and provides actionable cost-optimization insights via Power BI.

## 🏗️ Architecture
* **Data Sources**: Synthetic enterprise Azure data (Cost Management, Resource Graph, Azure Monitor).
* **Storage**: Azure Data Lake Storage Gen2.
* **Processing**: Azure Databricks (PySpark, Spark SQL).
* **Data Format**: Delta Lake (ACID compliance, schema enforcement).
* **Visualization**: Power BI (Import/DirectQuery).

### Medallion Data Flow:
1. **Bronze Layer**: Raw CSV data ingested into ADLS Gen2.
2. **Silver Layer**: Cleansed, deduplicated, and typed data stored as Delta tables.
3. **Gold Layer**: Business-level aggregations (Daily Costs, Resource Utilization, Health Scores, Optimization Recommendations).

## 🛠️ Technology Stack
* **Cloud**: Azure (ADLS Gen2, Databricks, Key Vault)
* **Data Engineering**: Apache Spark, PySpark, Delta Lake
* **Languages**: Python, SQL, DAX
* **BI Tool**: Power BI

## 📊 Key Dashboard Features
* **Executive Cost Overview**: MoM growth, YTD spend, and budget utilization.
* **Cost Optimization**: Right-sizing and shutdown recommendations with potential ROI.
* **Infrastructure Health**: CPU/Memory utilization trends and anomaly alerts.
* **Resource Inventory**: Under-utilized VM detection and regional cost mapping.

## 🚀 How to Run
1. Run `generate_enterprise_infra_data.py` locally to generate synthetic datasets.
2. Upload the generated CSV files to the `bronze/raw` container in ADLS Gen2.
3. Execute Databricks Notebook `00_Setup_Storage_Access` to configure storage credentials.
4. Execute `01_Bronze_to_Silver` to clean and save data to Delta format.
5. Execute `02_Silver_to_Gold` to generate business aggregations.
6. Execute `03_Register_Gold_Tables` to register Delta tables in the Databricks catalog.
7. Open the `.pbix` file in Power BI Desktop, configure the Databricks connection, and refresh.

## 📈 Business Impact
* **Cost Reduction**: Identifies idle resources and generates right-sizing recommendations.
* **Efficiency**: Automates monthly cloud reporting, saving IT and Finance teams ~20 hours/month.
* **Proactive Monitoring**: Flags degrading infrastructure health before it impacts production.
