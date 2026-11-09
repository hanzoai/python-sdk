# hanzo-login

Who a Hanzo tool acts as. Every Python tool on a machine resolves its credential here, so a
person signs in once, with the `hanzo` CLI, and every tool follows. Standard library only.

```python
import hanzo_login as login

cred = login.credential()  # Credential(source='login', identity=None, refused=None)
cred.secret  # the bearer token (never in repr)
login.credential("hanzo/z")  # that identity's token, whatever else is set
login.identities()  # [{'key': 'hanzo/z', 'owner': 'hanzo', 'active': True, ...}]
login.use("hanzo/z")  # this process only
login.switch("hanzo/z")  # the whole machine: the CLI's active identity
```

Order: `HANZO_API_KEY`, then the CLI's login (`hanzo auth token`), then `apiKey` in
`~/.hanzo/config.json` (legacy, last, so a stale key never shadows a login). Naming an
identity always asks the login, even with a key set, and never falls through to another.

The CLI is `~/.local/bin/hanzo`, never a lookup on `PATH` (Debian's hanzo-ide package puts a
GUI at `/usr/bin/hanzo` that opens a window on any arguments). The CLI owns the identity
store and the refresh; this package reads neither. A login's token is kept 300 seconds,
per identity.
