# 🚀 Data Pipeline Projects — Microsoft Fabric Lakehouse

This repository contains PySpark notebook-based data pipelines built for Microsoft Fabric Lakehouse using a Bronze, Silver, and Gold medallion architecture.

The notebooks listed in this repository are linked to master pipelines and are scheduled based on business reporting needs. Incremental load pipelines are optimized to run every morning from a copy of the production database refreshed at 4 AM. Snapshot pipelines are scheduled at month-end to preserve mandatory reporting data for financial and operational analytics.

---

## 📌 Project Purpose

The purpose of this project is to build reliable, automated, and analytics-ready data pipelines for enterprise reporting.

These pipelines support:

- Daily incremental data refreshes
- Full load processing when required
- Month-end snapshot reporting
- Dynamic Delta table creation
- Bronze, Silver, and Gold Lakehouse architecture
- Curated Gold layer datasets for downstream analytics
- Company-level KPI dashboards and Power BI reporting

---

## 🏗️ Lakehouse Architecture

```text
                         ┌──────────────────────────────┐
                         │   Production Database Copy   │
                         │   Refreshed Daily at 4 AM    │
                         └───────────────┬──────────────┘
                                         │
                                         ▼
                         ┌──────────────────────────────┐
                         │       Master Pipelines       │
                         │  Scheduled Daily / Monthly   │
                         └───────────────┬──────────────┘
                                         │
             ┌───────────────────────────┼───────────────────────────┐
             ▼                           ▼                           ▼
┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│    Bronze Layer      │    │    Silver Layer      │    │    Snapshot Layer    │
│ Raw Ingestion Tables │    │ Cleaned Delta Tables │    │ Month-End Snapshots  │
└──────────┬───────────┘    └──────────┬───────────┘    └──────────┬───────────┘
           │                           │                           │
           └───────────────────────────┼───────────────────────────┘
                                       ▼
                         ┌──────────────────────────────┐
                         │          Gold Layer          │
                         │ Curated Business Data Model  │
                         └───────────────┬──────────────┘
                                         ▼
                         ┌──────────────────────────────┐
                         │ Power BI / KPI Dashboards    │
                         │ Downstream Analytics         │
                         └──────────────────────────────┘
