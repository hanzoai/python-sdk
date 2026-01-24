# Net Tool

Network operations: search, fetch, download, crawl (HIP-0300 operator).

## Installation

```bash
pip install hanzo-tools-net

# With full HTML parsing support
pip install hanzo-tools-net[full]
```

## Overview

The `net` tool handles all network operations:

| Action | Signature | Effect |
|--------|-----------|--------|
| `search` | `(Query, engine?) → [{url, title, snippet}]` | NONDETERMINISTIC |
| `fetch` | `(URL, extract_text?) → {text, mime, status, hash}` | NONDETERMINISTIC |
| `download` | `(URL, dest?, assets?) → {path, size, mime}` | NONDETERMINISTIC |
| `crawl` | `(URL, dest, depth?, limit?) → {pages, count}` | NONDETERMINISTIC |
| `head` | `URL → {status, headers, size?, mime?}` | NONDETERMINISTIC |

## Actions

### search

Perform web search queries.

```python
net(action="search", query="python async best practices")
# Returns: {
#   results: [
#     {url: "https://...", title: "Async Python Guide", snippet: "..."},
#     {url: "https://...", title: "Python Concurrency", snippet: "..."}
#   ],
#   query: "python async best practices",
#   engine: "duckduckgo",
#   count: 10
# }

net(action="search", query="rust memory safety", limit=5)
# Limit results
```

**Parameters:**
- `query` (str): Search query
- `engine` (str, optional): Search engine ("duckduckgo" default)
- `limit` (int, optional): Maximum results (default: 10)

### fetch

Retrieve content from a URL.

```python
net(action="fetch", url="https://example.com/api/data")
# Returns: {
#   text: "{\"data\": [...]}",
#   mime: "application/json",
#   status: 200,
#   hash: "sha256:abc123...",
#   size: 1234,
#   url: "https://example.com/api/data"
# }

net(action="fetch", url="https://example.com", extract_text=True)
# Returns: {
#   text: "Example Domain. This domain is for use in...",  # Cleaned text
#   mime: "text/html",
#   status: 200,
#   ...
# }
```

**Parameters:**
- `url` (str): URL to fetch
- `extract_text` (bool, optional): Extract text from HTML (default: False)
- `headers` (dict, optional): Additional HTTP headers

### download

Save URL content to local file.

```python
net(action="download", url="https://example.com/report.pdf")
# Returns: {
#   path: "/current/dir/report.pdf",
#   size: 245678,
#   mime: "application/pdf",
#   url: "https://example.com/report.pdf"
# }

net(action="download", url="https://example.com", dest="./mirror/index.html", assets=True)
# Returns: {
#   path: "./mirror/index.html",
#   size: 5678,
#   mime: "text/html",
#   assets: ["./mirror/index_assets/style.css", "./mirror/index_assets/logo.png"],
#   assets_count: 12
# }
```

**Parameters:**
- `url` (str): URL to download
- `dest` (str, optional): Destination path (auto-generated if not specified)
- `assets` (bool, optional): Download page assets (images, CSS, JS)

### crawl

Recursively mirror a website.

```python
net(action="crawl", url="https://docs.example.com", dest="./mirror", depth=2)
# Returns: {
#   pages: [
#     "./mirror/index.html",
#     "./mirror/getting-started.html",
#     "./mirror/api/index.html",
#     "./mirror/api/reference.html"
#   ],
#   count: 47,
#   dest: "./mirror",
#   depth: 2
# }
```

**Parameters:**
- `url` (str): Starting URL
- `dest` (str): Destination directory
- `depth` (int, optional): Maximum crawl depth (default: 2)
- `same_host` (bool, optional): Only crawl same hostname (default: True)
- `limit` (int, optional): Maximum pages to download (default: 100)

### head

Get HTTP headers without downloading body.

```python
net(action="head", url="https://example.com/large-file.zip")
# Returns: {
#   status: 200,
#   headers: {
#     "content-type": "application/zip",
#     "content-length": "1234567890",
#     "last-modified": "..."
#   },
#   size: 1234567890,
#   mime: "application/zip",
#   url: "https://example.com/large-file.zip"
# }
```

## Usage Examples

### Research Workflow

```python
# 1. Search for information
results = net(action="search", query="rust async runtime comparison 2024")

# 2. Fetch promising articles
for result in results["data"]["results"][:3]:
    content = net(action="fetch", url=result["url"], extract_text=True)
    print(f"--- {result['title']} ---")
    print(content["data"]["text"][:500])
```

### Documentation Mirror

```python
# Mirror documentation for offline access
result = net(action="crawl",
             url="https://docs.example.com",
             dest="./docs-mirror",
             depth=3,
             limit=200)

print(f"Downloaded {result['data']['count']} pages")
```

### API Integration

```python
# Fetch JSON API
response = net(action="fetch",
               url="https://api.example.com/v1/users",
               headers={"Authorization": "Bearer token..."})

import json
data = json.loads(response["data"]["text"])
```

### Pre-flight Check

```python
# Check if file exists and get size before downloading
info = net(action="head", url="https://example.com/large-dataset.tar.gz")

if info["data"]["status"] == 200:
    size_mb = info["data"]["size"] / (1024 * 1024)
    print(f"File size: {size_mb:.1f} MB")

    if size_mb < 100:  # Only download if < 100MB
        net(action="download", url=info["data"]["url"])
```

## Error Handling

Network operations can fail. Handle errors appropriately:

```python
result = net(action="fetch", url="https://example.com/404")

if not result["ok"]:
    print(f"Error: {result['error']['message']}")
    # Error: HTTP 404: Not Found
```

## Dependencies

- `httpx` - HTTP client (required)
- `beautifulsoup4` + `lxml` - HTML parsing (optional, for better text extraction)

Install full dependencies:
```bash
pip install hanzo-tools-net[full]
```

## Rate Limiting

The net tool respects standard rate limiting:
- Honors `Retry-After` headers
- Default timeout: 30 seconds
- Configurable via environment variables

## See Also

- [HIP-0300](../hip/HIP-0300.md) - Unified Tools Architecture
- [Browser Tool](browser.md) - For JavaScript-rendered content
- [Filesystem Tool](fs.md) - For local file operations
