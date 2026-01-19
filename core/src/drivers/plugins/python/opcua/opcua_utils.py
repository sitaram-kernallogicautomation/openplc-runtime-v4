"""OPC-UA plugin utility functions."""

import ctypes
import os
import sys
import struct
from typing import Any
from asyncua import ua

# Add directories to path for module access
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

# Import logging (handle both package and direct loading)
try:
    from .opcua_logging import log_info, log_warn, log_error
except ImportError:
    from opcua_logging import log_info, log_warn, log_error


# TIME-related datatypes that use IEC_TIMESPEC structure
TIME_DATATYPES = frozenset(["TIME", "DATE", "TOD", "DT"])


def map_plc_to_opcua_type(plc_type: str) -> ua.VariantType:
    """Map plc datatype to OPC-UA VariantType."""
    type_mapping = {
        "BOOL": ua.VariantType.Boolean,
        "BYTE": ua.VariantType.Byte,
        "INT": ua.VariantType.Int16,
        "INT32": ua.VariantType.Int32,
        "DINT": ua.VariantType.Int32,
        "LINT": ua.VariantType.Int64,
        "FLOAT": ua.VariantType.Float,
        "REAL": ua.VariantType.Float,  # IEC 61131-3 REAL = 32-bit float
        "STRING": ua.VariantType.String,
        # TIME-related types - represented as Int64 (milliseconds for duration types)
        "TIME": ua.VariantType.Int64,  # Duration in milliseconds
        "TOD": ua.VariantType.Int64,  # Time of day in milliseconds since midnight
        "DATE": ua.VariantType.DateTime,  # Date as OPC-UA DateTime
        "DT": ua.VariantType.DateTime,  # Date and Time as OPC-UA DateTime
    }
    mapped_type = type_mapping.get(plc_type.upper(), ua.VariantType.Variant)
    return mapped_type


def timespec_to_milliseconds(tv_sec: int, tv_nsec: int) -> int:
    """
    Convert IEC_TIMESPEC (tv_sec, tv_nsec) to milliseconds.

    Args:
        tv_sec: Seconds component
        tv_nsec: Nanoseconds component

    Returns:
        Total time in milliseconds
    """
    return (tv_sec * 1000) + (tv_nsec // 1_000_000)


def milliseconds_to_timespec(ms: int) -> tuple:
    """
    Convert milliseconds to IEC_TIMESPEC format (tv_sec, tv_nsec).

    Args:
        ms: Time in milliseconds

    Returns:
        Tuple of (tv_sec, tv_nsec)
    """
    tv_sec = ms // 1000
    tv_nsec = (ms % 1000) * 1_000_000
    return (tv_sec, tv_nsec)


def convert_value_for_opcua(datatype: str, value: Any) -> Any:
    """Convert PLC debug variable value to OPC-UA compatible format."""
    # The debug utils return raw integer values based on variable size
    # Convert to appropriate OPC-UA types based on config datatype
    try:
        if datatype.upper() in ["BOOL", "Bool"]:
            # Ensure BOOL values are proper Python booleans
            if isinstance(value, bool):
                return value
            elif isinstance(value, (int, float)):
                return bool(value != 0)
            else:
                return bool(value)
        
        elif datatype.upper() in ["BYTE", "Byte"]:
            # Ensure proper uint8 type for OPC-UA compatibility
            return ctypes.c_uint8(max(0, min(255, int(value)))).value
        
        elif datatype.upper() in ["INT", "Int"]:
            # Ensure proper int16 type - critical for OPC-UA compatibility
            clamped_value = max(-32768, min(32767, int(value)))
            return ctypes.c_int16(clamped_value).value
        
        elif datatype.upper() in ["DINT", "Dint", "INT32", "Int32"]:
            # Ensure proper int32 type for OPC-UA compatibility
            clamped_value = max(-2147483648, min(2147483647, int(value)))
            return ctypes.c_int32(clamped_value).value
        
        elif datatype.upper() in ["LINT", "Lint"]:
            return int(value)  # int64
        
        elif datatype.upper() in ["FLOAT", "REAL"]:
            # Float/Real values are stored as integers in debug variables
            # Convert back to float if it's an integer representation
            if isinstance(value, int):
                try:
                    return struct.unpack('f', struct.pack('I', value))[0]
                except:
                    return float(value)
            return float(value)
        
        elif datatype.upper() in ["STRING", "String"]:
            return str(value)

        elif datatype.upper() == "TIME":
            # TIME values are stored as IEC_TIMESPEC (tv_sec, tv_nsec)
            # Convert to milliseconds for OPC-UA Int64 representation
            if isinstance(value, tuple) and len(value) == 2:
                tv_sec, tv_nsec = value
                return timespec_to_milliseconds(tv_sec, tv_nsec)
            elif isinstance(value, int):
                # If already an integer, assume it's milliseconds
                return value
            return 0

        elif datatype.upper() == "TOD":
            # TOD (Time of Day) - milliseconds since midnight
            if isinstance(value, tuple) and len(value) == 2:
                tv_sec, tv_nsec = value
                return timespec_to_milliseconds(tv_sec, tv_nsec)
            elif isinstance(value, int):
                return value
            return 0

        elif datatype.upper() in ["DATE", "DT"]:
            # DATE and DT map to OPC-UA DateTime
            # IEC_TIMESPEC stores seconds since epoch (1970-01-01)
            from datetime import datetime, timezone

            if isinstance(value, tuple) and len(value) == 2:
                tv_sec, tv_nsec = value
                # Convert to datetime object
                try:
                    dt = datetime.fromtimestamp(tv_sec, tz=timezone.utc)
                    # Add microseconds (nsec / 1000)
                    dt = dt.replace(microsecond=tv_nsec // 1000)
                    return dt
                except (OSError, OverflowError, ValueError):
                    # Invalid timestamp, return epoch
                    return datetime(1970, 1, 1, tzinfo=timezone.utc)
            elif isinstance(value, datetime):
                return value
            return datetime(1970, 1, 1, tzinfo=timezone.utc)

        else:
            return value

    except (ValueError, TypeError, OverflowError) as e:
        # If conversion fails, return a safe default
        log_warn(f"Failed to convert value {value} to OPC-UA format for {datatype}: {e}")
        if datatype.upper() == "BOOL":
            return False
        elif datatype.upper() in ["FLOAT", "REAL"]:
            return 0.0
        elif datatype.upper() == "STRING":
            return ""
        elif datatype.upper() in TIME_DATATYPES:
            return 0
        else:
            return 0


def convert_value_for_plc(datatype: str, value: Any) -> Any:
    """Convert OPC-UA value to PLC debug variable format."""
    # Handle different OPC-UA value types more robustly
    try:
        if datatype.upper() in ["BOOL", "Bool"]:
            # Convert any value to boolean, then to int (0/1)
            if isinstance(value, bool):
                return int(value)
            elif isinstance(value, (int, float)):
                return 1 if value != 0 else 0
            elif isinstance(value, str):
                return 1 if value.lower() in ['true', '1', 'yes', 'on'] else 0
            else:
                return int(bool(value))
        
        elif datatype.upper() in ["BYTE", "Byte"]:
            # Ensure proper uint8 type for PLC compatibility
            return ctypes.c_uint8(max(0, min(255, int(value)))).value
        
        elif datatype.upper() in ["INT", "Int"]:
            # Ensure proper int16 type for PLC compatibility  
            clamped_value = max(-32768, min(32767, int(value)))
            return ctypes.c_int16(clamped_value).value
        
        elif datatype.upper() in ["DINT", "Dint", "INT32", "Int32"]:
            # Ensure proper int32 type for PLC compatibility
            clamped_value = max(-2147483648, min(2147483647, int(value)))
            return ctypes.c_int32(clamped_value).value
        
        elif datatype.upper() in ["LINT", "Lint"]:
            return int(value)  # int64
        
        elif datatype.upper() in ["FLOAT", "REAL"]:
            # Convert float to int representation for storage
            if isinstance(value, float):
                try:
                    return struct.unpack('I', struct.pack('f', value))[0]
                except:
                    return int(value)
            else:
                return int(float(value))
        
        elif datatype.upper() in ["STRING", "String"]:
            return str(value)

        elif datatype.upper() == "TIME":
            # Convert OPC-UA milliseconds (Int64) to IEC_TIMESPEC tuple
            ms = int(value)
            return milliseconds_to_timespec(ms)

        elif datatype.upper() == "TOD":
            # TOD (Time of Day) - convert milliseconds to timespec
            ms = int(value)
            return milliseconds_to_timespec(ms)

        elif datatype.upper() in ["DATE", "DT"]:
            # Convert OPC-UA DateTime to IEC_TIMESPEC tuple
            from datetime import datetime, timezone

            if isinstance(value, datetime):
                # Convert datetime to seconds since epoch
                tv_sec = int(value.timestamp())
                tv_nsec = value.microsecond * 1000
                return (tv_sec, tv_nsec)
            elif isinstance(value, (int, float)):
                # Assume it's a timestamp
                return (int(value), 0)
            return (0, 0)

        else:
            # For unknown types, try to preserve the value
            return value

    except (ValueError, TypeError, OverflowError) as e:
        # If conversion fails, log and return a safe default
        log_warn(f"Failed to convert value {value} to {datatype}, using default: {e}")
        if datatype.upper() == "BOOL":
            return 0
        elif datatype.upper() in ["FLOAT", "REAL"]:
            return 0
        elif datatype.upper() == "STRING":
            return ""
        elif datatype.upper() in TIME_DATATYPES:
            return (0, 0)
        else:
            return 0


def infer_var_type(size: int) -> str:
    """
    Infer variable type from size.

    Args:
        size: Size of the variable in bytes

    Returns:
        String indicating the inferred type or type category
    """
    if size == 1:
        return "BOOL_OR_SINT"
    elif size == 2:
        return "UINT16"
    elif size == 4:
        return "UINT32_OR_TIME"
    elif size == 8:
        return "UINT64_OR_TIME"
    elif size == 127:
        # IEC_STRING: 1 byte len + 126 bytes body = 127 bytes
        return "STRING"
    else:
        return "UNKNOWN"
