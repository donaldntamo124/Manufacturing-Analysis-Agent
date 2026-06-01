"""
Test data fixture generator for Manufacturing Analysis Agent.
Creates sample Excel files for testing and demonstration.
"""

import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_simple_production_data():
    """
    Create a simple, clean production dataset with standard column names.
    """
    data = {
        "Job ID": ["J001", "J002", "J003", "J004", "J005"],
        "Process Step": ["Assembly", "Testing", "Assembly", "Packaging", "Assembly"],
        "Machine": ["Lathe-1", "Test-A", "Lathe-1", "Pack-1", "Drill-2"],
        "Operator": ["Alice", "Bob", "Alice", "Charlie", "David"],
        "Start Time": [
            datetime(2024, 1, 1, 8, 0),
            datetime(2024, 1, 1, 9, 30),
            datetime(2024, 1, 1, 10, 15),
            datetime(2024, 1, 1, 12, 0),
            datetime(2024, 1, 1, 13, 45),
        ],
        "End Time": [
            datetime(2024, 1, 1, 10, 15),
            datetime(2024, 1, 1, 11, 45),
            datetime(2024, 1, 1, 12, 30),
            datetime(2024, 1, 1, 13, 15),
            datetime(2024, 1, 1, 15, 0),
        ],
        "Quantity": [100, 100, 100, 100, 100],
        "Status": ["Completed", "Completed", "Completed", "Completed", "Completed"],
        "Due Date": [
            datetime(2024, 1, 1, 18, 0),
            datetime(2024, 1, 1, 17, 0),
            datetime(2024, 1, 1, 17, 0),
            datetime(2024, 1, 1, 16, 0),
            datetime(2024, 1, 1, 18, 0),
        ],
    }
    
    df = pd.DataFrame(data)
    return df


def create_messy_schedule_data():
    """
    Create a dataset with non-standard column names to test fuzzy matching.
    """
    data = {
        "Job No": ["WO-001", "WO-002", "WO-003", "WO-004"],
        "Operation": ["Fabrication", "Welding", "Fabrication", "QC Testing"],
        "Work Centre": ["Station-A", "Station-B", "Station-A", "Lab-1"],
        "Employee": ["John", "Maria", "John", "Lisa"],
        "Begin DateTime": [
            datetime(2024, 1, 2, 7, 0),
            datetime(2024, 1, 2, 9, 15),
            datetime(2024, 1, 2, 11, 0),
            datetime(2024, 1, 2, 14, 30),
        ],
        "Finish DateTime": [
            datetime(2024, 1, 2, 9, 30),
            datetime(2024, 1, 2, 12, 45),
            datetime(2024, 1, 2, 13, 20),
            datetime(2024, 1, 2, 15, 45),
        ],
        "Amount": [50, 75, 60, 50],
        "Current Status": ["Done", "Done", "In Progress", "Done"],
        "Target Date": [
            datetime(2024, 1, 2, 20, 0),
            datetime(2024, 1, 2, 19, 0),
            datetime(2024, 1, 2, 18, 0),
            datetime(2024, 1, 2, 17, 0),
        ],
    }
    
    df = pd.DataFrame(data)
    return df


def create_delayed_jobs_data():
    """
    Create a dataset with delayed jobs to test delay detection.
    """
    base_date = datetime(2024, 1, 3)
    
    data = {
        "Job ID": ["J101", "J102", "J103", "J104", "J105"],
        "Process Step": ["Assembly", "Testing", "Assembly", "Packaging", "Assembly"],
        "Machine": ["Line-1", "Test-1", "Line-1", "Pack-1", "Line-2"],
        "Operator": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "Start Time": [
            base_date + timedelta(hours=0),
            base_date + timedelta(hours=2),
            base_date + timedelta(hours=4),
            base_date + timedelta(hours=6),
            base_date + timedelta(hours=8),
        ],
        "End Time": [
            base_date + timedelta(hours=3),   # On time
            base_date + timedelta(hours=6),   # On time
            base_date + timedelta(hours=9),   # 2 hours late
            base_date + timedelta(hours=10),  # 1 hour late
            base_date + timedelta(hours=12),  # On time
        ],
        "Quantity": [100, 100, 100, 100, 100],
        "Status": ["Completed", "Completed", "Late", "Delayed", "Completed"],
        "Due Date": [
            base_date + timedelta(hours=3),   # Due at 3h
            base_date + timedelta(hours=6),   # Due at 6h
            base_date + timedelta(hours=7),   # Due at 7h (3h missed)
            base_date + timedelta(hours=9),   # Due at 9h (1h missed)
            base_date + timedelta(hours=12),  # Due at 12h
        ],
    }
    
    df = pd.DataFrame(data)
    return df


def create_bottleneck_data():
    """
    Create a dataset that highlights a bottleneck process.
    """
    base_date = datetime(2024, 1, 4)
    
    # Assembly is fast, Testing is slow (bottleneck)
    data = []
    for i in range(10):
        start = base_date + timedelta(hours=i, minutes=0)
        
        # Assembly: 30 minutes
        data.append({
            "Job ID": f"B{i:03d}",
            "Process Step": "Assembly",
            "Machine": "Assembly-Line",
            "Operator": "Operator-A",
            "Start Time": start,
            "End Time": start + timedelta(minutes=30),
            "Quantity": 100,
            "Status": "Completed",
            "Due Date": start + timedelta(hours=12),
        })
        
        # Testing: 120 minutes (BOTTLENECK!)
        start2 = start + timedelta(minutes=30)
        data.append({
            "Job ID": f"B{i:03d}",
            "Process Step": "Testing",
            "Machine": "Test-Station",
            "Operator": "Operator-B",
            "Start Time": start2,
            "End Time": start2 + timedelta(minutes=120),
            "Quantity": 100,
            "Status": "Completed",
            "Due Date": start + timedelta(hours=12),
        })
    
    df = pd.DataFrame(data)
    return df


def generate_all_fixtures():
    """Generate and save all test fixture files."""
    fixtures_dir = Path(__file__).parent
    
    print("Generating test fixtures...")
    
    # Create simple_production.xlsx
    df = create_simple_production_data()
    path = fixtures_dir / "simple_production.xlsx"
    df.to_excel(path, index=False, sheet_name="Production")
    print(f"Created {path}")
    
    # Create messy_schedule.xlsx
    df = create_messy_schedule_data()
    path = fixtures_dir / "messy_schedule.xlsx"
    df.to_excel(path, index=False, sheet_name="Schedule")
    print(f"Created {path}")
    
    # Create delayed_jobs.xlsx
    df = create_delayed_jobs_data()
    path = fixtures_dir / "delayed_jobs.xlsx"
    df.to_excel(path, index=False, sheet_name="Jobs")
    print(f"Created {path}")
    
    # Create bottleneck_scenario.xlsx
    df = create_bottleneck_data()
    path = fixtures_dir / "bottleneck_scenario.xlsx"
    df.to_excel(path, index=False, sheet_name="Production")
    print(f"Created {path}")
    
    print("\nAll fixtures generated successfully!")


if __name__ == "__main__":
    generate_all_fixtures()
