# tests/test_discrete_inputs.py
import simple_modbus


def test_inputs_basic(advanced_sba):
    block = simple_modbus.OpenPLCDiscreteInputsDataBlock(runtime_args=advanced_sba, num_inputs=8)

    # simulate PLC changing input bits
    advanced_sba.bits[4] = 1

    values = block.getValues(5, 1)  # modbus address mapped index 4
    assert values == [1]


def test_inputs_invalid_range_non_blocking(advanced_sba):
    block = simple_modbus.OpenPLCDiscreteInputsDataBlock(runtime_args=advanced_sba, num_inputs=4)

    advanced_sba.fail_range = True
    res = block.getValues(1, 3)

    assert res == []   # non-blocking safe fallback
