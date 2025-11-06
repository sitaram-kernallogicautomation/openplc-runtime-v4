import pytest
from modbus_master_plugin import (
    get_batch_read_requests_from_io_points,
    get_batch_write_requests_from_io_points,
    ModbusSlaveDevice
)

def test_get_batch_read_requests_from_io_points():
    print("\n--- Testing get_batch_read_requests_from_io_points ---")
    io_points = [{
        "io_points": [
            {
                "fc": 1,
                "offset": "0x0001",
                "iec_location": "%IX0.0",
                "len": 8
            },
            {
                "fc": 5,
                "offset": "0x0010",
                "iec_location": "%QX0.0",
                "len": 1
            }
        ]
    }]
    requests = get_batch_read_requests_from_io_points(io_points)
    for req in requests:
        print(req)