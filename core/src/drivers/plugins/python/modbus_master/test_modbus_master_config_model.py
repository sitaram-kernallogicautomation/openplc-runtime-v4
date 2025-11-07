import pytest
import sys
import os
from modbus_master_plugin import (
    get_batch_read_requests_from_io_points,
    get_batch_write_requests_from_io_points,
    ModbusSlaveDevice,
    safe_buffer_accessor,
    modbus_master_config
)

# Add the parent directory to Python path to find shared module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
# Import the configuration model
from shared.plugin_config_decode.modbus_master_config_model import (
    ModbusIoPointConfig,
    ModbusMasterConfig,
    ModbusDeviceConfig,
    IECAddress
)


def test_modbus_io_point_config_from_dict():
    print("\n--- Testing ModbusIoPointConfig.from_dict ---")
    io_point_data = {
        "fc": 3,
        "offset": "0xB00A",
        "iec_location": "%MW10",
        "len": 5
    }
    io_point = ModbusIoPointConfig.from_dict(data=io_point_data)
    print(io_point)
    assert io_point.fc == 3
    assert io_point.offset == "0xB00A"
    assert ("%" + str(io_point.iec_location.area) +
            str(io_point.iec_location.size) + 
            str(io_point.iec_location.byte)) == "%MW10"
    assert io_point.length == 5

def test_modbus_master_config_import():
    print("\n--- Testing ModbusMasterConfig.import_config_from_file ---")
    config_file_path = os.path.join(os.path.dirname(__file__), 'test_modbus_master_config.json')
    modbus_config = ModbusMasterConfig()
    modbus_config.import_config_from_file(config_file_path)
    
    print(f"Imported {len(modbus_config.devices)} devices.")
    for device in modbus_config.devices:
        print(device)
    
    try:
        modbus_config.validate()
    except ValueError as e:
        pytest.fail(f"Validation failed: {e}")
    
    assert len(modbus_config.devices) == 2
    device = modbus_config.devices[0]
    assert device.name == "test_1"
    assert device.host == "127.0.0.1"
    assert device.port == 5024
    assert len(device.io_points) == 3

# def test_get_batch_read_requests_from_io_points():
#     print("\n--- Testing get_batch_read_requests_from_io_points ---")
#     io_points = {
#         "io_points": [
#             {
#                 "fc": 1,
#                 "offset": "0x0001",
#                 "iec_location": "%IX0.0",
#                 "len": 8
#             },
#             {
#                 "fc": 5,
#                 "offset": "0x0010",
#                 "iec_location": "%QX0.0",
#                 "len": 1
#             }
#         ]
#     }
#     data = ModbusIoPointConfig.from_dict(data=io_points)
#     requests = get_batch_read_requests_from_io_points(data)
#     for req in requests:
#         print(req)


# def test_get_batch_write_requests_from_io_points():
#     print("\n--- Testing get_batch_write_requests_from_io_points ---")
#     io_points = [
#             {
#                 "fc": 15,
#                 "offset": "0x0020",
#                 "iec_location": "%QX0.0",
#                 "len": 4
#             },
#             {
#                 "fc": 6,
#                 "offset": "0x0030",
#                 "iec_location": "%MW0",
#                 "len": 2
#             }
#         ]
#     requests = get_batch_write_requests_from_io_points(io_points)
#     for req in requests:
#         print(req)

# def test_modbus_slave_device_initialization():
#     print("\n--- Testing ModbusSlaveDevice Initialization ---")
#     for device_config in modbus_master_config.devices:
#         try:
#             device = ModbusSlaveDevice(device_config, safe_buffer_accessor)
#             print(device)
#         except Exception as e:
#             print(f"Error initializing ModbusSlaveDevice: {e}")
        
#         assert device_config.name == "TestModbusSlave"