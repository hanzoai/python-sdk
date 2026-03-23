"""
Hanzo KMS CLI — fetch secrets non-interactively.

Usage:
    # Via env vars
    HANZO_KMS_EMAIL=z@hanzo.ai HANZO_KMS_PASSWORD=... python -m hanzo_kms get SECRET_NAME --project ID --env prod

    # Via flags
    python -m hanzo_kms get SECRET_NAME --email z@hanzo.ai --password ... --project ID --env prod

    # List secrets
    python -m hanzo_kms list --project ID --env prod

    # With universal auth
    HANZO_KMS_CLIENT_ID=... HANZO_KMS_CLIENT_SECRET=... python -m hanzo_kms get SECRET_NAME --project ID --env prod

    # With pre-authenticated token
    HANZO_KMS_TOKEN=... python -m hanzo_kms get SECRET_NAME --project ID --env prod
"""

import argparse
import os
import sys

from .client import KMSClient
from .models import (
    AuthenticationOptions,
    ClientSettings,
    TokenAuthMethod,
    UniversalAuthMethod,
    UserPasswordAuthMethod,
)


def _build_client(args: argparse.Namespace) -> KMSClient:
    """Build KMS client from CLI args + env vars."""
    site_url = args.url or os.getenv("HANZO_KMS_URL", "https://kms.hanzo.ai")

    # Auth priority: token > universal-auth > user/password > env
    token = args.token or os.getenv("HANZO_KMS_TOKEN", os.getenv("INFISICAL_TOKEN", ""))
    client_id = args.client_id or os.getenv("HANZO_KMS_CLIENT_ID", "")
    client_secret = args.client_secret or os.getenv("HANZO_KMS_CLIENT_SECRET", "")
    email = args.email or os.getenv("HANZO_KMS_EMAIL", "")
    password = args.password or os.getenv("HANZO_KMS_PASSWORD", "")

    auth = None
    if token:
        auth = AuthenticationOptions(token=TokenAuthMethod(access_token=token))
    elif client_id and client_secret:
        auth = AuthenticationOptions(
            universal_auth=UniversalAuthMethod(client_id=client_id, client_secret=client_secret)
        )
    elif email and password:
        auth = AuthenticationOptions(
            user_password=UserPasswordAuthMethod(email=email, password=password)
        )

    if not auth:
        # Try env fallback
        client = KMSClient(debug=getattr(args, "debug", False))
        if client.settings.auth:
            return client
        print("Error: No auth configured. Set HANZO_KMS_TOKEN, HANZO_KMS_CLIENT_ID/SECRET, or HANZO_KMS_EMAIL/PASSWORD", file=sys.stderr)
        sys.exit(1)

    settings = ClientSettings(site_url=site_url, auth=auth)
    return KMSClient(settings=settings, debug=getattr(args, "debug", False))


def main() -> None:
    parser = argparse.ArgumentParser(prog="hanzo-kms", description="Hanzo KMS CLI")
    parser.add_argument("--url", help="KMS URL (default: https://kms.hanzo.ai)")
    parser.add_argument("--token", help="Pre-authenticated access token")
    parser.add_argument("--client-id", help="Universal auth client ID")
    parser.add_argument("--client-secret", help="Universal auth client secret")
    parser.add_argument("--email", help="User email for SRP auth")
    parser.add_argument("--password", help="User password for SRP auth")
    parser.add_argument("--debug", action="store_true")

    sub = parser.add_subparsers(dest="command")

    # get command
    get_p = sub.add_parser("get", help="Get a secret value")
    get_p.add_argument("name", help="Secret name")
    get_p.add_argument("--project", required=True, help="Project ID")
    get_p.add_argument("--env", default="prod", help="Environment (default: prod)")
    get_p.add_argument("--path", default="/", help="Secret path")

    # list command
    list_p = sub.add_parser("list", help="List secrets")
    list_p.add_argument("--project", required=True, help="Project ID")
    list_p.add_argument("--env", default="prod", help="Environment (default: prod)")
    list_p.add_argument("--path", default="/", help="Secret path")
    list_p.add_argument("--keys-only", action="store_true", help="Only print keys")

    # export command
    export_p = sub.add_parser("export", help="Export secrets as env vars")
    export_p.add_argument("--project", required=True, help="Project ID")
    export_p.add_argument("--env", default="prod", help="Environment (default: prod)")
    export_p.add_argument("--path", default="/", help="Secret path")
    export_p.add_argument("--format", choices=["env", "json"], default="env")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    client = _build_client(args)

    if args.command == "get":
        secret = client.get_secret(
            project_id=args.project,
            environment=args.env,
            secret_name=args.name,
            path=args.path,
        )
        print(secret.secret_value)

    elif args.command == "list":
        secrets = client.list_secrets(
            project_id=args.project,
            environment=args.env,
            path=args.path,
        )
        for s in secrets:
            if args.keys_only:
                print(s.secret_key)
            else:
                print(f"{s.secret_key}={s.secret_value}")

    elif args.command == "export":
        import json as _json

        secrets = client.list_secrets(
            project_id=args.project,
            environment=args.env,
            path=args.path,
        )
        if args.format == "json":
            print(_json.dumps({s.secret_key: s.secret_value for s in secrets}, indent=2))
        else:
            for s in secrets:
                print(f"{s.secret_key}={s.secret_value}")

    client.close()


if __name__ == "__main__":
    main()
