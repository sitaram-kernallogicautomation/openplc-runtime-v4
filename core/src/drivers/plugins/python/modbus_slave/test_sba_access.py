import pytest
from unittest.mock import MagicMock, patch
from simple_modbus import SafeBufferAccess


@pytest.fixture
def runtime_args():
    """Fake runtime args with a mock PLC buffer."""
    class FakeRuntime:
        def __init__(self):
            self.analog_inputs = [100, 200, 300, 400]
    return FakeRuntime()


def test_safe_buffer_init_valid(runtime_args):
    sba = SafeBufferAccess(runtime_args)
    assert sba.is_valid is True
    assert sba.error_msg == ""


def test_safe_buffer_init_invalid():
    sba = SafeBufferAccess(None)
    assert sba.is_valid is False
    assert "None" in sba.error_msg.lower()


def test_safe_buffer_read_ok(runtime_args):
    sba = SafeBufferAccess(runtime_args)
    assert sba.read(0) == 100
    assert sba.read(3) == 400


def test_safe_buffer_read_invalid_range(runtime_args):
    sba = SafeBufferAccess(runtime_args)
    with pytest.raises(IndexError):
        sba.read(10)

    with pytest.raises(IndexError):
        sba.read(-1)


def test_safe_buffer_write_ok(runtime_args):
    sba = SafeBufferAccess(runtime_args)
    sba.write(1, 999)
    assert runtime_args.analog_inputs[1] == 999


def test_safe_buffer_write_invalid_range(runtime_args):
    sba = SafeBufferAccess(runtime_args)
    with pytest.raises(IndexError):
        sba.write(10, 55)


def test_safe_buffer_write_masking(runtime_args):
    """Check that masking is respected (simulate 16-bit modbus word)."""
    sba = SafeBufferAccess(runtime_args)

    sba.write(0, 0xFFFF_FFFF)    # 32-bit attempt
    assert runtime_args.analog_inputs[0] == 0xFFFF & 0xFFFF  # Only 16 bits allowed


def test_safe_buffer_lock_is_respected(runtime_args):
    sba = SafeBufferAccess(runtime_args)

    # Replace lock with a controllable fake lock
    fake_lock = MagicMock()
    fake_lock.__enter__.return_value = True
    fake_lock.__exit__.return_value = False

    sba.lock = fake_lock

    sba.write(1, 123)

    fake_lock.__enter__.assert_called_once()
    fake_lock.__exit__.assert_called_once()
