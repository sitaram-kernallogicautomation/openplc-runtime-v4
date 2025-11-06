# tests/conftest.py
import pytest
import asyncio
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext,
)
from pymodbus.device import ModbusDeviceIdentification


@pytest.fixture(scope="module")
def modbus_server():
    """Start a Modbus TCP server in the background for tests."""

    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [17]*100),
        co=ModbusSequentialDataBlock(0, [17]*100),
        hr=ModbusSequentialDataBlock(0, [17]*100),
        ir=ModbusSequentialDataBlock(0, [17]*100),
    )
    context = ModbusServerContext(slaves=store, single=True)

    identity = ModbusDeviceIdentification()
    identity.VendorName = "pytest-server"
    identity.ProductCode = "PM"
    identity.VendorUrl = "http://example.com"
    identity.ProductName = "Pytest Modbus Server"
    identity.ModelName = "Test Server"
    identity.MajorMinorRevision = "1.0"

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def start_server():
        await StartAsyncTcpServer(
            context=context,
            identity=identity,
            address=("localhost", 5020),
        )

    # Run in background thread
    import threading

    thread = threading.Thread(target=loop.run_until_complete, args=(start_server(),))
    thread.daemon = True
    thread.start()

    yield  # <-- yield control to test

    # teardown
    loop.call_soon_threadsafe(loop.stop)
    thread.join(timeout=2)
