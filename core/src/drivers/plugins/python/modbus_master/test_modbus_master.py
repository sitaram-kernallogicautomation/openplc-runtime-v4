# tests/test_modbus_master.py
import pytest
from pymodbus.client import AsyncModbusTcpClient
import asyncio

@pytest.mark.asyncio
async def test_modbus_master_reads(modbus_server):
    """Test that the Modbus master can read from the test server."""
    client = AsyncModbusTcpClient("localhost", port=5020)
    await client.connect()

    rr = await client.read_holding_registers(0, 10)
    assert not rr.isError()
    assert rr.registers == [17] * 10

    await client.close()

@pytest.mark.asyncio
async def test_modbus_plugin_reads(modbus_server, modbus_master_plugin):
    """Test the plugin's Modbus read behavior."""
    await modbus_master_plugin.start()

    data = await modbus_master_plugin.read(fc=3, address=0, count=10)
    assert all(value == 17 for value in data)

    await modbus_master_plugin.stop()
