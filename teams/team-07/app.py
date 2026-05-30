import streamlit as st
import pandas as pd
import numpy as np
import folium
import os
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

from data_prep import load_uci, build_street_light_nodes
from detector import aggregate_nodes, run_isolation_forest
from classifier import classify_all, evaluate_classifier
from report_generator import generate_fault_report
from work_order import generate_work_order, generate_summary_report

st.set_page_config(page_title="Street Light Fault Monitor", layout="wide")

st.title("🔦 Smart Street Light Fault Report Generator")
st.subheader("Bengaluru Smart City Division — Powered by UCI Power Dataset + Groq AI")

# Sidebar
st.sidebar.header("⚙️ Setup")

if st.sidebar.button("① Download & Generate Dataset"):
    with st.spinner("Downloading UCI dataset..."):
        base = load_uci()
    with st.spinner("Building 50 street light nodes..."):
        build_street_light_nodes(base)
        
    for key in ['agg', 'full_agg', 'anomalies', 'faults', 'reports']:
        if key in st.session_state:
            del st.session_state[key]
            
    st.sidebar.success("✅ Dataset generated successfully! (Randomized)")
    st.toast("✅ New randomized dataset loaded!")

st.sidebar.divider()
st.sidebar.caption("Or upload existing CSV:")
uploaded = st.sidebar.file_uploader("Upload sensor_logs.csv", type="csv")
if uploaded:
    st.sidebar.success("✅ File uploaded successfully!")

st.sidebar.divider()
if not os.environ.get("GROQ_API_KEY"):
    st.sidebar.warning("⚠️ GROQ_API_KEY environment variable is not set. AI Reports will fail.")
else:
    st.sidebar.success("✅ GROQ_API_KEY is configured.")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Detection",
    "🗺️ Fault Map",
    "📋 Reports",
    "📄 Work Orders",
    "📈 Evaluation"
])

data_path = uploaded or ("sensor_logs.csv" if os.path.exists("sensor_logs.csv") else None)

if data_path:
    # Processing
    try:
        if 'agg' not in st.session_state or uploaded is not None:
            agg = aggregate_nodes(data_path)
            anomalies, full_agg = run_isolation_forest(agg)
            faults = classify_all(anomalies)
            
            st.session_state['agg'] = agg
            st.session_state['full_agg'] = full_agg
            st.session_state['anomalies'] = anomalies
            st.session_state['faults'] = faults
            st.session_state['reports'] = {}
    except Exception as e:
        st.error(f"❌ Error processing the uploaded file. Please ensure you upload the raw 'sensor_logs.csv' and not an exported table. Details: {str(e)}")
        st.stop()
        
    agg = st.session_state['agg']
    full_agg = st.session_state['full_agg']
    anomalies = st.session_state['anomalies']
    faults = st.session_state['faults']
    
    with tab1:
        total_nodes = len(agg)
        anomalous_nodes = len(anomalies)
        healthy_nodes = total_nodes - anomalous_nodes
        fault_rate = (anomalous_nodes / total_nodes) * 100 if total_nodes > 0 else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Nodes", total_nodes)
        c2.metric("Anomalies Detected", anomalous_nodes)
        c3.metric("Healthy Nodes", healthy_nodes)
        c4.metric("Fault Rate %", f"{fault_rate:.1f}%")
        
        st.subheader("Isolation Forest — All Node Scores")
        st.caption("More negative = more anomalous")
        display_agg = full_agg[['node_id', 'iso_score', 'avg_v', 'avg_p', 'avg_brightness', 'on_ratio', 'cv_p']].sort_values('iso_score')
        st.dataframe(display_agg, use_container_width=True)
        
        st.subheader("Classified Faults")
        
        c1, c2 = st.columns(2)
        with c1:
            filter_priority_tab1 = st.multiselect("Filter Table by Priority", options=["All", "P1", "P2", "P3"], default="All")
        with c2:
            all_fault_types_tab1 = faults['fault_type'].unique().tolist()
            filter_fault_tab1 = st.multiselect("Filter Table by Fault Type", options=["All"] + all_fault_types_tab1, default="All")
            
        filtered_faults_tab1 = faults.copy()
        if "All" not in filter_priority_tab1 and filter_priority_tab1:
            filtered_faults_tab1 = filtered_faults_tab1[filtered_faults_tab1['priority'].isin(filter_priority_tab1)]
        if "All" not in filter_fault_tab1 and filter_fault_tab1:
            filtered_faults_tab1 = filtered_faults_tab1[filtered_faults_tab1['fault_type'].isin(filter_fault_tab1)]
            
        display_faults = filtered_faults_tab1[['node_id', 'road_type', 'fault_type', 'priority', 'avg_v', 'avg_p', 'avg_brightness', 'on_ratio']].sort_values('priority')
        st.dataframe(display_faults, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.bar_chart(faults['fault_type'].value_counts())
        with col2:
            st.bar_chart(faults['priority'].value_counts())

    with tab2:
        if len(faults) > 0:
            st.subheader("Map Filters")
            c1, c2 = st.columns(2)
            with c1:
                filter_priority = st.multiselect("Filter by Priority", options=["All", "P1", "P2", "P3"], default="All")
            with c2:
                all_fault_types = faults['fault_type'].unique().tolist()
                filter_fault = st.multiselect("Filter by Fault Type", options=["All"] + all_fault_types, default="All")
            
            filtered_faults = faults.copy()
            if "All" not in filter_priority and filter_priority:
                filtered_faults = filtered_faults[filtered_faults['priority'].isin(filter_priority)]
            if "All" not in filter_fault and filter_fault:
                filtered_faults = filtered_faults[filtered_faults['fault_type'].isin(filter_fault)]
                
            mean_lat = full_agg['lat'].mean()
            mean_lon = full_agg['lon'].mean()
            m = folium.Map(location=[mean_lat, mean_lon], zoom_start=13)
            
            for idx, row in full_agg.iterrows():
                if row['anomaly_score'] != -1:
                    folium.CircleMarker(
                        location=[row['lat'], row['lon']],
                        radius=6,
                        color="blue",
                        fill=True,
                        fill_opacity=0.4,
                        popup=f"{row['node_id']} — Healthy"
                    ).add_to(m)
                    
            for idx, row in filtered_faults.iterrows():
                priority = row['priority']
                color = "red" if priority == "P1" else "orange" if priority == "P2" else "green"
                
                popup_html = f"""<b>{row['node_id']}</b><br>
                                 Road: {row['road_type']}<br>
                                 Fault: {row['fault_type']}<br>
                                 Priority: {row['priority']}<br>
                                 Voltage: {row['avg_v']:.1f}V<br>
                                 Brightness: {row['avg_brightness']:.1f}%"""
                
                folium.CircleMarker(
                    location=[row['lat'], row['lon']],
                    radius=10,
                    color=color,
                    fill=True,
                    fill_opacity=0.85,
                    popup=folium.Popup(popup_html, max_width=300)
                ).add_to(m)
                
            legend_html = '''
                 <div style="position: fixed; 
                             bottom: 50px; right: 50px; width: 150px; height: 110px; 
                             background-color: white; border:2px solid grey; z-index:9999; font-size:14px;
                             padding: 10px;">
                 <b>Legend</b><br>
                 <i style="background:blue;border-radius:50%;width:10px;height:10px;display:inline-block;"></i> Healthy<br>
                 <i style="background:red;border-radius:50%;width:10px;height:10px;display:inline-block;"></i> P1<br>
                 <i style="background:orange;border-radius:50%;width:10px;height:10px;display:inline-block;"></i> P2<br>
                 <i style="background:green;border-radius:50%;width:10px;height:10px;display:inline-block;"></i> P3
                 </div>
                 '''
            m.get_root().html.add_child(folium.Element(legend_html))
            
            st_folium(m, width=1000, height=550)
            
            st.subheader("Summary Table")
            summary = faults.groupby(['fault_type', 'priority']).size().reset_index(name='count')
            st.dataframe(summary, use_container_width=True)

    with tab3:
        st.subheader("AI-Generated Fault Reports (Groq / Llama 3)")
        st.warning(f"This will make {len(faults)} API calls to Groq.")
        
        if st.button("🤖 Generate All Fault Reports"):
            progress_bar = st.progress(0)
            for i, (idx, row) in enumerate(faults.iterrows()):
                node_id = row['node_id']
                report_text = generate_fault_report(row.to_dict())
                st.session_state['reports'][node_id] = report_text
                progress_bar.progress((i + 1) / len(faults))
            st.success("All reports generated!")
            
        if st.session_state['reports']:
            selected_node = st.selectbox("Select node to view report:", list(st.session_state['reports'].keys()))
            st.text_area("Report Content", st.session_state['reports'][selected_node], height=300, disabled=True)
            
            # Show fault details
            node_data = faults[faults['node_id'] == selected_node].iloc[0]
            st.write(f"**Fault Type:** {node_data['fault_type']} | **Priority:** {node_data['priority']} | **Road:** {node_data['road_type']}")

    with tab4:
        st.subheader("Generate DOCX Work Orders")
        
        if st.button("📄 Generate All Work Orders + Summary"):
            os.makedirs("work_orders", exist_ok=True)
            progress = st.progress(0)
            
            for i, (idx, row) in enumerate(faults.iterrows()):
                node_id = row['node_id']
                report_text = st.session_state['reports'].get(node_id, "Report not generated. Run AI Reports tab first.")
                generate_work_order(row.to_dict(), report_text, f"work_orders/WO_{node_id}.docx")
                progress.progress((i + 1) / len(faults))
                
            generate_summary_report(faults, len(agg), "work_orders/daily_fault_summary.docx")
            st.success(f"✅ {len(faults)} work orders + 1 summary report saved to /work_orders/")
            
        st.divider()
        st.subheader("Download Individual Work Orders")
        selected_wo_node = st.selectbox("Select node:", faults['node_id'].tolist())
        wo_path = f"work_orders/WO_{selected_wo_node}.docx"
        if os.path.exists(wo_path):
            with open(wo_path, "rb") as file:
                st.download_button(
                    label="Download Work Order",
                    data=file,
                    file_name=f"WO_{selected_wo_node}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
        st.divider()
        st.subheader("Download Summary Report")
        sum_path = "work_orders/daily_fault_summary.docx"
        if os.path.exists(sum_path):
            with open(sum_path, "rb") as file:
                st.download_button(
                    label="Download Summary Report",
                    data=file,
                    file_name="daily_fault_summary.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

    with tab5:
        if os.path.exists("street_lights_labeled.csv"):
            st.subheader("Model Evaluation vs Ground Truth")
            metrics = evaluate_classifier(faults, "street_lights_labeled.csv")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Accuracy", f"{metrics['accuracy']*100:.1f}%")
            c2.metric("Precision", f"{metrics['precision']*100:.1f}%")
            c3.metric("Recall", f"{metrics['recall']*100:.1f}%")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Confusion Matrix")
                labels = metrics['labels']
                cm = metrics['confusion_matrix']
                
                fig, ax = plt.subplots(figsize=(6, 4))
                cax = ax.matshow(cm, cmap=plt.cm.Blues)
                fig.colorbar(cax)
                ax.set_xticks(np.arange(len(labels)))
                ax.set_yticks(np.arange(len(labels)))
                ax.set_xticklabels(labels, rotation=45, ha='left')
                ax.set_yticklabels(labels)
                ax.set_xlabel('Predicted')
                ax.set_ylabel('True')
                for i in range(len(labels)):
                    for j in range(len(labels)):
                        ax.text(j, i, cm[i, j], ha='center', va='center', color='black')
                st.pyplot(fig)
            
            with col2:
                st.subheader("Classification Report")
                st.code(metrics['classification_report'])
                
            st.subheader("Ground Truth vs Predicted")
            labeled_df = pd.read_csv("street_lights_labeled.csv")
            gt_df = labeled_df.groupby('node_id')['fault_label'].first().reset_index()
            merged_df = pd.merge(faults, gt_df, on='node_id', how='left')
            
            display_cols = ['node_id', 'road_type', 'fault_label', 'fault_type', 'priority']
            comp_df = merged_df[display_cols].copy()
            comp_df.rename(columns={'fault_label': 'true_fault', 'fault_type': 'predicted_fault'}, inplace=True)
            comp_df['match'] = comp_df['true_fault'] == comp_df['predicted_fault']
            
            def highlight_mismatch(val):
                if isinstance(val, bool):
                    return 'background-color: #ffcccc' if not val else ''
                return ''
                
            st.dataframe(comp_df.style.map(highlight_mismatch, subset=['match']), use_container_width=True)
            
            st.divider()
            st.caption("Note: Evaluation uses street_lights_labeled.csv ground truth vs rule-based classifier predictions.")
        else:
            st.warning("Run Step 1 to generate labeled dataset first.")
