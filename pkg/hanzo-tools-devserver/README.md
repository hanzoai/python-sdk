# hanzo-tools-devserver

The `devserver` tool for hanzo-mcp: running dev servers as MCP nodes.

- `index` — find dev servers on this machine (Next, Vite, Nuxt, Remix, React Router,
  Astro, SvelteKit) from each process's argv, cwd and listening ports, and list the
  tools of the MCP each one serves (Next 16+ at `/_next/mcp`; Vite-based frameworks at
  `/__mcp/sse` with `vite-plugin-mcp` or `nuxt-mcp-dev`).
- `call` — run one of those tools.
- `errors` — current build/runtime errors: the server's `get_errors` where it has one,
  otherwise Vite's error overlay, console errors and page errors, read through the
  `browser` tool.

`hanzo_tools.devserver.discover()` returns the servers as plain `DevServer` records.

```bash
pip install hanzo-tools-devserver
```
