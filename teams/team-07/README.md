# 💡 Smart Street Light Fault Report Generator using Sensor Data

## Overview

The **Smart Street Light Fault Report Generator** is an AI-powered smart city monitoring system developed as part of the **Generative AI (25ECSC314)** course project. The system automates the detection, classification, visualization, and reporting of street-light faults using Machine Learning and Generative AI.

The project addresses the challenge of inefficient street-light maintenance by providing an automated framework that analyzes sensor data, identifies faults, prioritizes maintenance activities, and generates maintenance reports and work orders.

---

# Problem Statement

Urban municipalities lose significant energy and face safety risks due to faulty street lights and the absence of automated fault reporting systems.

The objective is to build a Generative AI-based solution that:

* Ingests street-light sensor data
* Detects fault patterns
* Classifies fault types
* Assigns maintenance priorities
* Generates structured fault reports
* Creates maintenance work orders automatically

---

# Objectives

* Detect abnormal street-light behaviour using **Isolation Forest** anomaly detection.
* Classify faults into **Burnt, Flickering, Voltage Surge, and Offline** categories.
* Generate AI-powered fault reports and maintenance work orders.
* Visualize fault locations on an interactive map and prioritize repairs using **P1, P2, and P3** levels.

---

# Dataset Used

## UCI Individual Household Electric Power Consumption Dataset

The project uses the **UCI Individual Household Electric Power Consumption Dataset**, which contains:

* More than 2 million electrical measurements
* Voltage readings
* Current intensity measurements
* Active power consumption values
* Timestamp information

### Features Used

| Feature             | Description                 |
| ------------------- | --------------------------- |
| Voltage             | Electrical voltage readings |
| Global Intensity    | Current measurements        |
| Global Active Power | Power consumption values    |
| Date & Time         | Timestamp information       |

### Smart Street Light Simulation

The dataset is transformed into a simulated smart-city environment consisting of:

* 50 Smart Street-Light Nodes
* GPS Coordinates
* Road Categories:

  * Highway
  * Main Road
  * Residential
* Simulated Fault Types:

  * Burnt Lamp
  * Flickering Lamp
  * Voltage Surge
  * Offline Node

---

# Methodology

The proposed system follows the workflow shown below:

1. Data Cleaning and Preprocessing
2. Street-Light Node Generation
3. Fault Injection Simulation
4. Feature Engineering
5. Isolation Forest Anomaly Detection
6. Rule-Based Fault Classification
7. Priority Assignment
8. Generative AI Report Generation
9. Performance Evaluation
10. Work Order Generation

---

# Machine Learning Approach

## Anomaly Detection

### Isolation Forest

The system uses **Isolation Forest**, an unsupervised anomaly detection algorithm, to identify abnormal street-light behaviour.

### Why Isolation Forest?

* Works well without labelled training data
* Efficient for large datasets
* Suitable for anomaly detection problems
* Automatically isolates abnormal observations

### Features Used

The following features are extracted for anomaly detection:

* Average Voltage
* Voltage Standard Deviation
* Average Current
* Current Standard Deviation
* Average Power
* Power Standard Deviation
* Brightness Percentage
* On-Time Ratio
* Power Coefficient of Variation

---

# Fault Classification

Detected anomalies are classified using a rule-based classification engine.

## Fault Categories

| Fault Type    | Description                                |
| ------------- | ------------------------------------------ |
| Burnt         | Lamp is completely non-functional          |
| Flickering    | Unstable brightness and power fluctuations |
| Voltage Surge | Excessively high voltage conditions        |
| Offline       | Communication or power failure             |

---

# Priority Assignment

Maintenance priority is assigned based on road importance.

| Road Type   | Priority |
| ----------- | -------- |
| Highway     | P1       |
| Main Road   | P2       |
| Residential | P3       |

This ensures critical faults on major roads receive immediate attention.

---

# Generative AI Integration

## Groq + Llama 3

The Generative AI component uses the **Llama 3 Large Language Model** served through the **Groq API**.

### Role of Generative AI

The model is used to generate:

* Fault Analysis Reports
* Maintenance Recommendations
* Technician Instructions
* Municipal Summary Reports

### Input to the LLM

* Fault Type
* Priority Level
* Voltage Statistics
* Power Statistics
* Brightness Information
* GPS Coordinates
* Road Type

### Output from the LLM

* Structured Fault Reports
* Maintenance Recommendations
* Work Order Content

---

# Dashboard Features

## Streamlit Dashboard

The web dashboard provides:

* Fault Detection Overview
* Node Health Statistics
* Interactive Filters
* Evaluation Metrics
* Report Generation Interface

## Folium GIS Map

The system visualizes:

* Healthy Street Lights
* Faulty Street Lights
* GPS Locations
* Priority Levels (P1, P2, P3)

---

# Evaluation Metrics

The performance of the classification system is evaluated using:

* Accuracy
* Precision
* Recall
* Confusion Matrix
* Classification Report

Ground-truth labels generated during fault simulation are used for evaluation.

---

# System Outputs

The system automatically generates:

### Fault Detection Dashboard

* Real-time anomaly visualization
* Node status monitoring
* Fault statistics

### GIS-Based Fault Map

* Interactive fault location visualization
* Priority-based color coding

### AI-Generated Fault Reports

* Fault summaries
* Technical analysis
* Recommended actions

### Automated DOCX Work Orders

* Maintenance instructions
* Fault details
* Technician checklist

### Municipal Summary Report

* Total faults detected
* Priority distribution
* Maintenance recommendations

---

# Technology Stack

| Component             | Technology                      |
| --------------------- | ------------------------------- |
| Programming Language  | Python                          |
| Data Processing       | Pandas, NumPy                   |
| Machine Learning      | Scikit-Learn (Isolation Forest) |
| Dashboard Development | Streamlit                       |
| GIS Visualization     | Folium                          |
| Generative AI         | Groq API + Llama 3              |
| Document Generation   | python-docx                     |

---

# Results

The developed system successfully:

* Generated a simulated network of 50 smart street-light nodes.
* Detected abnormal street-light behaviour using Isolation Forest.
* Classified faults into four categories.
* Assigned maintenance priorities automatically.
* Visualized faults on an interactive GIS map.
* Generated AI-powered maintenance reports.
* Produced DOCX work orders and municipal summary reports.
* Evaluated classification performance using standard ML metrics.

---

# Future Scope

* Integration with real-time IoT street-light sensors.
* Predictive maintenance using historical failure trends.
* Mobile application for maintenance personnel.
* Smart city platform integration.
* Automated SMS and email alert systems.
* Cloud-based deployment for city-scale monitoring.

---

# Installation and Setup

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure Groq API Key

```bash
export GROQ_API_KEY="your_api_key_here"
```

## Step 3: Run the Application

```bash
streamlit run app.py
```

---

# Project Information

**Course:** Generative AI (25ECSC314)

**Department:** Computer Science and Engineering

**Semester:** VI Semester

**Academic Year:** 2025–26

## Team Members

| Name                | Roll No. | USN          |
| ------------------- | -------- | ------------ |
| Anagha Hegde        | 112      | 01FE23BCS064 |
| Sahana V. Agadi     | 116      | 01FE21BCS091 |
| Srushti Bammanawadi | 121      | 01FE23BCS098 |
| Tanushree Manjunath | 126      | 01FE23BCS120 |

**Guide:** Dr. Guruprasad Konnurmath
Professor, Department of Computer Science and Engineering

---

## Conclusion

The Smart Street Light Fault Report Generator demonstrates how Machine Learning and Generative AI can be combined to automate urban infrastructure monitoring. By detecting faults early, prioritizing maintenance activities, and generating actionable reports, the system helps improve operational efficiency, reduce maintenance costs, and enhance public safety in smart city environments.
