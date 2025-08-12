"""Device capabilities for distributed Hanzo networks."""

from typing import Any
from pydantic import BaseModel
import platform
import psutil

DEBUG = 0  # Default debug level
TFLOPS = 1.00


class DeviceFlops(BaseModel):
    """Device floating-point operations per second."""

    # units of TFLOPS
    fp32: float
    fp16: float
    int8: float

    def __str__(self):
        return f"fp32: {self.fp32 / TFLOPS:.2f} TFLOPS, fp16: {self.fp16 / TFLOPS:.2f} TFLOPS, int8: {self.int8 / TFLOPS:.2f} TFLOPS"

    def to_dict(self):
        return self.model_dump()


class DeviceCapabilities(BaseModel):
    """Device capabilities information."""

    model: str
    chip: str
    memory: int  # MB
    flops: DeviceFlops

    def __str__(self):
        return f"Model: {self.model}. Chip: {self.chip}. Memory: {self.memory}MB. Flops: {self.flops}"

    def model_post_init(self, __context: Any) -> None:
        if isinstance(self.flops, dict):
            self.flops = DeviceFlops(**self.flops)

    def to_dict(self):
        return {
            "model": self.model,
            "chip": self.chip,
            "memory": self.memory,
            "flops": self.flops.to_dict(),
        }


UNKNOWN_DEVICE_CAPABILITIES = DeviceCapabilities(
    model="Unknown Model",
    chip="Unknown Chip",
    memory=0,
    flops=DeviceFlops(fp32=0, fp16=0, int8=0),
)

# Common chip performance data
CHIP_FLOPS = {
    # Apple M series
    "Apple M1": DeviceFlops(fp32=2.29 * TFLOPS, fp16=4.58 * TFLOPS, int8=9.16 * TFLOPS),
    "Apple M1 Pro": DeviceFlops(
        fp32=5.30 * TFLOPS, fp16=10.60 * TFLOPS, int8=21.20 * TFLOPS
    ),
    "Apple M1 Max": DeviceFlops(
        fp32=10.60 * TFLOPS, fp16=21.20 * TFLOPS, int8=42.40 * TFLOPS
    ),
    "Apple M2": DeviceFlops(
        fp32=3.55 * TFLOPS, fp16=7.10 * TFLOPS, int8=14.20 * TFLOPS
    ),
    "Apple M2 Pro": DeviceFlops(
        fp32=5.68 * TFLOPS, fp16=11.36 * TFLOPS, int8=22.72 * TFLOPS
    ),
    "Apple M2 Max": DeviceFlops(
        fp32=13.49 * TFLOPS, fp16=26.98 * TFLOPS, int8=53.96 * TFLOPS
    ),
    "Apple M3": DeviceFlops(
        fp32=3.55 * TFLOPS, fp16=7.10 * TFLOPS, int8=14.20 * TFLOPS
    ),
    "Apple M3 Pro": DeviceFlops(
        fp32=4.97 * TFLOPS, fp16=9.94 * TFLOPS, int8=19.88 * TFLOPS
    ),
    "Apple M3 Max": DeviceFlops(
        fp32=14.20 * TFLOPS, fp16=28.40 * TFLOPS, int8=56.80 * TFLOPS
    ),
    "Apple M4": DeviceFlops(
        fp32=4.26 * TFLOPS, fp16=8.52 * TFLOPS, int8=17.04 * TFLOPS
    ),
    # NVIDIA GPUs
    "NVIDIA GEFORCE RTX 4090": DeviceFlops(
        fp32=82.58 * TFLOPS, fp16=165.16 * TFLOPS, int8=330.32 * TFLOPS
    ),
    "NVIDIA GEFORCE RTX 4080": DeviceFlops(
        fp32=48.74 * TFLOPS, fp16=97.48 * TFLOPS, int8=194.96 * TFLOPS
    ),
    "NVIDIA GEFORCE RTX 4070": DeviceFlops(
        fp32=29.0 * TFLOPS, fp16=58.0 * TFLOPS, int8=116.0 * TFLOPS
    ),
    "NVIDIA GEFORCE RTX 3090": DeviceFlops(
        fp32=35.6 * TFLOPS, fp16=71.2 * TFLOPS, int8=142.4 * TFLOPS
    ),
    "NVIDIA GEFORCE RTX 3080": DeviceFlops(
        fp32=29.8 * TFLOPS, fp16=59.6 * TFLOPS, int8=119.2 * TFLOPS
    ),
    # Add more as needed
}


def device_capabilities() -> DeviceCapabilities:
    """Get current device capabilities."""
    system = platform.system()

    if system == "Darwin":  # macOS
        return mac_device_capabilities()
    elif system == "Linux":
        return linux_device_capabilities()
    elif system == "Windows":
        return windows_device_capabilities()
    else:
        return DeviceCapabilities(
            model="Unknown Device",
            chip="Unknown Chip",
            memory=psutil.virtual_memory().total // 2**20,
            flops=DeviceFlops(fp32=0, fp16=0, int8=0),
        )


def mac_device_capabilities() -> DeviceCapabilities:
    """Get macOS device capabilities."""
    try:
        import subprocess

        # Get model info
        model_result = subprocess.run(
            ["system_profiler", "SPHardwareDataType"], capture_output=True, text=True
        )

        model = "Mac"
        chip = "Unknown"

        if model_result.returncode == 0:
            output = model_result.stdout
            # Parse model name
            for line in output.split("\n"):
                if "Model Name:" in line:
                    model = line.split("Model Name:")[-1].strip()
                elif "Chip:" in line:
                    chip = line.split("Chip:")[-1].strip()
                elif "System Chip:" in line:
                    chip = line.split("System Chip:")[-1].strip()

        # Get memory
        memory = psutil.virtual_memory().total // 2**20

        # Get FLOPS for the chip
        flops = CHIP_FLOPS.get(chip, DeviceFlops(fp32=0, fp16=0, int8=0))

        return DeviceCapabilities(model=model, chip=chip, memory=memory, flops=flops)

    except Exception as e:
        if DEBUG >= 1:
            print(f"Error getting Mac device capabilities: {e}")
        return DeviceCapabilities(
            model="Mac",
            chip="Unknown",
            memory=psutil.virtual_memory().total // 2**20,
            flops=DeviceFlops(fp32=0, fp16=0, int8=0),
        )


def linux_device_capabilities() -> DeviceCapabilities:
    """Get Linux device capabilities."""
    # Basic implementation - can be extended with GPU detection
    return DeviceCapabilities(
        model="Linux Box",
        chip="CPU",
        memory=psutil.virtual_memory().total // 2**20,
        flops=DeviceFlops(fp32=0, fp16=0, int8=0),
    )


def windows_device_capabilities() -> DeviceCapabilities:
    """Get Windows device capabilities."""
    # Basic implementation - can be extended with GPU detection
    return DeviceCapabilities(
        model="Windows Box",
        chip="CPU",
        memory=psutil.virtual_memory().total // 2**20,
        flops=DeviceFlops(fp32=0, fp16=0, int8=0),
    )
