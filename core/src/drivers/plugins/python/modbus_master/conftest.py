# tests/conftest.py
import importlib
import pytest
# import asyncio
# from pymodbus.server import StartAsyncTcpServer
# from pymodbus.datastore import (
#     ModbusSequentialDataBlock,
#     ModbusSlaveContext,
#     ModbusServerContext,
# )
# from pymodbus.device import ModbusDeviceIdentification

# from unittest.mock import AsyncMock, patch

# @pytest.fixture
# def mocked_modbus_client():
#     with patch(
#         "core.src.drivers.plugins.python.modbus_master.modbus_master_plugin.AsyncModbusTcpClient"
#     ) as mock_class:
#         mock_client = AsyncMock()
#         mock_client.connect.return_value = True
#         mock_client.close.return_value = True

#         mock_response = AsyncMock()
#         mock_response.isError.return_value = False
#         mock_response.registers = [17] * 10
#         mock_client.read_holding_registers.return_value = mock_response

#         mock_class.return_value = mock_client
#         yield mock_client


# @pytest.fixture(scope="function")
# async def modbus_master_plugin(modbus_server):
#     """Fixture that initializes and cleans up the Modbus master plugin."""
#     # Import plugin module dynamically
#     plugin = importlib.import_module(
#         "core.src.drivers.plugins.python.modbus_master.modbus_master_plugin"
#     )

#     config = {"host": "localhost", "port": 5020}

#     # Call INIT and START
#     await plugin.INIT(config)
#     await plugin.START()

#     yield plugin  # <-- yield plugin to the test

#     # Cleanup
#     await plugin.STOP()

# @pytest.fixture(scope="module")
# def modbus_server():
#     """Start a Modbus TCP server in the background for tests."""

#     store = ModbusSlaveContext(
#         di=ModbusSequentialDataBlock(0, [17]*100),
#         co=ModbusSequentialDataBlock(0, [17]*100),
#         hr=ModbusSequentialDataBlock(0, [17]*100),
#         ir=ModbusSequentialDataBlock(0, [17]*100),
#     )
#     context = ModbusServerContext(slaves=store, single=True)

#     identity = ModbusDeviceIdentification()
#     identity.VendorName = "pytest-server"
#     identity.ProductCode = "PM"
#     identity.VendorUrl = "http://example.com"
#     identity.ProductName = "Pytest Modbus Server"
#     identity.ModelName = "Test Server"
#     identity.MajorMinorRevision = "1.0"

#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)

#     async def start_server():
#         await StartAsyncTcpServer(
#             context=context,
#             identity=identity,
#             address=("localhost", 5020),
#         )

#     # Run in background thread
#     import threading

#     thread = threading.Thread(target=loop.run_until_complete, args=(start_server(),))
#     thread.daemon = True
#     thread.start()

#     yield  # <-- yield control to test

#     # teardown
#     loop.call_soon_threadsafe(loop.stop)
#     thread.join(timeout=2)
