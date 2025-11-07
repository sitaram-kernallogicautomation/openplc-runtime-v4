import pytest
from unittest.mock import AsyncMock, patch

# @pytest.mark.asyncio
# async def test_plugin_read_with_mock():
#     # Patch the AsyncModbusTcpClient inside your plugin
#     with patch(
#         "core.src.drivers.plugins.python.modbus_master.modbus_master_plugin.AsyncModbusTcpClient"
#     ) as mock_client_class:

#         # Create a fake instance for AsyncModbusTcpClient
#         mock_client = AsyncMock()
#         mock_client.connect.return_value = True
#         mock_client.close.return_value = True

#         # Define fake Modbus read response
#         mock_response = AsyncMock()
#         mock_response.isError.return_value = False
#         mock_response.registers = [17, 18, 19, 20]
#         mock_client.read_holding_registers.return_value = mock_response

#         # The class returns our fake instance when instantiated
#         mock_client_class.return_value = mock_client

#         # Import your plugin (fresh import so patch applies)
#         import importlib
#         plugin = importlib.import_module(
#             "core.src.drivers.plugins.python.modbus_master.modbus_master_plugin"
#         )

#         # Initialize the plugin
#         config = {"host": "localhost", "port": 5020}
#         await plugin.INIT(config)
#         await plugin.START()

#         # Call the read method (this uses the mocked client)
#         result = await plugin.read(fc=3, address=0, count=4)

#         # Assertions
#         assert result == [17, 18, 19, 20]
#         mock_client.read_holding_registers.assert_awaited_with(0, 4)

#         await plugin.STOP()
