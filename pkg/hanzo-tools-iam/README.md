# hanzo-tools-iam

MCP tool for Hanzo IAM — users, organizations, roles, permissions, providers,
applications, tokens, sessions, invitations and audit records.

## One tenant, resolved from IAM

The caller of this tool is a language model, so the organization it acts in is
not a deployment constant. There is exactly one source for it: IAM's own
`/v1/iam/whoami`, which resolves the token subject to the live user row and
returns the same `owner` IAM's authorization layer pins every request to.

Never a literal, never configuration, never the `owner` token claim — that one
names the *application's* organization, which is why IAM itself refuses to
derive authority from it. **A missing tenant is a refusal, not a fallback.**

Pass `owner` only to name a *different* organization. IAM grants that to a
superadmin and refuses it for everyone else; the client sends what you meant
and lets the server decide.

## Installation

```bash
pip install hanzo-tools-iam
```

Part of the [hanzo-mcp](https://pypi.org/project/hanzo-mcp/) ecosystem.
