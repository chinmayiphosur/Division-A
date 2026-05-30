import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix, classification_report

def classify_fault(row):
    if row['on_ratio'] < 0.05:
        fault_type = "offline"
    elif row['on_ratio'] < 0.6:
        fault_type = "burnt"
    elif row['std_v'] > 15 or row['avg_v'] > 245:
        fault_type = "voltage_surge"
    elif row['cv_p'] > 0.5:
        fault_type = "flickering"
    else:
        fault_type = "unknown"
        
    road_type = row.get('road_type', '')
    if road_type == "Highway":
        priority = "P1"
    elif road_type == "Main Road":
        priority = "P2"
    elif road_type == "Residential":
        priority = "P3"
    else:
        priority = "P2"
        
    return {
        "fault_type": fault_type,
        "priority": priority,
        "confidence": 0.92
    }

def classify_all(anomalies_df):
    results = anomalies_df.apply(classify_fault, axis=1, result_type='expand')
    
    final_df = anomalies_df.copy()
    final_df['fault_type'] = results['fault_type']
    final_df['priority'] = results['priority']
    final_df['confidence'] = results['confidence']
    
    cols = ['node_id', 'lat', 'lon', 'road_type', 'avg_v', 'std_v', 'avg_c', 'avg_p', 'cv_p', 'on_ratio', 'avg_brightness', 'iso_score', 'fault_type', 'priority', 'confidence']
    return final_df[cols]

def evaluate_classifier(faults_df, labeled_path="street_lights_labeled.csv"):
    labeled_df = pd.read_csv(labeled_path)
    
    # Aggregate ground truth fault_label per node_id (take first value)
    gt_df = labeled_df.groupby('node_id')['fault_label'].first().reset_index()
    
    merged_df = pd.merge(faults_df, gt_df, on='node_id', how='left')
    
    y_true = merged_df['fault_label'].fillna('unknown').values
    y_pred = merged_df['fault_type'].values
    
    labels = sorted(list(set(y_true) | set(y_pred)))
    
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, average='weighted', zero_division=0)
    rec = recall_score(y_true, y_pred, average='weighted', zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    cr = classification_report(y_true, y_pred, labels=labels, zero_division=0)
    
    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "confusion_matrix": cm,
        "classification_report": cr,
        "labels": labels
    }
