# Run backend first: uvicorn main:app --reload --port 8000
# Then run this: streamlit run app.py

import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import pandas as pd
from datetime import datetime
import re

# ---------------------------------------------------------------------------
# SESSION STATE — persist API response across rerenders
# ---------------------------------------------------------------------------
if "route_data" not in st.session_state:
    st.session_state.route_data = None

st.set_page_config(page_title="Last-Mile Fleet Route Optimiser", layout="wide")
st.title("🚚 Last-Mile Fleet Route Optimiser — Hubli")

# ---------------------------------------------------------------------------
# SIDEBAR — Inputs
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Route Configuration")

    depot_address = st.text_input(
        "Depot Address",
        placeholder="e.g. Hubli Junction Railway Station"
    )

    start_time = st.text_input(
        "Start Time (HH:MM)",
        value=datetime.now().strftime("%H:%M")
    )

    col_cap, col_fleet = st.columns(2)
    with col_cap:
        vehicle_capacity = st.number_input(
            "Capacity per Vehicle (kg)",
            min_value=1,
            value=15
        )
    with col_fleet:
        num_vehicles = st.number_input(
            "Active Fleet Size",
            min_value=1,
            max_value=5,
            value=3
        )

    st.markdown("---")
    st.subheader("Delivery Stops")

    addresses = []
    weights = []

    for i in range(1, 11):
        st.markdown(f"**Stop {i}**")
        col1, col2 = st.columns([3, 1])
        with col1:
            addr = st.text_input(
                f"Address {i}",
                placeholder="Enter delivery address in Hubli",
                key=f"addr_{i}",
                label_visibility="collapsed"
            )
        with col2:
            wt = st.number_input(
                "Weight (kg)",
                min_value=1,
                value=1,
                key=f"weight_{i}",
                label_visibility="collapsed"
            )
        addresses.append(addr)
        weights.append(wt)

    st.markdown("---")
    optimise_btn = st.button("🗺️ Optimise Fleet Routes", use_container_width=True)

# ---------------------------------------------------------------------------
# VALIDATION + API CALL
# ---------------------------------------------------------------------------
if optimise_btn:
    valid = True

    if not depot_address.strip():
        st.warning("⚠️ Depot address must not be empty.")
        valid = False

    if valid:
        empty_stops = [i + 1 for i, a in enumerate(addresses) if not a or not a.strip()]
        if empty_stops:
            st.warning(f"⚠️ Address is empty for stop(s): {empty_stops}. All 10 delivery addresses are required.")
            valid = False

    if valid:
        zero_weights = [i + 1 for i, w in enumerate(weights) if w is None or w <= 0]
        if zero_weights:
            st.warning(f"⚠️ Weight must be greater than 0 for stop(s): {zero_weights}.")
            valid = False

    if valid and (vehicle_capacity is None or vehicle_capacity <= 0):
        st.warning("⚠️ Vehicle capacity must be set and greater than 0.")
        valid = False

    if valid:
        payload = {
            "depot": depot_address.strip(),
            "current_time": start_time.strip(),
            "vehicle_capacity": int(vehicle_capacity),
            "addresses": [a.strip() for a in addresses],
            "package_weights": [int(w) for w in weights],
            "num_vehicles": int(num_vehicles)
        }

        with st.spinner("Executing multi-vehicle CVRP routing optimization... ⏳"):
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/optimize-route",
                    json=payload,
                    timeout=120
                )

                if response.status_code == 200:
                    st.session_state.route_data = response.json()
                else:
                    try:
                        detail = response.json().get("detail", response.text)
                    except Exception:
                        detail = response.text
                    st.error(f"❌ API Error: {detail}")

            except requests.exceptions.ConnectionError:
                st.error("❌ Could not connect to backend. Make sure FastAPI server is running on port 8000.")
            except requests.exceptions.Timeout:
                st.error("❌ Request timed out. The backend optimization engine is taking too long to respond.")
            except requests.exceptions.RequestException:
                st.error("❌ Network error layer hit. Verify backend endpoint accessibility.")

# ---------------------------------------------------------------------------
# OUTPUT LAYER
# ---------------------------------------------------------------------------
if st.session_state.route_data:
    data = st.session_state.route_data

    fleet_routes = data.get("fleet_routes", [])
    skipped_stops = data.get("skipped_stops", [])
    driver_briefing = data.get("driver_briefing", "")
    depot_coords = data.get("depot_coords")

    # -----------------------------------------------------------------------
    # 1. OPTIMIZED FLEET MANIFEST TABLES & ISOLATED INSTRUCTIONS
    # -----------------------------------------------------------------------
    st.subheader("🗺️ Optimized Fleet Deployment Plan")
    
    if skipped_stops:
        st.error(f"⚠️ Fleet Capacity Overload: {len(skipped_stops)} shipments dropped due to overall capacity limitations!")
        with st.expander("View Unassigned Cargo Shipments", expanded=True):
            skipped_df = pd.DataFrame([{
                "Line Item": s["global_stop_index"],
                "Unserviced Destination": s["address"],
                "Weight": f"{s['package_weight']} kg"
            } for s in skipped_stops])
            st.dataframe(skipped_df, hide_index=True, use_container_width=True)

    for v_route in fleet_routes:
        vehicle_id = v_route["vehicle_id"]
        total_weight = v_route["total_weight"]
        stops = v_route["route"]
        
        with st.expander(f"🚛 Vehicle {vehicle_id} Dashboard — ({total_weight} kg / {vehicle_capacity} kg capacity)", expanded=True):
            if not stops:
                st.info("No delivery nodes assigned to this vehicle for this shift.")
            else:
                st.markdown("#### 📊 Route Sequence Manifest")
                table_rows = [{
                    "Seq No": s["stop_number"],
                    "Original Item Ref": s["global_stop_index"],
                    "Delivery Address": s["address"],
                    "Dynamic ETA Window": s["eta_window"],
                    "Package Weight": f"{s['package_weight']} kg"
                } for s in stops]
                st.dataframe(pd.DataFrame(table_rows), hide_index=True, use_container_width=True)
                
                st.markdown(f"#### 📋 Dedicated Manifest Instructions for Driver {vehicle_id}")
                
                # -----------------------------------------------------------------------
                # ROBUST REGEX PARSING LAYER
                # -----------------------------------------------------------------------
                v_instructions = ""
                
                # Matches variant heading formats case-insensitively, handling markdown syntax smoothly
                header_pattern = rf"(?:#*\s*Vehicle\s+ID\s*:?\s*{vehicle_id}\b)"
                header_match = re.search(header_pattern, driver_briefing, re.IGNORECASE)
                
                if header_match:
                    start_pos = header_match.end()
                    remaining_text = driver_briefing[start_pos:]
                    
                    # Track down the next vehicle block start anchor point
                    next_vehicle_pattern = r"(?:#*\s*Vehicle\s+ID\s*:?\s*\d+\b)"
                    next_vehicle_match = re.search(next_vehicle_pattern, remaining_text, re.IGNORECASE)
                    
                    if next_vehicle_match:
                        content_slice = remaining_text[:next_vehicle_match.start()]
                    else:
                        # Slice clean at the horizontal separator line for the final vehicle block
                        content_slice = remaining_text.split("---")[0]
                    
                    # Clean out lingering headers, punctuation, lists, and spacing layout artifacts
                    v_instructions = content_slice.lstrip(" \t\n\r:*-#").replace("Dispatch Array", "").strip()
                
                if not v_instructions:
                    v_instructions = "Follow the sequential matrix table layout coordinates outlined above for this route run."

                scrollbox_start = """
                <div style="
                    background-color: #1e2430; 
                    padding: 18px; 
                    border-radius: 6px; 
                    border: 1px solid #3a4250; 
                    max-height: 250px; 
                    overflow-y: auto;
                    color: #e0e6ed;
                    line-height: 1.6;
                    margin-top: 10px;
                    margin-bottom: 10px;
                ">
                """
                scrollbox_end = "</div>"
                
                full_instructions_html = f"{scrollbox_start}\n{v_instructions}\n{scrollbox_end}"
                st.markdown(full_instructions_html, unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # 2. COLOR-CODED MULTI-VEHICLE MAP TRACKING
    # -----------------------------------------------------------------------
    st.subheader("Interactive Fleet Route Visualizer")

    HUBLI_LAT, HUBLI_LNG = 15.3647, 75.1240
    m = folium.Map(location=[HUBLI_LAT, HUBLI_LNG], zoom_start=13)

    if depot_coords:
        folium.Marker(
            location=depot_coords,
            tooltip="Central Distribution Depot",
            popup=depot_address,
            icon=folium.Icon(color="black", icon="home", prefix="fa")
        ).add_to(m)

    route_colors = ["blue", "purple", "orange", "darkgreen", "cadetblue"]

    for idx, v_route in enumerate(fleet_routes):
        color = route_colors[idx % len(route_colors)]
        vehicle_id = v_route["vehicle_id"]
        polyline_points = [depot_coords] if depot_coords else [[HUBLI_LAT, HUBLI_LNG]]

        for stop in v_route["route"]:
            lat = stop.get("lat")
            lng = stop.get("lng")
            if lat is None or lng is None:
                continue
                
            folium.Marker(
                location=[lat, lng],
                tooltip=f"V{vehicle_id} Stop {stop['stop_number']}: {stop['address']}",
                popup=f"<b>Vehicle {vehicle_id} — Stop {stop['stop_number']}</b><br>{stop['address']}<br>ETA: {stop['eta_window']}",
                icon=folium.Icon(color=color, icon="play", prefix="fa")
            ).add_to(m)
            polyline_points.append([lat, lng])

        if len(polyline_points) > 1:
            if depot_coords:
                polyline_points.append(depot_coords)
            folium.PolyLine(
                locations=polyline_points,
                color=color,
                weight=4,
                opacity=0.8,
                tooltip=f"Vehicle {vehicle_id} Route Path"
            ).add_to(m)

    st_folium(m, width=1300, height=500)

    # -----------------------------------------------------------------------
    # 3. CUSTOMER NOTIFICATIONS
    # -----------------------------------------------------------------------
    st.subheader("Customer Messages")
    customer_messages = data.get("customer_messages", [])
    
    if not customer_messages:
        st.info("No customer notification messages generated for this run.")
    else:
        with st.container(border=True):
            for i, msg in enumerate(customer_messages):
                st.markdown(f"**Stop Ref {msg['stop_number']} — {msg['address']}**")
                st.write(msg['message'])
                
                if i < len(customer_messages) - 1:
                    st.markdown("---")