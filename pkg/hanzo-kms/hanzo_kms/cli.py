"""Hanzo KMS CLI — read and write secrets non-interactively.

A secret is (org, path, name, env). The org comes from ``--org`` /
``HANZO_KMS_ORG`` (default ``hanzo``); path and name are positional.

Usage:
    # Machine identity from the environment
    export HANZO_KMS_CLIENT_ID=... HANZO_KMS_CLIENT_SECRET=...
    python -m hanzo_kms get providers/lux deploy-mnemonic --env prod

    # Or a pre-issued IAM bearer token
    HANZO_KMS_TOKEN=... python -m hanzo_kms list --path providers/lux --env prod

    python -m hanzo_kms set providers/lux deploy-mnemonic "word word ..." --env prod
    python -m hanzo_kms delete providers/lux deploy-mnemonic --env prod
    python -m hanzo_kms export --path providers/lux --env prod --format json
"""

import argparse
import json
import sys

from .client import KMSClient
from .models import settings_from_env
from .routes import DEFAULT_ENV


def _client(args: argparse.Namespace) -> KMSClient:
    """Build a client from the environment, overlaid with CLI flags."""
    settings = settings_from_env()
    if args.url:
        settings.site_url = args.url
    if args.org:
        settings.org = args.org
    if args.token:
        settings.access_token = args.token
    if args.client_id:
        settings.client_id = args.client_id
    if args.client_secret:
        settings.client_secret = args.client_secret

    if not (settings.access_token or (settings.client_id and settings.client_secret)):
        print(
            "Error: no auth configured. Set HANZO_KMS_TOKEN, or "
            "HANZO_KMS_CLIENT_ID and HANZO_KMS_CLIENT_SECRET.",
            file=sys.stderr,
        )
        sys.exit(1)

    return KMSClient(settings, debug=args.debug)


def main() -> None:
    parser = argparse.ArgumentParser(prog="hanzo-kms", description="Hanzo KMS CLI")
    parser.add_argument("--url", help="KMS URL (default: https://kms.hanzo.ai)")
    parser.add_argument("--org", help="Organization (default: hanzo)")
    parser.add_argument("--token", help="Pre-issued IAM bearer token")
    parser.add_argument("--client-id", help="Machine identity client ID")
    parser.add_argument("--client-secret", help="Machine identity client secret")
    parser.add_argument("--debug", action="store_true")

    sub = parser.add_subparsers(dest="command")

    list_p = sub.add_parser("list", help="List secret names at a path")
    list_p.add_argument("--path", default="", help="Secret path")
    list_p.add_argument("--env", default=DEFAULT_ENV, help=f"Environment (default: {DEFAULT_ENV})")

    get_p = sub.add_parser("get", help="Print a secret value")
    get_p.add_argument("path", help="Secret path, e.g. providers/lux")
    get_p.add_argument("name", help="Secret name")
    get_p.add_argument("--env", default=DEFAULT_ENV, help=f"Environment (default: {DEFAULT_ENV})")

    set_p = sub.add_parser("set", help="Create or replace a secret")
    set_p.add_argument("path", help="Secret path")
    set_p.add_argument("name", help="Secret name")
    set_p.add_argument("value", help="Secret value")
    set_p.add_argument("--env", default=DEFAULT_ENV, help=f"Environment (default: {DEFAULT_ENV})")

    del_p = sub.add_parser("delete", help="Delete a secret")
    del_p.add_argument("path", help="Secret path")
    del_p.add_argument("name", help="Secret name")
    del_p.add_argument("--env", default=DEFAULT_ENV, help=f"Environment (default: {DEFAULT_ENV})")

    export_p = sub.add_parser("export", help="Export every secret at a path")
    export_p.add_argument("--path", default="", help="Secret path")
    export_p.add_argument("--env", default=DEFAULT_ENV, help=f"Environment (default: {DEFAULT_ENV})")
    export_p.add_argument("--format", choices=["env", "json"], default="env")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    client = _client(args)
    try:
        if args.command == "list":
            for name in client.list_secrets(args.path, args.env):
                print(name)

        elif args.command == "get":
            print(client.get_secret(args.path, args.name, args.env))

        elif args.command == "set":
            client.put_secret(args.path, args.name, args.value, args.env)
            print(f"set {args.path}/{args.name} ({args.env})")

        elif args.command == "delete":
            client.delete_secret(args.path, args.name, args.env)
            print(f"deleted {args.path}/{args.name} ({args.env})")

        elif args.command == "export":
            names = client.list_secrets(args.path, args.env)
            values = {name: client.get_secret(args.path, name, args.env) for name in names}
            if args.format == "json":
                print(json.dumps(values, indent=2))
            else:
                for name, value in values.items():
                    print(f"{name}={value}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
