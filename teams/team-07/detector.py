import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest

def aggregate_nodes(path="sensor_logs.csv"):
    df = pd.read_csv(path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    agg = df.groupby('node_id').agg(
        lat=('latitude', 'first'),
        lon=('longitude', 'first'),
        road_type=('road_type', 'first'),
        avg_v=('voltage_v', 'mean'),
        std_v=('voltage_v', 'std'),
        avg_c=('current_a', 'mean'),
        std_c=('current_a', 'std'),
        avg_p=('power_w', 'mean'),
        std_p=('power_w', 'std'),
        avg_brightness=('brightness_pct', 'mean')
    ).reset_index()
    
    # Calculate on_ratio
    on_ratio = df.groupby('node_id').apply(lambda x: (x['power_w'] > 5).mean(), include_groups=False).reset_index(name='on_ratio')
    agg = pd.merge(agg, on_ratio, on='node_id')
    
    agg['cv_p'] = agg['std_p'] / (agg['avg_p'] + 1e-6)
    agg.fillna(0, inplace=True)
    
    return agg

def run_isolation_forest(agg, contamination="auto"):
    features = ['avg_v', 'std_v', 'avg_c', 'std_c', 'avg_p', 'std_p', 'cv_p', 'on_ratio', 'avg_brightness']
    X = agg[features]
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    clf = IsolationForest(n_estimators=200, contamination=contamination, random_state=42, n_jobs=-1)
    
    agg['anomaly_score'] = clf.fit_predict(X_scaled)
    agg['iso_score'] = clf.decision_function(X_scaled)
    
    anomalies_df = agg[agg['anomaly_score'] == -1].copy()
    
    return anomalies_df, agg
