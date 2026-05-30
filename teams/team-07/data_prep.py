import os
import zipfile
import requests
import pandas as pd
import numpy as np

def load_uci():
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00235/household_power_consumption.zip"
    zip_path = "hpc.zip"
    txt_path = "household_power_consumption.txt"

    if not os.path.exists(txt_path):
        if not os.path.exists(zip_path):
            print("Downloading UCI dataset...")
            r = requests.get(url)
            with open(zip_path, "wb") as f:
                f.write(r.content)
        print("Extracting zip...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")

    print("Loading data...")
    df = pd.read_csv(
        txt_path, 
        sep=";", 
        na_values="?", 
        parse_dates=[['Date', 'Time']], 
        dayfirst=True,
        low_memory=False
    )
    df.dropna(inplace=True)
    df.rename(columns={'Date_Time': 'datetime'}, inplace=True)
    
    # Keep only first 7 days of data
    start_time = df['datetime'].min()
    end_time = start_time + pd.Timedelta(days=7)
    df = df[df['datetime'] <= end_time]

    df.rename(columns={
        'Global_active_power': 'power_kw',
        'Voltage': 'voltage_v',
        'Global_intensity': 'current_a'
    }, inplace=True)
    
    df['power_w'] = df['power_kw'] * 1000
    return df[['datetime', 'voltage_v', 'current_a', 'power_w']]

def build_street_light_nodes(base_df, n_nodes=50, seed=None):
    rng = np.random.default_rng(seed)
    
    latitudes = rng.uniform(12.92, 13.02, size=n_nodes)
    longitudes = rng.uniform(77.55, 77.65, size=n_nodes)
    
    road_types = []
    for i in range(n_nodes):
        if i <= 16:
            road_types.append("Highway")
        elif i <= 33:
            road_types.append("Main Road")
        else:
            road_types.append("Residential")
            
    fault_options = ["normal", "burnt", "flickering", "voltage_surge", "offline"]
    fault_probs = [0.55, 0.10, 0.15, 0.10, 0.10]
    fault_labels = rng.choice(fault_options, size=n_nodes, p=fault_probs).tolist()
            
    rng.shuffle(road_types)
    rng.shuffle(fault_labels)
            
    all_data = []
    
    global_max_power = base_df['power_w'].max()
    if global_max_power == 0:
        global_max_power = 1 # avoid div by zero
        
    for i in range(n_nodes):
        node_id = f"NODE_{i:03d}"
        
        v = base_df['voltage_v'].values.copy()
        c = base_df['current_a'].values.copy()
        p = base_df['power_w'].values.copy()
        ts = base_df['datetime'].values.copy()
        
        n_samples = len(v)
        f_label = fault_labels[i]
        
        if f_label == "burnt":
            cutoff = int(n_samples * 0.4)
            v[cutoff:] = rng.normal(0, 1, size=n_samples - cutoff)
            c[cutoff:] = np.abs(rng.normal(0, 0.05, size=n_samples - cutoff))
            p[cutoff:] = np.abs(rng.normal(0, 2, size=n_samples - cutoff))
            
        elif f_label == "flickering":
            spike_idx = rng.choice(n_samples, size=int(n_samples * 0.12), replace=False)
            p[spike_idx] *= rng.uniform(0.1, 3.5, size=len(spike_idx))
            c[spike_idx] *= rng.uniform(0.1, 3.0, size=len(spike_idx))
            
        elif f_label == "voltage_surge":
            surge_idx = rng.choice(n_samples, size=int(n_samples * 0.16), replace=False)
            v[surge_idx] = rng.uniform(260, 280, size=len(surge_idx))
            p[surge_idx] *= 1.8
            
        elif f_label == "offline":
            v[:] = np.abs(rng.normal(2, 1, size=n_samples))
            c[:] = np.abs(rng.normal(0.01, 0.005, size=n_samples))
            p[:] = np.abs(rng.normal(1, 0.5, size=n_samples))
            
        # Add noise
        v += rng.normal(0, 1.5, size=n_samples)
        
        # Clip
        v = np.clip(v, 0, 300)
        c = np.clip(c, 0, 20)
        p = np.clip(p, 0, 5000)
        
        brightness_normal = (p / global_max_power) * 100
        
        if f_label == "normal":
            brightness = brightness_normal
        elif f_label == "burnt":
            brightness = np.zeros(n_samples)
        elif f_label == "flickering":
            brightness = brightness_normal * rng.uniform(0.0, 1.5, size=n_samples)
        elif f_label == "voltage_surge":
            brightness = np.full(n_samples, 100.0)
        elif f_label == "offline":
            brightness = np.zeros(n_samples)
            
        brightness = np.clip(brightness, 0, 100)
        
        node_df = pd.DataFrame({
            'node_id': node_id,
            'timestamp': ts,
            'latitude': latitudes[i],
            'longitude': longitudes[i],
            'voltage_v': v,
            'current_a': c,
            'power_w': p,
            'brightness_pct': brightness,
            'road_type': road_types[i],
            'fault_label': f_label
        })
        all_data.append(node_df)
        
    full_df = pd.concat(all_data, ignore_index=True)
    
    labeled_path = "street_lights_labeled.csv"
    unlabeled_path = "sensor_logs.csv"
    
    full_df.to_csv(labeled_path, index=False)
    
    sensor_df = full_df.drop(columns=['fault_label'])
    sensor_df.to_csv(unlabeled_path, index=False)
    
    print("Fault type distribution:")
    print(pd.Series(fault_labels).value_counts())
    print("\nRoad type distribution:")
    print(pd.Series(road_types).value_counts())
    
    return full_df
