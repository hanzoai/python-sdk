"""Network tool for HIP-0300 architecture.

This module provides the 'fetch' tool for network operations:
- search: Query → [URL, title, snippet]
- research: Query → {answer with citations, sources, follow_ups}
- fetch: URL → {text, mime, status}
- download: URL → Path (with assets)
- crawl: URL + depth → [Path] (recursive mirror)

Effect lattice position: NONDETERMINISTIC_EFFECT
Network operations are inherently non-deterministic.
"""

import asyncio
import os
import re
from pathlib import Path
from typing import Any, ClassVar
from urllib.parse import urljoin, urlparse

from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import (
    BaseTool,
    CloudError,
    HanzoCloud,
    InvalidParamsError,
    ToolError,
    content_hash,
)

# A research pass legitimately runs for minutes — it plans, searches, reads a few
# dozen pages and writes — so its stream gets its own budget instead of the
# client's request-shaped default.
RESEARCH_TIMEOUT = 300.0


def _extract_markdown(resp: Any) -> str:
    """Best-effort markdown out of a Hanzo Crawl / Firecrawl response.

    The crawl `data` is shape-polymorphic across versions — a bare string, a
    {markdown|fit_markdown|raw_markdown|content} object, or a list of those — so
    this accepts any of them and returns the first non-empty markdown found.
    """

    def from_obj(obj: Any) -> str:
        if isinstance(obj, str):
            return obj.strip()
        if isinstance(obj, dict):
            for k in ("markdown", "fit_markdown", "raw_markdown", "content", "text"):
                v = obj.get(k)
                if isinstance(v, str) and v.strip():
                    return v.strip()
                if isinstance(v, dict):
                    inner = from_obj(v)
                    if inner:
                        return inner
        return ""

    if not isinstance(resp, dict):
        return from_obj(resp)
    payload = resp.get("data", resp)  # {status,msg,data} or {success,data:{...}}
    if isinstance(payload, list):
        for item in payload:
            md = from_obj(item)
            if md:
                return md
        return ""
    return from_obj(payload)


def _research_mode(mode: str) -> str:
    """The one pass this action opens.

    ``deep`` is the older name for the same research pass, so it normalizes.
    Anything else names a different pass — plain web search is its own action — and
    is refused rather than silently downgraded.
    """
    m = (mode or "research").strip().lower()
    if m in ("research", "deep"):
        return "research"
    raise InvalidParamsError(
        f"unknown research mode: {mode}", param="mode", expected="research"
    )


def _source(s: Any) -> dict:
    """A citation's card: where it is, what it is, and its mark."""
    if not isinstance(s, dict):
        return {"url": str(s), "title": "", "favicon": ""}
    return {
        "url": s.get("url", ""),
        "title": s.get("title", ""),
        "favicon": s.get("favicon", ""),
    }


def _crawl_metadata(resp: Any) -> dict:
    """Pull a metadata dict out of a crawl response, if present."""
    if isinstance(resp, dict):
        payload = resp.get("data", resp)
        if isinstance(payload, dict) and isinstance(payload.get("metadata"), dict):
            return payload["metadata"]
    return {}


class FetchTool(BaseTool):
    """Network operations tool (HIP-0300).

    Handles all network operations:
    - search: Web search query
    - fetch: Single URL retrieval
    - download: Save page with assets
    - crawl: Recursive site mirror

    Effect: NONDETERMINISTIC_EFFECT
    """

    name: ClassVar[str] = "fetch"
    VERSION: ClassVar[str] = "0.1.0"

    def __init__(self, cwd: str | None = None):
        super().__init__()
        self.cwd = cwd or os.getcwd()
        self._client = None
        self._cloud: HanzoCloud | None = None
        self._register_net_actions()

    def _get_cloud(self) -> HanzoCloud | None:
        """Shared Hanzo Cloud client, or None when no API key is configured."""
        if self._cloud is None:
            self._cloud = HanzoCloud()
        return self._cloud if self._cloud.configured() else None

    @property
    def description(self) -> str:
        return """Network operations tool (HIP-0300).

Actions:
- search: Web search — cloud Bing meta-search (api.hanzo.ai) with a local
  DuckDuckGo fallback (Query → [URL, title, snippet])
- web_read: Fetch a URL → clean markdown (cloud Crawl4AI, local fallback)
- research: Search + read + synthesize behind one endpoint — the cloud answer
  engine (Query → {answer with citations, sources, follow_ups})
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
                    headers={"User-Agent": "Mozilla/5.0 (compatible; HanzoBot/1.0)"},
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
            text = re.sub(
                r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE
            )
            text = re.sub(
                r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE
            )
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

    async def _duckduckgo_search(self, query: str, limit: int) -> list[dict]:
        """Local DuckDuckGo HTML search (no API key). Used as a fallback."""
        client = await self._get_client()
        response = await client.get(f"https://html.duckduckgo.com/html/?q={query}")

        results: list[dict] = []
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(response.text, "lxml")
            for result in soup.select(".result")[:limit]:
                title_el = result.select_one(".result__title")
                snippet_el = result.select_one(".result__snippet")
                link_el = result.select_one(".result__url")
                if title_el and link_el:
                    results.append(
                        {
                            "title": title_el.get_text(strip=True),
                            "url": link_el.get("href", ""),
                            "snippet": (
                                snippet_el.get_text(strip=True) if snippet_el else ""
                            ),
                        }
                    )
        except ImportError:
            results = [
                {
                    "note": "Install beautifulsoup4 for better parsing",
                    "raw_length": len(response.text),
                }
            ]
        return results

    def _register_net_actions(self):
        """Register all network actions."""

        @self.action("search", "Web search query")
        async def search(
            ctx: MCPContext,
            query: str,
            engine: str = "hanzo",
            limit: int = 10,
        ) -> dict:
            """Perform web search.

            Prefers the cloud Bing meta-search (api.hanzo.ai /v1/websearch/search)
            and falls back to local DuckDuckGo when the cloud is unreachable or
            no API key is configured.

            Args:
                query: Search query
                engine: hanzo (cloud, default) | duckduckgo (local)
                limit: Max results

            Returns:
                {results: [{url, title, snippet}], query, engine, count}

            Effect: NONDETERMINISTIC_EFFECT
            """
            if engine in ("hanzo", "auto", "bing"):
                cloud = self._get_cloud()
                if cloud is not None:
                    try:
                        data = await cloud.get("/v1/websearch/search", {"q": query})
                        results = [
                            {
                                "url": r.get("url", ""),
                                "title": r.get("title", ""),
                                "snippet": r.get("content") or r.get("snippet", ""),
                            }
                            for r in (data.get("results") or [])[:limit]
                        ]
                        return {
                            "results": results,
                            "query": query,
                            "engine": "hanzo",
                            "count": len(results),
                        }
                    except CloudError:
                        pass  # fall through to local DuckDuckGo

            results = await self._duckduckgo_search(query, limit)
            return {
                "results": results,
                "query": query,
                "engine": "duckduckgo",
                "count": len(results),
            }

        @self.action("web_read", "Fetch a URL → clean markdown")
        async def web_read(
            ctx: MCPContext,
            url: str,
        ) -> dict:
            """Read a web page as clean markdown.

            Prefers the cloud reader (api.hanzo.ai /v1/crawl, Crawl4AI) and falls
            back to a local fetch + text extraction when the cloud is unreachable.

            Returns:
                {url, markdown, source: "cloud" | "local", metadata?}

            Effect: NONDETERMINISTIC_EFFECT
            """
            cloud = self._get_cloud()
            if cloud is not None:
                try:
                    data = await cloud.post("/v1/crawl", {"url": url})
                    markdown = _extract_markdown(data)
                    if markdown:
                        return {
                            "url": url,
                            "markdown": markdown,
                            "source": "cloud",
                            "metadata": _crawl_metadata(data),
                        }
                except CloudError:
                    pass  # fall through to local fetch

            client = await self._get_client()
            try:
                response = await client.get(url)
            except Exception as e:
                raise ToolError(
                    code="INTERNAL_ERROR",
                    message=f"web_read failed (cloud + local): {e}",
                    details={"url": url},
                )
            text = self._extract_text(response.text)
            return {
                "url": str(response.url),
                "markdown": text,
                "source": "local",
                "status": response.status_code,
            }

        @self.action("research", "Research a question → cited answer + sources")
        async def research(
            ctx: MCPContext,
            query: str,
            mode: str = "research",
        ) -> dict:
            """Research a question end to end and return a cited answer.

            Search finds pages and web_read reads one; research is the whole
            loop behind a single endpoint — the cloud answer engine
            (api.hanzo.ai /v1/ask) plans queries, searches, reads the best
            pages and writes an answer that cites them. Its progress frames are
            consumed here, so the caller gets the finished result without
            orchestrating search + web_read itself.

            Args:
                query: The question to research
                mode: research (default); "deep" names the same pass

            Returns:
                {answer, sources: [{url, title, favicon}], follow_ups, query, mode}

            Effect: NONDETERMINISTIC_EFFECT
            """
            if not query or not query.strip():
                raise InvalidParamsError("query is required", param="query")
            mode = _research_mode(mode)
            cloud = self._get_cloud()
            if cloud is None:
                raise ToolError(
                    code="INVALID_PARAMS",
                    message="Hanzo Cloud not configured: set HANZO_API_KEY "
                    "or add .apiKey to ~/.hanzo/config.json",
                )

            answer = ""
            deltas: list[str] = []
            sources: list = []
            follow_ups: list[str] = []
            async for event in cloud.stream(
                "/v1/ask", {"q": query, "mode": mode}, timeout=RESEARCH_TIMEOUT
            ):
                kind = event.get("type")
                if kind == "text":
                    deltas.append(event.get("delta") or "")
                elif kind == "sources":
                    sources = event.get("sources") or sources
                elif kind == "follow_ups":
                    follow_ups = event.get("questions") or []
                elif kind == "done":
                    answer = event.get("answer") or ""
                    sources = event.get("sources") or sources
                    break
                elif kind == "error":
                    raise ToolError(
                        code="INTERNAL_ERROR",
                        message=event.get("message") or "research stream failed",
                        details={"query": query},
                    )
                # status frames are progress, not result

            return {
                # The done frame carries the finished text; the accumulated
                # deltas are the same answer, and stand in if it arrives empty.
                "answer": answer or "".join(deltas),
                "sources": [_source(s) for s in sources],
                "follow_ups": follow_ups,
                "query": query,
                "mode": mode,
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

        @self.action("request", "Full HTTP request with method/headers/body")
        async def request(
            ctx: MCPContext,
            url: str,
            method: str = "GET",
            headers: dict | None = None,
            body: str | None = None,
            timeout: int = 30,
        ) -> dict:
            """HTTP request with full control over method, headers, body.

            Unlike 'fetch' which focuses on text extraction, 'request' returns
            the raw response with status, headers, and body.

            Effect: NONDETERMINISTIC_EFFECT
            """
            client = await self._get_client()

            try:
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    content=body,
                    timeout=timeout,
                )
            except Exception as e:
                raise ToolError(
                    code="INTERNAL_ERROR",
                    message=f"Request failed: {e}",
                    details={"url": url, "method": method},
                )

            content_type = response.headers.get("content-type", "")
            resp_headers = dict(response.headers)

            if "json" in content_type:
                try:
                    body_data = response.json()
                except Exception:
                    body_data = response.text
            else:
                body_data = response.text[:50000] if len(response.text) > 50000 else response.text

            return {
                "status": response.status_code,
                "headers": resp_headers,
                "body": body_data,
            }

        @self.action("open", "Open URL in browser")
        async def open_url(
            ctx: MCPContext,
            url: str,
        ) -> dict:
            """Open URL in the system default browser.

            Effect: NONDETERMINISTIC_EFFECT
            """
            import platform

            system = platform.system().lower()
            if system == "darwin":
                cmd = ["open", url]
            elif system == "linux":
                cmd = ["xdg-open", url]
            elif system == "windows":
                cmd = ["start", url]
            else:
                cmd = ["xdg-open", url]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            return {"url": url, "opened": True}


# Singleton
fetch_tool = FetchTool
