import pytest
from modbus_master_plugin import (
    get_batch_read_requests_from_io_points,
    get_batch_write_requests_from_io_points,
    ModbusSlaveDevice,
    safe_buffer_accessor,
    modbus_master_config
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


def test_get_batch_write_requests_from_io_points():
    print("\n--- Testing get_batch_write_requests_from_io_points ---")
    io_points = [
            {
                "fc": 15,
                "offset": "0x0020",
                "iec_location": "%QX0.0",
                "len": 4
            },
            {
                "fc": 6,
                "offset": "0x0030",
                "iec_location": "%MW0",
                "len": 2
            }
        ]
    requests = get_batch_write_requests_from_io_points(io_points)
    for req in requests:
        print(req)

def test_modbus_slave_device_initialization():
    print("\n--- Testing ModbusSlaveDevice Initialization ---")
    for device_config in modbus_master_config.devices:
        try:
            device = ModbusSlaveDevice(device_config, safe_buffer_accessor)
            print(device)
        except Exception as e:
            print(f"Error initializing ModbusSlaveDevice: {e}")
        
        assert device_config.name == "TestModbusSlave"