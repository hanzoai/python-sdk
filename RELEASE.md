# Releasing

One lane: `.hanzo/workflows/publish-pypi.yml`, on the git.hanzo.ai runner fleet.
It reads the PyPI token from KMS at publish time — nothing else in this repo
uploads, and no token is ever handed to a shell here.

Bump the version, commit, push a tag:

```bash
# pkg/hanzo-mcp/pyproject.toml -> version = "0.15.15"
git commit -am "hanzo-mcp 0.15.15"
git push origin main
git tag hanzo-mcp-0.15.15 && git push origin hanzo-mcp-0.15.15
```

The tag names the packages:

| tag | publishes |
|---|---|
| `v3.2.13` | every workspace package |
| `hanzoai-v3.2.13` | the root `hanzoai` client alone |
| `hanzo-tools-0.3.5` | every `pkg/hanzo-tools-*` |
| `hanzo-mcp-0.15.15` | the matching `pkg/<name>`, else `hanzo` |

A `v*` tag is not as broad as it looks: uploads pass `--skip-existing`, so a
package whose version is already on PyPI is a no-op. What it does publish is
every package whose in-tree version is new — which is the point, and also the
reason to look before you tag.

Watch the run under Actions on git.hanzo.ai. Versions are semver, and PyPI never
lets a version be replaced: a bad release is fixed by a higher one.

## Before you tag

Build what the lane will build and read the metadata you are about to publish —
the registry page is the first thing a reader sees, and it is permanent.

```bash
python -m build . --outdir dist          # or pkg/<name>
python -m twine check dist/*
```

`twine check` catches a README that will not render. It does not catch a missing
one: a package with no `readme`, `license` or `authors` in its `pyproject.toml`
uploads happily and lands as a blank page.

## If the lane fails

Read the job log — every failure mode it knows about prints a line saying which
credential or path it wanted. The KMS read is the one worth naming: KMS serves
`GET /v1/kms/secrets/<path>/<name>?env=<env>` and takes the org from the caller's
token, so a request in any other shape 404s exactly like an unseeded path. Prove
a route against a secret you know exists before concluding a secret is missing.
