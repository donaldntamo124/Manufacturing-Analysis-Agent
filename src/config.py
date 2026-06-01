"""
Configuration module for Manufacturing Analysis Agent.
Defines the standard data schema and column mapping rules.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List


@dataclass
class StandardSchema:
    """Standard schema for manufacturing data after normalization."""
    job_id: str
    process_step: str
    machine: str
    operator: str
    start_time: datetime
    end_time: datetime
    quantity: float
    status: str
    due_date: datetime
    wip_location: str


# Mapping hints for column inference: standard field name -> list of common user column names
SCHEMA_MAPPING_HINTS = {
    "job_id": [
        "Job ID",
        "Job No",
        "Job Number",
        "Order ID",
        "Order Number",
        "Work Order",
        "WO",
        "Job",
        "Order",
    ],
    "process_step": [
        "Process Step",
        "Operation",
        "Operation Name",
        "Process",
        "Step",
        "Stage",
        "Phase",
        "Activity",
    ],
    "machine": [
        "Machine",
        "Machine Name",
        "Work Centre",
        "Work Center",
        "Equipment",
        "Station",
        "Resource",
    ],
    "operator": [
        "Operator",
        "Operator Name",
        "Employee",
        "Worker",
        "Staff",
        "Person",
        "Assigned To",
    ],
    "start_time": [
        "Start Time",
        "Start Date",
        "Start DateTime",
        "Begin Time",
        "Begin Date",
        "Scheduled Start",
        "Started",
    ],
    "end_time": [
        "End Time",
        "End Date",
        "End DateTime",
        "Finish Time",
        "Finish Date",
        "Complete Time",
        "Completion Time",
        "Finished",
        "Completed",
    ],
    "quantity": [
        "Quantity",
        "Qty",
        "Amount",
        "Volume",
        "Units",
        "Pieces",
    ],
    "status": [
        "Status",
        "State",
        "Progress",
        "Current Status",
        "Job Status",
    ],
    "due_date": [
        "Due Date",
        "Due DateTime",
        "Deadline",
        "Target Date",
        "Expected Date",
        "Required By",
    ],
    "wip_location": [
        "WIP Location",
        "Current Location",
        "Current Step",
        "In Progress At",
        "Location",
        "Current Process",
    ],
}

# Required columns for MVP analysis to work
REQUIRED_COLUMNS = ["job_id", "process_step", "start_time", "end_time"]

# Fuzzy matching thresholds
FUZZY_MATCH_THRESHOLDS = {
    "auto_map": 85,  # Confidence >= 85% → auto-map without asking user
    "suggest": 60,   # Confidence 60-85% → suggest to user, ask for confirmation
    "ask": 60,       # Confidence < 60% → ask user directly
}

# Application constants
MAX_PREVIEW_ROWS = 5
ALLOWED_DATETIME_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%d-%m-%Y %H:%M:%S",
    "%d-%m-%Y",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y",
]
