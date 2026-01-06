# Tools

Tools give agents the ability to take actions and access external data.

## Function Tools

The simplest way to create a tool:

```python
from agents import Agent, function_tool

@function_tool
def get_weather(city: str) -> str:
    """Get current weather for a city.
    
    Args:
        city: The city name to get weather for
    """
    # Your implementation
    return f"Weather in {city}: Sunny, 72°F"

agent = Agent(
    name="weather_bot",
    instructions="Help users with weather information.",
    tools=[get_weather],
)
```

## Async Tools

```python
@function_tool
async def fetch_data(url: str) -> str:
    """Fetch data from a URL."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
```

## Tools with Context

Access the run context in tools:

```python
from dataclasses import dataclass
from agents import function_tool, RunContextWrapper

@dataclass
class AppContext:
    user_id: str
    api_key: str

@function_tool
def get_user_profile(ctx: RunContextWrapper[AppContext]) -> str:
    """Get the current user's profile."""
    user_id = ctx.context.user_id
    # Fetch profile using user_id
    return f"Profile for user {user_id}"
```

## Tool Parameters

Pydantic models for complex parameters:

```python
from pydantic import BaseModel, Field
from agents import function_tool

class SearchParams(BaseModel):
    query: str = Field(description="Search query")
    max_results: int = Field(default=10, description="Max results to return")
    include_metadata: bool = Field(default=False)

@function_tool
def search(params: SearchParams) -> str:
    """Search the knowledge base."""
    # Use params.query, params.max_results, etc.
    return f"Found results for: {params.query}"
```

## Custom Tool Class

For more control, extend the `Tool` class:

```python
from agents import Tool

class DatabaseTool(Tool):
    name = "query_database"
    description = "Query the application database"
    
    def __init__(self, connection_string: str):
        self.conn = connect(connection_string)
    
    async def run(self, query: str) -> str:
        result = await self.conn.execute(query)
        return str(result)
    
    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL query to execute"
                }
            },
            "required": ["query"]
        }
```

## Tool Return Types

### String (default)

```python
@function_tool
def simple() -> str:
    return "Hello"
```

### Structured (Pydantic)

```python
class ToolResult(BaseModel):
    success: bool
    data: dict

@function_tool
def structured() -> ToolResult:
    return ToolResult(success=True, data={"key": "value"})
```

### List/Dict

```python
@function_tool
def get_items() -> list[str]:
    return ["item1", "item2", "item3"]
```

## Error Handling

```python
from agents import function_tool, ToolError

@function_tool
def risky_operation(param: str) -> str:
    """An operation that might fail."""
    try:
        result = do_something(param)
        return result
    except Exception as e:
        raise ToolError(f"Operation failed: {e}")
```

## Tool Metadata

```python
@function_tool(
    name="custom_name",  # Override function name
    description="Custom description",  # Override docstring
)
def my_tool(x: int) -> int:
    return x * 2
```

## Multiple Tools

```python
from agents import Agent

agent = Agent(
    name="multi_tool",
    instructions="Use available tools to help users.",
    tools=[
        get_weather,
        search_web,
        calculate,
        send_email,
    ],
)
```

## See Also

- [Agents](agents.md) - Creating agents
- [Running Agents](running_agents.md) - Execution
- [Context](context.md) - Run context
