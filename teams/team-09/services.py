import time
import os
import requests
from typing import List, Tuple, Dict, Any
from datetime import datetime, timedelta, time as dt_time
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2

# ---------------------------------------------------------------------------
# 1. PYDANTIC SCHEMAS FOR STRUCTURED LLM OUTPUT
# ---------------------------------------------------------------------------
class CustomerRouteRecord(BaseModel):
    stop_ref: int = Field(..., description="The original request item line number reference (1 to 10)")
    customer_name: str = Field(..., description="A common North Karnataka resident name generated for the recipient (e.g., Basavaraj, Shrinivas, Patil, Amit)")
    address: str = Field(..., description="The exact destination address string")
    eta_window: str = Field(..., description="The assigned 15-minute delivery ETA window")

class RouteNarrativeOutput(BaseModel):
    driver_briefing_english: str = Field(
        ..., 
        description="Highly structured, compact manifest line items for the driver fleet in English. Strictly no driving directions or road turn instructions. No emojis."
    )
    driver_briefing_kannada: str = Field(
        ..., 
        description="The exact same structured manifest line items translated into clear, professional Kannada. Strictly no driving directions. No emojis."
    )
    whatsapp_template: str = Field(
        ...,
        description="A clean, professional-cum-casual uniform text message template string. Must contain the literal tags {customer_name}, {delivery_address}, and {eta_window}. No emojis."
    )

# Custom Exception for Geocoding Errors
class GeocodingError(Exception):
    def __init__(self, address: str, message: str = "Address could not be geocoded"):
        self.address = address
        self.message = message
        super().__init__(f"{message}: {address}")

# ---------------------------------------------------------------------------
# 2. CORE LOGISTICS SERVICES
# ---------------------------------------------------------------------------
def geocode_address(address: str) -> Tuple[float, float]:
    """
    Geocodes a single address string using Nominatim (OSM) with rate-limiting.
    Appends Hubli, Karnataka context to assist matching when not already present.
    """
    query_address = address
    if "hubli" not in address.lower() and "hubballi" not in address.lower():
        query_address = f"{address}, Hubli, Karnataka, India"

    print(f"Nominatim geocoding '{address}'...")
    time.sleep(1.0)  # Respect OSM rate-limit policy

    nom_headers = {
        "User-Agent": "HubliLastMileRouteOptimizer/1.0 (delivery-route-optimization-backend-agent)"
    }
    nom_params: Dict[str, Any] = {"q": query_address, "format": "json", "limit": 1}

    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params=nom_params,
            headers=nom_headers,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        if not data and query_address != address:
            time.sleep(1.0)
            nom_params["q"] = address
            response = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params=nom_params,
                headers=nom_headers,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

        if not data:
            raise GeocodingError(address, "Nominatim returned no matching coordinates")

        lat = float(data[0]["lat"])
        lng = float(data[0]["lon"])
        return lat, lng

    except Exception as e:
        if isinstance(e, GeocodingError):
            raise e
        raise GeocodingError(address, f"Geocoding request failed: {str(e)}")

def get_distance_matrix(coordinates: List[Tuple[float, float]]) -> Tuple[List[List[float]], List[List[float]]]:
    """
    Queries OSRM Table API to retrieve the full NxN travel durations (seconds) 
    and distances (meters) matrices.
    """
    coords_str = ";".join([f"{lng},{lat}" for lat, lng in coordinates])
    url = f"http://router.project-osrm.org/table/v1/driving/{coords_str}?annotations=duration,distance"
    
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == "Ok":
            return data["durations"], data["distances"]
        else:
            raise ValueError(f"OSRM error response: {data.get('code')}")
            
    except Exception as primary_error:
        print(f"Primary OSRM query failed, attempting fallbacks. Error: {primary_error}")
        try:
            url_duration = f"http://router.project-osrm.org/table/v1/driving/{coords_str}?annotations=duration"
            res_dur = requests.get(url_duration, timeout=15)
            res_dur.raise_for_status()
            dur_data = res_dur.json()
            
            url_distance = f"http://router.project-osrm.org/table/v1/driving/{coords_str}?annotations=distance"
            res_dist = requests.get(url_distance, timeout=15)
            res_dist.raise_for_status()
            dist_data = res_dist.json()
            
            if dur_data.get("code") == "Ok" and dist_data.get("code") == "Ok":
                return dur_data["durations"], dist_data["distances"]
            else:
                raise ValueError("OSRM fallback responses were not Ok")
        except Exception as fallback_error:
            raise ValueError(f"All OSRM queries failed. Details: {fallback_error}")

def solve_cvrp(
    durations: List[List[float]],
    package_weights: List[int],
    vehicle_capacity: int,
    num_vehicles: int = 3
) -> Tuple[Dict[int, List[int]], List[int]]:
    """
    Solves a multi-vehicle CVRP with soft drop disjunction constraints.
    """
    num_nodes = len(durations)
    depot = 0
    
    manager = pywrapcp.RoutingIndexManager(num_nodes, num_vehicles, depot)
    routing = pywrapcp.RoutingModel(manager)
    
    def transit_callback(from_index, to_index):
        return int(round(durations[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]))
    transit_idx = routing.RegisterTransitCallback(transit_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_idx)
    
    def demand_callback(from_index):
        node = manager.IndexToNode(from_index)
        return 0 if node == 0 else package_weights[node - 1]
    demand_idx = routing.RegisterUnaryTransitCallback(demand_callback)
    
    routing.AddDimensionWithVehicleCapacity(
        demand_idx,
        0,
        [vehicle_capacity] * num_vehicles,
        True,
        "Capacity"
    )
    
    PENALTY = 1_000_000 
    for node in range(1, num_nodes):
        routing.AddDisjunction([manager.NodeToIndex(node)], PENALTY)
        
    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_params.time_limit.seconds = 5
    
    solution = routing.SolveWithParameters(search_params)
    if not solution:
        raise ValueError("The structural solver failed to establish an initial fleet configuration.")
        
    fleet_assignments = {}
    assigned_nodes = set()
    
    for vehicle_id in range(num_vehicles):
        index = routing.Start(vehicle_id)
        current_route = []
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node != 0:
                current_route.append(node)
                assigned_nodes.add(node)
            index = solution.Value(routing.NextVar(index))
        fleet_assignments[vehicle_id] = current_route
        
    skipped_nodes = [n for n in range(1, num_nodes) if n not in assigned_nodes]
    return fleet_assignments, skipped_nodes

def get_speed_for_time(departure_time: dt_time) -> float:
    """Returns driving speed in meters per second (m/s) based on departure time."""
    t_0600 = dt_time(6, 0)
    t_1000 = dt_time(10, 0)
    t_1700 = dt_time(17, 0)
    t_2100 = dt_time(21, 0)
    
    if t_0600 <= departure_time < t_1000:
        speed_kmph = 30.0
    elif t_1000 <= departure_time < t_1700:
        speed_kmph = 20.0
    elif t_1700 <= departure_time < t_2100:
        speed_kmph = 15.0
    else:
        speed_kmph = 35.0
        
    return speed_kmph * (1000.0 / 3600.0)

def calculate_route_etas(
    route_order: List[int],
    distances: List[List[float]],
    start_time_str: str
) -> List[Dict[str, Any]]:
    """Computes travel durations using the dynamic speed table and distances."""
    hour, minute = map(int, start_time_str.split(":"))
    current_dt = datetime.combine(datetime.today(), dt_time(hour, minute))
    
    stop_details = []
    current_node = 0
    
    for idx, stop_node in enumerate(route_order):
        dist_meters = distances[current_node][stop_node]
        speed_mps = get_speed_for_time(current_dt.time())
        travel_seconds = dist_meters / speed_mps
        arrival_dt = current_dt + timedelta(seconds=travel_seconds)
        
        minute_rounded = (arrival_dt.minute // 15) * 15
        window_start = arrival_dt.replace(minute=minute_rounded, second=0, microsecond=0)
        window_end = window_start + timedelta(minutes=15)
        
        eta_window_str = f"{window_start.strftime('%H:%M')} to {window_end.strftime('%H:%M')}"
        
        stop_details.append({
            "stop_number": idx + 1,
            "stop_node": stop_node,
            "arrival_time": arrival_dt,
            "eta_window": eta_window_str
        })
        
        current_dt = arrival_dt + timedelta(minutes=10)
        current_node = stop_node
        
    return stop_details

# ---------------------------------------------------------------------------
# 3. GENERATE LOGISTICS COMMUNICATIONS
# ---------------------------------------------------------------------------
def generate_route_narrative(
    depot_address: str,
    start_time: str,
    fleet_summary_text: str
) -> Tuple[str, str, str]:
    """
    Instructs Gemini 2.5 Flash to act as a strict logistics compiler.
    Eliminates road navigation turns, focuses purely on delivery manifests and templates.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=api_key, 
        temperature=0.15 # Lowered temperature for maximum programmatic accuracy
    )
    
    structured_llm = llm.with_structured_output(RouteNarrativeOutput)
    
    prompt = f"""
    You are a strict backend dispatch coordinator for a delivery fleet in Hubli, Karnataka.
    Review the following mathematically optimized route schedule generated by our engine:
    {fleet_summary_text}

    Generate three distinct string outputs matching these exact structural definitions:

    TASK 1: driver_briefing_english (Type: String)
    Compile a clean, crisp, high-density driver manifest. 
    CRITICAL RULE: Do not write any driving directions, highway instructions, or turn-by-turn guidance (e.g., do NOT say 'turn right', 'go down Gokul Road', or 'take the highway'). The driver already has a GPS map line tracking.
    Instead, format each stop strictly on its own new line using this precise structural pattern:
    * Stop #[No]: [Address] | ETA Window: [Window] | Segment Distance: [Pull the distance value exactly as provided in the schedule text] | Required Delivery Action: [Generate a highly specific, realistic, non-vague delivery operational instruction based on the location type, e.g., 'Deliver to the main ground floor reception desk, obtain signature from the manager on duty', 'Verify parcel package weight match with entry ledger at the warehouse cargo bay gate', 'Leave with household security guard at the gate if resident is unavailable']. No emojis.

    TASK 2: driver_briefing_kannada (Type: String)
    Translate the exact high-density manifest list from TASK 1 into professional, natural Kannada text. Maintain the identical layout structure, segment distance figures, and stop sequences. Ensure local Hubli area names remain clear and recognizable. No emojis.

    TASK 3: whatsapp_template (Type: String)
    Generate exactly ONE professional-cum-casual notification template text block to be used for customer text dispatches.
    - It must sound warm, polite, and reassuring.
    - It MUST include the literal text placeholders {{customer_name}}, {{delivery_address}}, and {{eta_window}} embedded naturally inside the sentence structure so our Python engine can process them locally.
    - Do not fill these tags with real names or data; leave the raw tag syntax intact. No emojis.
    Example text target: "Hello {{customer_name}}, your shipment from our central depot is out for delivery to {{delivery_address}}. Our courier partner is estimated to arrive at your location within the window of {{eta_window}}. Kindly ensure someone is available to collect the parcel."
    """
    
    try:
        result = structured_llm.invoke(prompt)
        return result.driver_briefing_english, result.driver_briefing_kannada, result.whatsapp_template
    except Exception as e:
        print(f"Structured LLM compilation breakdown, hitting system safety fallback: {e}")
        fallback_brief = f"### Route Summary Plan\n\n{fleet_summary_text}"
        fallback_tpl = "Hello {{customer_name}}, your order heading to {{delivery_address}} is scheduled for delivery within the window {{eta_window}}."
        return fallback_brief, fallback_brief, fallback_tpl