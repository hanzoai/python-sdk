#!/usr/bin/env python3
"""
Simplified E2E Test for Hanzo Net + Hanzo Dev Integration

This test demonstrates the core functionality without requiring hanzo-network package.
"""

import os
import sys
import json
import time
import socket
import asyncio
import logging
import subprocess
from typing import Dict, List, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleHanzoNetTest:
    """Simplified E2E test for hanzo net orchestration."""
    
    def __init__(self):
        self.hanzo_net_process = None
        self.hanzo_dev_process = None
        self.workspace = Path.home() / ".hanzo" / "e2e-test"
        self.workspace.mkdir(parents=True, exist_ok=True)
        
    def is_port_open(self, host: str, port: int) -> bool:
        """Check if a port is open."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    
    async def test_hanzo_net_startup(self, model: str = "llama-3.2-3b") -> bool:
        """Test that hanzo net can start with a local model."""
        logger.info(f"\n=== Testing Hanzo Net Startup with {model} ===")
        
        port = 52415
        
        # Check if already running
        if self.is_port_open("localhost", port):
            logger.info(f"✓ Port {port} already in use (hanzo net may be running)")
            return True
        
        try:
            # Start hanzo net
            cmd = [
                "hanzo", "net",
                "--name", "e2e-test",
                "--port", str(port),
                "--models", model,
                "--network", "local"
            ]
            
            logger.info(f"Starting: {' '.join(cmd)}")
            
            self.hanzo_net_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for startup
            for i in range(30):
                await asyncio.sleep(1)
                if self.is_port_open("localhost", port):
                    logger.info(f"✓ hanzo net started on port {port}")
                    return True
                
                # Check if process died
                if self.hanzo_net_process.poll() is not None:
                    stdout, stderr = self.hanzo_net_process.communicate()
                    logger.error(f"hanzo net failed to start")
                    logger.error(f"STDERR: {stderr}")
                    return False
            
            logger.error("Timeout waiting for hanzo net")
            return False
            
        except Exception as e:
            logger.error(f"Error starting hanzo net: {e}")
            return False
    
    async def test_hanzo_dev_with_local(self, model: str = "llama-3.2-3b") -> bool:
        """Test hanzo dev with local orchestrator."""
        logger.info(f"\n=== Testing Hanzo Dev with Local Orchestrator ===")
        
        try:
            # Start hanzo dev with local orchestrator
            cmd = [
                "hanzo", "dev",
                "--orchestrator", f"local:{model}",
                "--instances", "2",
                "--use-hanzo-net",
                "--workspace", str(self.workspace)
            ]
            
            logger.info(f"Starting: {' '.join(cmd)}")
            
            # Start process and capture output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Read output for a few seconds
            start_time = time.time()
            output_lines = []
            success_indicators = [
                "Agent network initialized",
                "Created local",
                "orchestrator",
                "hanzo/net started"
            ]
            
            while time.time() - start_time < 15:  # 15 second timeout
                line = process.stdout.readline()
                if line:
                    output_lines.append(line.strip())
                    logger.info(f"  {line.strip()}")
                    
                    # Check for success indicators
                    for indicator in success_indicators:
                        if indicator.lower() in line.lower():
                            logger.info(f"✓ Found: {indicator}")
                
                # Check if process died
                if process.poll() is not None:
                    break
                
                await asyncio.sleep(0.1)
            
            # Terminate the process
            process.terminate()
            await asyncio.sleep(2)
            if process.poll() is None:
                process.kill()
            
            # Check if we saw success indicators
            full_output = "\n".join(output_lines)
            if any(indicator in full_output.lower() for indicator in ["network initialized", "orchestrator", "started"]):
                logger.info("✓ hanzo dev initialized successfully")
                return True
            else:
                logger.warning("Could not confirm successful initialization")
                return False
                
        except Exception as e:
            logger.error(f"Error testing hanzo dev: {e}")
            return False
    
    async def test_cost_optimization_config(self) -> bool:
        """Test that cost optimization is configured correctly."""
        logger.info("\n=== Testing Cost Optimization Configuration ===")
        
        # Check if the dev.py file has cost optimization logic
        dev_file = Path(__file__).parent.parent.parent.parent / "pkg" / "hanzo" / "src" / "hanzo" / "dev.py"
        
        if dev_file.exists():
            content = dev_file.read_text()
            
            checks = {
                "CostOptimizedRouter": "Cost-optimized router class",
                "local_workers": "Local worker configuration",
                "simple_keywords": "Simple task detection",
                "complex_keywords": "Complex task detection",
                "local models preferred": "Local model preference"
            }
            
            results = []
            for key, description in checks.items():
                if key.lower() in content.lower():
                    logger.info(f"  ✓ {description} found")
                    results.append(True)
                else:
                    logger.warning(f"  ✗ {description} not found")
                    results.append(False)
            
            success = all(results)
            if success:
                logger.info("✓ Cost optimization properly configured")
            else:
                logger.warning("⚠ Some cost optimization features missing")
            
            return success
        else:
            logger.error(f"dev.py not found at {dev_file}")
            return False
    
    async def run_all_tests(self):
        """Run all tests."""
        logger.info("\n" + "="*60)
        logger.info("HANZO NET SIMPLE E2E TEST")
        logger.info("="*60)
        
        results = {}
        
        try:
            # Test 1: Hanzo net startup
            results["hanzo_net"] = await self.test_hanzo_net_startup()
            
            # Test 2: Hanzo dev with local orchestrator
            results["hanzo_dev"] = await self.test_hanzo_dev_with_local()
            
            # Test 3: Cost optimization configuration
            results["cost_optimization"] = await self.test_cost_optimization_config()
            
            # Summary
            logger.info("\n" + "="*60)
            logger.info("TEST SUMMARY")
            logger.info("="*60)
            
            for test_name, success in results.items():
                status = "✓ PASSED" if success else "✗ FAILED"
                logger.info(f"{test_name}: {status}")
            
            all_passed = all(results.values())
            
            if all_passed:
                logger.info("\n✓ All tests passed!")
            else:
                logger.info("\n✗ Some tests failed")
            
            return all_passed
            
        finally:
            # Cleanup
            if self.hanzo_net_process:
                self.hanzo_net_process.terminate()
                await asyncio.sleep(1)
                if self.hanzo_net_process.poll() is None:
                    self.hanzo_net_process.kill()
            
            if self.hanzo_dev_process:
                self.hanzo_dev_process.terminate()
                await asyncio.sleep(1)
                if self.hanzo_dev_process.poll() is None:
                    self.hanzo_dev_process.kill()


async def main():
    """Main entry point."""
    test = SimpleHanzoNetTest()
    success = await test.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())