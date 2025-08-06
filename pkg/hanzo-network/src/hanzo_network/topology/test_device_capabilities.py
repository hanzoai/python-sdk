import pytest
from unittest.mock import patch, Mock
from hanzo_network.topology.device_capabilities import mac_device_capabilities, DeviceCapabilities, DeviceFlops, TFLOPS, device_capabilities


@patch("subprocess.run")
@patch("psutil.virtual_memory")
def test_mac_device_capabilities_pro(mock_memory, mock_subprocess_run):
    # Mock memory
    mock_memory.return_value = Mock(total=137438953472)  # 128 GB
    
    # Mock the subprocess output
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = """
Hardware:

Hardware Overview:

Model Name: MacBook Pro
Model Identifier: Mac15,9
Model Number: Z1CM000EFB/A
Chip: Apple M3 Max
Total Number of Cores: 16 (12 performance and 4 efficiency)
Memory: 128 GB
System Firmware Version: 10000.000.0
OS Loader Version: 10000.000.0
Serial Number (system): XXXXXXXXXX
Hardware UUID: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
Provisioning UDID: XXXXXXXX-XXXXXXXXXXXXXXXX
Activation Lock Status: Enabled
"""
    mock_subprocess_run.return_value = mock_result

    # Call the function
    result = mac_device_capabilities()

    # Check the results
    assert isinstance(result, DeviceCapabilities)
    assert result.model == "MacBook Pro"
    assert result.chip == "Apple M3 Max"
    assert result.memory == 131072  # 128 GB in MB
    assert "fp32: 14.20 TFLOPS" in str(result)


@patch("subprocess.run")
@patch("psutil.virtual_memory")
def test_mac_device_capabilities_air(mock_memory, mock_subprocess_run):
    # Mock memory
    mock_memory.return_value = Mock(total=8589934592)  # 8 GB
    
    # Mock the subprocess output
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = """
Hardware:

Hardware Overview:

Model Name: MacBook Air
Model Identifier: Mac14,2
Model Number: MLY33B/A
Chip: Apple M2
Total Number of Cores: 8 (4 performance and 4 efficiency)
Memory: 8 GB
System Firmware Version: 10000.00.0
OS Loader Version: 10000.00.0
Serial Number (system): XXXXXXXXXX
Hardware UUID: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
Provisioning UDID: XXXXXXXX-XXXXXXXXXXXXXXXX
Activation Lock Status: Disabled
"""
    mock_subprocess_run.return_value = mock_result

    # Call the function
    result = mac_device_capabilities()

    # Check the results
    assert isinstance(result, DeviceCapabilities)
    assert result.model == "MacBook Air"
    assert result.chip == "Apple M2"
    assert result.memory == 8192  # 8 GB in MB


@pytest.mark.skip(reason="Unskip this test when running on a MacBook Pro, Apple M3 Max, 128GB")
def test_mac_device_capabilities_real():
    # Call the function without mocking
    result = mac_device_capabilities()

    # Check the results
    assert isinstance(result, DeviceCapabilities)
    assert result.model == "MacBook Pro"
    assert result.chip == "Apple M3 Max"
    assert result.memory == 131072  # 128 GB in MB
    assert result.flops == DeviceFlops(fp32=14.20*TFLOPS, fp16=28.40*TFLOPS, int8=56.80*TFLOPS)
    assert str(result) == "Model: MacBook Pro. Chip: Apple M3 Max. Memory: 131072MB. Flops: fp32: 14.20 TFLOPS, fp16: 28.40 TFLOPS, int8: 56.80 TFLOPS"


def test_device_capabilities():
    caps = device_capabilities()
    assert caps.model != ""
    assert caps.chip != ""
    assert caps.memory > 0
    assert caps.flops is not None