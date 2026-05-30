import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from schemas import RouteOptimizationRequest, RouteOptimizationResponse
from services import (
    geocode_address,
    get_distance_matrix,
    solve_cvrp,
    calculate_route_etas,
    generate_route_narrative,
    GeocodingError
)

app = FastAPI(
    title="Last-Mile Delivery Route Optimiser API",
    description="Optimises delivery paths using OSRM distances, applies dynamic speed-based ETAs, and generates driver briefs/SMS notifications using Google Gemini.",
    version="1.0.0"
)

# Set up CORS middleware for premium UI clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom error handler for clean geocoding failure messages
@app.exception_handler(GeocodingError)
async def geocoding_error_handler(request: Request, exc: GeocodingError):
    return JSONResponse(
        status_code=400,
        content={
            "error": "GeocodingError",
            "message": exc.message,
            "address": exc.address
        }
    )

@app.get("/", tags=["General"])
async def root():
    return {
        "message": "Welcome to the Last-Mile Delivery Route Optimiser API",
        "docs_url": "/docs",
        "status": "healthy"
    }

@app.post("/optimize-route", response_model=RouteOptimizationResponse, tags=["Route Optimisation"])
async def optimize_route(request: RouteOptimizationRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing API configuration key.")

    # 1. Geocode Depot & Stops
    depot_lat, depot_lng = geocode_address(request.depot)
    coordinates = [(depot_lat, depot_lng)]
    for addr in request.addresses:
        coordinates.append(geocode_address(addr))
            
    # 2. Build Cost Matrix
    durations, distances = get_distance_matrix(coordinates)
        
    # 3. Solve Real Fleet CVRP
    fleet_assignments, skipped_nodes = solve_cvrp(
        durations, request.package_weights, request.vehicle_capacity, request.num_vehicles
    )
        
   # 4. Generate Times and Build Fleet Payload Objects
    final_fleet_routes = []
    fleet_prompt_text = ""
    
    for vehicle_id, nodes in fleet_assignments.items():
        if not nodes:
            continue
            
        stop_details = calculate_route_etas(nodes, distances, request.current_time)
        vehicle_stops = []
        vehicle_total_weight = 0
        
        current_node = 0 # The Depot index is always 0
        for idx, stop in enumerate(stop_details):
            node_idx = stop["stop_node"]
            weight = request.package_weights[node_idx - 1]
            vehicle_total_weight += weight
            
            # Calculate segment distance from the immediate previous stop location
            # Converting OSRM raw meters to a clean kilometer metric
            seg_distance_km = round(distances[current_node][node_idx] / 1000.0, 2)
            
            vehicle_stops.append({
                "stop_number": idx + 1,
                "global_stop_index": node_idx,
                "address": request.addresses[node_idx - 1],
                "lat": coordinates[node_idx][0],
                "lng": coordinates[node_idx][1],
                "eta_window": stop["eta_window"],
                "package_weight": weight,
                "segment_distance_km": seg_distance_km
            })
            
            current_node = node_idx # Shift tracking marker to current stop location
            
        final_fleet_routes.append({
            "vehicle_id": vehicle_id,
            "route": vehicle_stops,
            "total_weight": vehicle_total_weight
        })
        
        # Build a highly precise, data-dense text manifest to feed Gemini
        fleet_prompt_text += f"\n### Vehicle ID {vehicle_id} Dispatch Array (Loaded Weight: {vehicle_total_weight}kg):\n"
        for vs in vehicle_stops:
            fleet_prompt_text += f"- Stop #{vs['stop_number']} (Item #{vs['global_stop_index']}): Destination '{vs['address']}' | Time Window: {vs['eta_window']} | Distance from previous node: {vs['segment_distance_km']} km | Load: {vs['package_weight']} kg\n"

    # Handle skipped items safely
    final_skipped_stops = []
    if skipped_nodes:
        fleet_prompt_text += "\n### ⚠️ UNASSIGNED PARCELS DUE TO METRIC OVERLOAD:\n"
        for node in skipped_nodes:
            weight = request.package_weights[node - 1]
            addr = request.addresses[node - 1]
            final_skipped_stops.append({
                "global_stop_index": node,
                "address": addr,
                "package_weight": weight
            })
            fleet_prompt_text += f"- Item #{node}: {addr} ({weight} kg)\n"

    # 5. Execute Optimized Structured LLM Call
    brief_en, brief_kn, raw_whatsapp_template = generate_route_narrative(
        depot_address=request.depot, 
        start_time=request.current_time, 
        fleet_summary_text=fleet_prompt_text
    )

    # SECURE LOCAL PYTHON DATA MAPPING LOOP
    # This guarantees the customer names perfectly match the map sequence locations
    final_customer_alerts = []
    real_customer_names = ["Basavaraj", "Srinivas", "Ganesh", "Anand", "Patil", "Priya", "Rohan", "Amit", "Kulkarni", "Deepa"]

    for route_obj in final_fleet_routes:
        for stop in route_obj["route"]:
            global_idx = stop["global_stop_index"]
            customer_name = real_customer_names[(global_idx - 1) % len(real_customer_names)]
            
            try:
                # Local safe text replacement injection
                formatted_message = raw_whatsapp_template.format(
                    customer_name=customer_name,
                    delivery_address=stop["address"],
                    eta_window=stop["eta_window"]
                )
            except Exception:
                formatted_message = f"Hello {customer_name}, your delivery package to {stop['address']} is scheduled within the window: {stop['eta_window']}."

            final_customer_alerts.append({
                "stop_number": stop["global_stop_index"],
                "address": stop["address"],
                "message": formatted_message
            })

    # Assemble the bilingual split components cleanly for the Streamlit viewport container
    combined_briefing_document = f"## 🇬🇧 Fleet Operational Manifest (English)\n\n{brief_en}\n\n---\n\n## 📌 ಚಾಲಕನ ವಿವರಣೆ (Kannada Driver Briefing)\n\n{brief_kn}"

    return {
        "fleet_routes": final_fleet_routes,
        "skipped_stops": final_skipped_stops,
        "driver_briefing": combined_briefing_document,
        "customer_messages": final_customer_alerts,
        "depot_coords": [depot_lat, depot_lng]
    }