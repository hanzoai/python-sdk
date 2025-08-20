#!/usr/bin/env python3
"""Test rate limiting and error recovery."""

import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "pkg" / "hanzo" / "src"))

from hanzo.rate_limiter import RateLimiter, RateLimitConfig, ErrorRecovery, smart_limiter

async def test_rate_limiter():
    """Test rate limiter functionality."""
    console = Console()
    
    console.print("\n[bold cyan]Testing Rate Limiter[/bold cyan]\n")
    
    # Create a strict rate limiter for testing
    config = RateLimitConfig(
        requests_per_minute=5,
        requests_per_hour=100,
        burst_size=2
    )
    limiter = RateLimiter(config)
    
    # Test rapid requests
    console.print("[bold]Testing rate limiting (5 requests/minute):[/bold]")
    
    for i in range(8):
        allowed, wait = await limiter.check_rate_limit()
        
        if allowed:
            await limiter.acquire()
            console.print(f"✅ Request {i+1} allowed")
        else:
            console.print(f"⏳ Request {i+1} blocked, wait {wait:.1f}s")
        
        # Small delay between requests
        await asyncio.sleep(0.1)
    
    # Test status
    console.print("\n[bold]Rate limiter status:[/bold]")
    status = limiter.get_status()
    
    table = Table(title="Rate Limiter Status")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    for key, value in status.items():
        table.add_row(key.replace("_", " ").title(), str(value))
    
    console.print(table)
    
    # Test error recovery
    console.print("\n[bold]Testing error recovery:[/bold]")
    
    recovery = ErrorRecovery(limiter)
    
    # Simulate a function that fails initially
    attempt_count = 0
    
    async def flaky_function():
        nonlocal attempt_count
        attempt_count += 1
        
        if attempt_count < 3:
            console.print(f"  Attempt {attempt_count} failed")
            raise Exception("Simulated error")
        
        console.print(f"  Attempt {attempt_count} succeeded!")
        return "Success"
    
    try:
        result = await recovery.with_retry(flaky_function, max_retries=5)
        console.print(f"[green]Result: {result}[/green]")
    except Exception as e:
        console.print(f"[red]Failed after retries: {e}[/red]")
    
    # Test smart limiter
    console.print("\n[bold]Testing smart rate limiter:[/bold]")
    
    # Simulate API calls
    async def mock_api_call(api_type: str):
        console.print(f"  Calling {api_type} API...")
        await asyncio.sleep(0.1)
        return f"Response from {api_type}"
    
    # Test different API types
    for api_type in ["openai", "anthropic", "local", "free"]:
        try:
            result = await smart_limiter.execute_with_limit(
                api_type,
                mock_api_call,
                api_type
            )
            console.print(f"  ✅ {api_type}: {result}")
        except Exception as e:
            console.print(f"  ❌ {api_type}: {e}")
    
    # Show all limiter statuses
    console.print("\n[bold]All API limiter statuses:[/bold]")
    all_status = smart_limiter.get_all_status()
    
    for api_type, status in all_status.items():
        if status["total_requests"] > 0:
            console.print(f"\n{api_type}:")
            console.print(f"  Requests: {status['total_requests']}")
            console.print(f"  Errors: {status['total_errors']}")
            console.print(f"  Last minute: {status['requests_last_minute']}")
    
    console.print("\n[green]✅ Rate limiting tests completed![/green]")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_rate_limiter())
    sys.exit(0 if success else 1)