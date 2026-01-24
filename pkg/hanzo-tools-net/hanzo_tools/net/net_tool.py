"""Network tool for HIP-0300 architecture.

This module provides the 'net' tool for network operations:
- search: Query → [URL, title, snippet]
- fetch: URL → {text, mime, status}
- download: URL → Path (with assets)
- crawl: URL + depth → [Path] (recursive mirror)

Effect lattice position: NONDETERMINISTIC_EFFECT
Network operations are inherently non-deterministic.
"""

import os
import json
import asyncio
import re
from typing import Any, ClassVar
from pathlib import Path
from urllib.parse import urlparse, urljoin
import mimetypes

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import (
    BaseTool,
    ToolError,
    InvalidParamsError,
    NotFoundError,
    content_hash,
)


class NetTool(BaseTool):
    """Network operations tool (HIP-0300).

    Handles all network operations:
    - search: Web search query
    - fetch: Single URL retrieval
    - download: Save page with assets
    - crawl: Recursive site mirror

    Effect: NONDETERMINISTIC_EFFECT
    """

    name: ClassVar[str] = "net"
    VERSION: ClassVar[str] = "0.1.0"

    def __init__(self, cwd: str | None = None):
        super().__init__()
        self.cwd = cwd or os.getcwd()
        self._client = None
        self._register_net_actions()

    @property
    def description(self) -> str:
        return """Network operations tool (HIP-0300).

Actions:
- search: Web search (Query → [URL, title, snippet])
- fetch: Retrieve URL content (URL → {text, mime, status})
- download: Save page with assets (URL → Path)
- crawl: Recursive site mirror (URL, depth → [Path])

Effect: NONDETERMINISTIC_EFFECT (network I/O)
"""

    async def _get_client(self):
        """Get or create HTTP client."""
        if self._client is None:
            try:
                import httpx
                self._client = httpx.AsyncClient(
                    follow_redirects=True,
                    timeout=30.0,
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; HanzoBot/1.0)"
                    }
                )
            except ImportError:
                raise ToolError(
                    code="INTERNAL_ERROR",
                    message="httpx not installed. Run: pip install httpx",
                )
        return self._client

    def _extract_text(self, html: str) -> str:
        """Extract text from HTML."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            return soup.get_text(separator="\n", strip=True)
        except ImportError:
            # Fallback: simple regex
            text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text)
            return text.strip()

    def _extract_links(self, html: str, base_url: str) -> list[str]:
        """Extract links from HTML."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")
            links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                full_url = urljoin(base_url, href)
                links.append(full_url)
            return links
        except ImportError:
            # Fallback: regex
            pattern = r'href=["\']([^"\']+)["\']'
            matches = re.findall(pattern, html)
            return [urljoin(base_url, m) for m in matches]

    def _register_net_actions(self):
        """Register all network actions."""

        @self.action("search", "Web search query")
        async def search(
            ctx: MCPContext,
            query: str,
            engine: str = "duckduckgo",
            limit: int = 10,
        ) -> dict:
            """Perform web search.

            Args:
                query: Search query
                engine: Search engine (duckduckgo, google)
                limit: Max results

            Returns:
                {results: [{url, title, snippet}]}

            Effect: NONDETERMINISTIC_EFFECT
            """
            client = await self._get_client()

            if engine == "duckduckgo":
                # DuckDuckGo HTML search (no API key needed)
                url = f"https://html.duckduckgo.com/html/?q={query}"
                response = await client.get(url)

                results = []
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, "lxml")
                    for result in soup.select(".result")[:limit]:
                        title_el = result.select_one(".result__title")
                        snippet_el = result.select_one(".result__snippet")
                        link_el = result.select_one(".result__url")

                        if title_el and link_el:
                            results.append({
                                "title": title_el.get_text(strip=True),
                                "url": link_el.get("href", ""),
                                "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                            })
                except ImportError:
                    # Fallback without beautifulsoup
                    results = [{
                        "note": "Install beautifulsoup4 for better parsing",
                        "raw_length": len(response.text),
                    }]

            else:
                raise InvalidParamsError(
                    f"Unknown engine: {engine}",
                    param="engine",
                    expected="duckduckgo",
                )

            return {
                "results": results,
                "query": query,
                "engine": engine,
                "count": len(results),
            }

        @self.action("fetch", "Retrieve URL content")
        async def fetch(
            ctx: MCPContext,
            url: str,
            extract_text: bool = False,
            headers: dict | None = None,
        ) -> dict:
            """Fetch content from URL.

            Args:
                url: URL to fetch
                extract_text: Extract text from HTML
                headers: Additional headers

            Returns:
                {text, mime, status, headers, hash}

            Effect: NONDETERMINISTIC_EFFECT
            """
            client = await self._get_client()

            try:
                response = await client.get(url, headers=headers)
            except Exception as e:
                raise ToolError(
                    code="INTERNAL_ERROR",
                    message=f"Network error: {e}",
                    details={"url": url},
                )

            content_type = response.headers.get("content-type", "")
            mime = content_type.split(";")[0].strip()

            # Determine if text or binary
            is_text = mime.startswith("text/") or mime in [
                "application/json",
                "application/xml",
                "application/javascript",
            ]

            if is_text:
                text = response.text
                if extract_text and "html" in mime:
                    text = self._extract_text(text)
                return {
                    "text": text,
                    "mime": mime,
                    "status": response.status_code,
                    "hash": content_hash(text),
                    "size": len(response.content),
                    "url": str(response.url),
                }
            else:
                # Binary content
                return {
                    "binary": True,
                    "mime": mime,
                    "status": response.status_code,
                    "hash": content_hash(response.content),
                    "size": len(response.content),
                    "url": str(response.url),
                }

        @self.action("download", "Save URL to file")
        async def download(
            ctx: MCPContext,
            url: str,
            dest: str | None = None,
            assets: bool = False,
        ) -> dict:
            """Download URL to local file.

            Args:
                url: URL to download
                dest: Destination path (auto-generated if not specified)
                assets: Download page assets (images, css, js)

            Returns:
                {path, size, mime}

            Effect: NONDETERMINISTIC_EFFECT
            """
            client = await self._get_client()

            try:
                response = await client.get(url)
            except Exception as e:
                raise ToolError(
                    code="INTERNAL_ERROR",
                    message=f"Download failed: {e}",
                )

            # Generate destination path
            if not dest:
                parsed = urlparse(url)
                filename = Path(parsed.path).name or "index.html"
                dest = str(Path(self.cwd) / filename)

            dest_path = Path(dest)
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Save content
            dest_path.write_bytes(response.content)

            result = {
                "path": str(dest_path),
                "size": len(response.content),
                "mime": response.headers.get("content-type", "").split(";")[0],
                "url": url,
            }

            # Download assets if requested
            if assets and "html" in result["mime"]:
                downloaded_assets = []
                html = response.text
                links = []

                # Extract asset URLs
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, "lxml")

                    for tag in soup.find_all(["img", "link", "script"]):
                        src = tag.get("src") or tag.get("href")
                        if src and not src.startswith("data:"):
                            links.append(urljoin(url, src))
                except ImportError:
                    pass

                # Download assets
                assets_dir = dest_path.parent / f"{dest_path.stem}_assets"
                assets_dir.mkdir(exist_ok=True)

                for asset_url in links[:50]:  # Limit to 50 assets
                    try:
                        asset_resp = await client.get(asset_url)
                        asset_name = Path(urlparse(asset_url).path).name
                        asset_path = assets_dir / asset_name
                        asset_path.write_bytes(asset_resp.content)
                        downloaded_assets.append(str(asset_path))
                    except Exception:
                        pass

                result["assets"] = downloaded_assets
                result["assets_count"] = len(downloaded_assets)

            return result

        @self.action("crawl", "Recursive site mirror")
        async def crawl(
            ctx: MCPContext,
            url: str,
            dest: str,
            depth: int = 2,
            same_host: bool = True,
            limit: int = 100,
        ) -> dict:
            """Crawl and mirror a website.

            Args:
                url: Starting URL
                dest: Destination directory
                depth: Maximum crawl depth
                same_host: Only crawl same hostname
                limit: Maximum pages to download

            Returns:
                {pages: [Path], count}

            Effect: NONDETERMINISTIC_EFFECT
            """
            client = await self._get_client()
            parsed_start = urlparse(url)
            start_host = parsed_start.netloc

            dest_path = Path(dest)
            dest_path.mkdir(parents=True, exist_ok=True)

            visited = set()
            pages = []
            queue = [(url, 0)]  # (url, depth)

            while queue and len(pages) < limit:
                current_url, current_depth = queue.pop(0)

                if current_url in visited:
                    continue

                if current_depth > depth:
                    continue

                parsed = urlparse(current_url)
                if same_host and parsed.netloc != start_host:
                    continue

                visited.add(current_url)

                try:
                    response = await client.get(current_url)
                except Exception:
                    continue

                # Generate filename
                path_parts = parsed.path.strip("/").split("/")
                if not path_parts or not path_parts[-1]:
                    path_parts.append("index.html")
                elif "." not in path_parts[-1]:
                    path_parts[-1] += ".html"

                file_path = dest_path / "/".join(path_parts)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_bytes(response.content)
                pages.append(str(file_path))

                # Extract links for further crawling
                if "html" in response.headers.get("content-type", ""):
                    links = self._extract_links(response.text, current_url)
                    for link in links:
                        if link not in visited:
                            queue.append((link, current_depth + 1))

            return {
                "pages": pages,
                "count": len(pages),
                "dest": str(dest_path),
                "depth": depth,
            }

        @self.action("head", "Get URL headers only")
        async def head(
            ctx: MCPContext,
            url: str,
        ) -> dict:
            """Get HTTP headers without downloading body.

            Args:
                url: URL to check

            Returns:
                {status, headers, size?, mime?}

            Effect: NONDETERMINISTIC_EFFECT
            """
            client = await self._get_client()

            try:
                response = await client.head(url)
            except Exception as e:
                raise ToolError(
                    code="INTERNAL_ERROR",
                    message=f"Request failed: {e}",
                )

            headers = dict(response.headers)
            result = {
                "status": response.status_code,
                "headers": headers,
                "url": str(response.url),
            }

            if "content-length" in headers:
                result["size"] = int(headers["content-length"])
            if "content-type" in headers:
                result["mime"] = headers["content-type"].split(";")[0].strip()

            return result

    def register(self, mcp_server: FastMCP) -> None:
        """Register as 'net' tool with MCP server."""
        tool_name = self.name
        tool_description = self.description

        @mcp_server.tool(name=tool_name, description=tool_description)
        async def handler(
            ctx: MCPContext,
            action: str = "help",
            **kwargs: Any,
        ) -> str:
            result = await self.call(ctx, action=action, **kwargs)
            return json.dumps(result, indent=2, default=str)


# Singleton
net_tool = NetTool
