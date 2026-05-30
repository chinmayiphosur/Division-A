from pydantic import BaseModel, Field, field_validator
from typing import List
import re

# ---------------------------------------------------------------------------
# 1. REQUEST SCHEMA
# ---------------------------------------------------------------------------
class RouteOptimizationRequest(BaseModel):
    depot: str = Field(..., description="The starting depot address string")
    current_time: str = Field(..., description="Start time in HH:MM format")
    vehicle_capacity: int = Field(..., description="Maximum capacity per vehicle in kg")
    addresses: List[str] = Field(..., description="List of exactly 10 delivery addresses")
    package_weights: List[int] = Field(..., description="List of exactly 10 package weights")
    num_vehicles: int = Field(default=3, description="Number of active vehicles in the fleet")

    @field_validator('addresses')
    def validate_addresses_count(cls, v):
        if len(v) != 10:
            raise ValueError("Exactly 10 delivery addresses must be provided.")
        for addr in v:
            if not addr or not addr.strip():
                raise ValueError("Address strings cannot be empty or whitespace-only.")
        return v

    @field_validator('package_weights')
    def validate_package_weights(cls, v):
        if len(v) != 10:
            raise ValueError("Exactly 10 package weights must be provided.")
        for weight in v:
            if weight < 0:
                raise ValueError("Package weights cannot be negative.")
        return v

    @field_validator('current_time')
    def validate_current_time(cls, v):
        if not re.match(r"^(?:[01]\d|2[0-3]):[0-5]\d$", v):
            raise ValueError("Current time must be in HH:MM 24-hour format.")
        return v


# ---------------------------------------------------------------------------
# 2. SUPPORTING SUB-SCHEMAS
# ---------------------------------------------------------------------------
class StopInfo(BaseModel):
    stop_number: int = Field(..., description="1-based sequence order within this specific vehicle's route")
    global_stop_index: int = Field(..., description="Original 1-based index (1 to 10) from the request list")
    address: str = Field(..., description="The geocoded address")
    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")
    eta_window: str = Field(..., description="Dynamic 15-minute delivery window")
    package_weight: int = Field(..., description="Weight of the package for this stop")


class VehicleRoute(BaseModel):
    vehicle_id: int = Field(..., description="0-indexed vehicle identifier")
    route: List[StopInfo] = Field(..., description="Ordered list of delivery stops for this vehicle")
    total_weight: int = Field(..., description="Total package weight assigned to this vehicle")


class SkippedStop(BaseModel):
    global_stop_index: int = Field(..., description="Original 1-based index of the unassigned delivery")
    address: str = Field(..., description="Address that could not be serviced due to fleet capacity constraints")
    package_weight: int = Field(..., description="Weight of the unserviced package")


# ---------------------------------------------------------------------------
# 3. RESPONSE SCHEMA
# ---------------------------------------------------------------------------
class RouteOptimizationResponse(BaseModel):
    fleet_routes: List[VehicleRoute] = Field(..., description="Optimized routes broken down by vehicle fleet allocation")
    skipped_stops: List[SkippedStop] = Field(..., description="Stops dropped by the solver due to capacity limits")
    driver_briefing: str = Field(..., description="A collective markdown fleet briefing narrative in English and Kannada")
    customer_messages: List[dict] = Field(..., description="The flat collection of customer text alerts generated locally using the template")
    depot_coords: List[float] = Field(..., description="Geocoded [lat, lng] coordinates of the starting depot")