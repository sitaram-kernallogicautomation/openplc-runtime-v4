# tests/test_modbus_plugin.py
import pytest

@pytest.mark.asyncio
async def test_plugin_can_read(modbus_master_plugin):
    """Test the plugin performs a Modbus read correctly."""
    data = await modbus_master_plugin.read(fc=3, address=0, count=5)
    assert isinstance(data, list)
    assert all(value == 17 for value in data)
