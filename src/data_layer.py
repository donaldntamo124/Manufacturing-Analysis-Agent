"""
Data layer for Excel file handling and column mapping.
Handles reading Excel files, column inference, and data standardization.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import pytz
from fuzzywuzzy import fuzz

from src.config import (
    SCHEMA_MAPPING_HINTS,
    REQUIRED_COLUMNS,
    FUZZY_MATCH_THRESHOLDS,
    ALLOWED_DATETIME_FORMATS,
    MAX_PREVIEW_ROWS,
)


def read_excel_file(file_path: str) -> Dict[str, any]:
    """
    Read an Excel file and return metadata about available sheets.
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        Dictionary with keys:
        - sheets: List of sheet names
        - file_name: Name of the file
        - file_size: Size in bytes
    """
    file_path = Path(file_path)
    
    try:
        excel_file = pd.ExcelFile(file_path)
        return {
            "sheets": excel_file.sheet_names,
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size,
        }
    except Exception as e:
        raise ValueError(f"Failed to read Excel file: {str(e)}")


def preview_sheet(file_path: str, sheet_name: str, rows: int = MAX_PREVIEW_ROWS) -> pd.DataFrame:
    """
    Preview the first N rows of a specific sheet.
    
    Args:
        file_path: Path to the Excel file
        sheet_name: Name of the sheet to preview
        rows: Number of rows to preview (default: 5)
        
    Returns:
        DataFrame with first N rows
    """
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=rows)
        return df
    except Exception as e:
        raise ValueError(f"Failed to preview sheet '{sheet_name}': {str(e)}")


def infer_column_mapping(columns: List[str]) -> Dict[str, Tuple[str, float]]:
    """
    Infer a mapping from user columns to standard schema fields using fuzzy matching.
    
    Args:
        columns: List of column names from the user's Excel file
        
    Returns:
        Dictionary mapping schema field names to tuples of (user_column, confidence_score).
        Confidence score is 0-100. Only includes matches >= FUZZY_MATCH_THRESHOLDS["suggest"].
    """
    mapping = {}
    
    for schema_field, hints in SCHEMA_MAPPING_HINTS.items():
        best_match = None
        best_score = 0
        
        for user_col in columns:
            for hint in hints:
                # Use token_set_ratio for more flexible matching
                score = fuzz.token_set_ratio(user_col.lower(), hint.lower())
                
                if score > best_score:
                    best_score = score
                    best_match = user_col
        
        # Only include if score meets minimum threshold for suggestions
        if best_score >= FUZZY_MATCH_THRESHOLDS["suggest"]:
            mapping[schema_field] = (best_match, best_score)
    
    return mapping


def validate_required_columns(mapping: Dict[str, Tuple[str, float]]) -> Tuple[bool, List[str]]:
    """
    Check if all required columns are present in the mapping.
    
    Args:
        mapping: Column mapping returned by infer_column_mapping()
        
    Returns:
        Tuple of (is_valid: bool, missing_columns: List[str])
    """
    missing = []
    
    for required_col in REQUIRED_COLUMNS:
        if required_col not in mapping:
            missing.append(required_col)
    
    return (len(missing) == 0, missing)


def _parse_datetime(value: any) -> Optional[datetime]:
    """
    Helper function to parse datetime values from various formats.
    Handles both string and Excel datetime formats.
    """
    if pd.isna(value):
        return None
    
    # If already a datetime, return it
    if isinstance(value, datetime):
        return value
    
    # Try parsing as string
    if isinstance(value, str):
        for fmt in ALLOWED_DATETIME_FORMATS:
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
        # If no format matched, raise error
        raise ValueError(f"Could not parse datetime: {value}")
    
    # Try converting to string first (handles Excel numeric dates)
    try:
        str_value = str(value)
        for fmt in ALLOWED_DATETIME_FORMATS:
            try:
                return datetime.strptime(str_value, fmt)
            except ValueError:
                continue
    except Exception:
        pass
    
    raise ValueError(f"Could not parse datetime: {value}")


def clean_and_standardize_data(
    df: pd.DataFrame,
    mapping: Dict[str, Tuple[str, float]],
) -> pd.DataFrame:
    """
    Clean and standardize data according to the schema.
    Renames columns, casts types, and handles nulls.
    
    Args:
        df: Raw DataFrame from Excel
        mapping: Column mapping (schema_field -> (user_column, confidence))
        
    Returns:
        Cleaned DataFrame with standard column names and proper types
    """
    # Create a copy to avoid modifying original
    df = df.copy()
    
    # Rename columns according to mapping
    rename_dict = {}
    for schema_field, (user_column, _) in mapping.items():
        if user_column in df.columns:
            rename_dict[user_column] = schema_field
    
    df = df.rename(columns=rename_dict)
    
    # Select only mapped columns (drop unmapped columns)
    mapped_columns = [col for col in df.columns if col in rename_dict.values()]
    df = df[mapped_columns]
    
    # Type casting
    if "quantity" in df.columns:
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    
    # Parse datetime columns
    for datetime_col in ["start_time", "end_time", "due_date"]:
        if datetime_col in df.columns:
            try:
                df[datetime_col] = df[datetime_col].apply(_parse_datetime)
            except Exception as e:
                raise ValueError(f"Failed to parse {datetime_col}: {str(e)}")
    
    # Drop rows with missing required fields
    for required_col in REQUIRED_COLUMNS:
        if required_col in df.columns:
            df = df.dropna(subset=[required_col])
    
    # Reset index
    df = df.reset_index(drop=True)
    
    return df
