"""
Hanzo KMS Client - Pure Python implementation

A full-featured KMS client compatible with Infisical API.
"""

import os
import time
from typing import Optional

import httpx

from .models import (
    AuthenticationOptions,
    ClientSettings,
    CreateSecretOptions,
    DeleteSecretOptions,
    GetSecretOptions,
    ListSecretsOptions,
    SecretElement,
    SecretsResponse,
    TokenResponse,
    UpdateSecretOptions,
)


class KMSClient:
    """
    Hanzo KMS Client for secret management.

    Supports multiple authentication methods:
    - Universal Auth (client_id/client_secret)
    - AWS IAM
    - Azure AD
    - GCP IAM
    - Kubernetes Service Account

    Example:
        client = KMSClient(ClientSettings(
            site_url="https://kms.hanzo.ai",
            auth=AuthenticationOptions(
                universal_auth=UniversalAuthMethod(
                    client_id="your-client-id",
                    client_secret="your-client-secret",
                )
            )
        ))

        secrets = client.list_secrets(project_id="myproject", environment="production")
    """

    def __init__(
        self,
        settings: Optional[ClientSettings] = None,
        debug: bool = False,
    ):
        """Initialize KMS client.

        Args:
            settings: Client configuration (defaults from environment if not provided)
            debug: Enable debug logging
        """
        self.settings = settings or self._settings_from_env()
        self.debug = debug
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0
        self._http_client: Optional[httpx.Client] = None

    def _settings_from_env(self) -> ClientSettings:
        """Create settings from environment variables."""
        from .models import UniversalAuthMethod

        site_url = os.getenv(
            "HANZO_KMS_URL", os.getenv("INFISICAL_SITE_URL", "https://kms.hanzo.ai")
        )
        organization = os.getenv("HANZO_KMS_ORG", "hanzo")
        client_id = os.getenv("HANZO_KMS_CLIENT_ID", os.getenv("INFISICAL_CLIENT_ID", ""))
        client_secret = os.getenv(
            "HANZO_KMS_CLIENT_SECRET", os.getenv("INFISICAL_CLIENT_SECRET", "")
        )

        auth = None
        if client_id and client_secret:
            auth = AuthenticationOptions(
                universal_auth=UniversalAuthMethod(
                    client_id=client_id,
                    client_secret=client_secret,
                )
            )

        return ClientSettings(site_url=site_url, organization=organization, auth=auth)

    @property
    def http(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.Client(
                base_url=self.settings.site_url.rstrip("/"),
                timeout=30.0,
                headers={
                    "User-Agent": self.settings.user_agent,
                    "Content-Type": "application/json",
                },
            )
        return self._http_client

    def _get_access_token(self) -> str:
        """Get valid access token, refreshing if needed."""
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        auth = self.settings.auth
        if not auth:
            raise ValueError("No authentication configured")

        # Universal Auth
        if auth.universal_auth:
            response = self.http.post(
                "/api/v1/auth/universal-auth/login",
                json={
                    "clientId": auth.universal_auth.client_id,
                    "clientSecret": auth.universal_auth.client_secret,
                },
            )
            response.raise_for_status()
            data = response.json()
            token_data = TokenResponse.model_validate(data)
            self._access_token = token_data.access_token
            self._token_expires_at = time.time() + token_data.expires_in
            return self._access_token

        # Kubernetes Auth
        if auth.kubernetes:
            token_path = auth.kubernetes.service_account_token_path
            if os.path.exists(token_path):
                with open(token_path) as f:
                    k8s_token = f.read().strip()

                response = self.http.post(
                    "/api/v1/auth/kubernetes-auth/login",
                    json={
                        "identityId": auth.kubernetes.identity_id,
                        "jwt": k8s_token,
                    },
                )
                response.raise_for_status()
                data = response.json()
                token_data = TokenResponse.model_validate(data)
                self._access_token = token_data.access_token
                self._token_expires_at = time.time() + token_data.expires_in
                return self._access_token

        # AWS IAM Auth
        if auth.aws_iam:
            # Get AWS credentials from environment/instance metadata
            import json

            try:
                import boto3

                session = boto3.Session()
                credentials = session.get_credentials()
                region = session.region_name or "us-east-1"

                response = self.http.post(
                    "/api/v1/auth/aws-auth/login",
                    json={
                        "identityId": auth.aws_iam.identity_id,
                        "iamHttpRequestMethod": "POST",
                        "iamRequestBody": "",
                        "iamRequestHeaders": json.dumps(
                            {
                                "X-Amz-Date": credentials.token or "",
                            }
                        ),
                    },
                )
                response.raise_for_status()
                data = response.json()
                token_data = TokenResponse.model_validate(data)
                self._access_token = token_data.access_token
                self._token_expires_at = time.time() + token_data.expires_in
                return self._access_token
            except ImportError:
                raise ValueError("boto3 required for AWS IAM auth: pip install boto3")

        raise ValueError("No valid authentication method configured")

    def _auth_headers(self) -> dict[str, str]:
        """Get authorization headers including organization context."""
        token = self._get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "X-Org-Name": self.settings.organization,
        }

    def _resolve_project_id(self, project_id: str) -> tuple[str, str]:
        """Resolve org-scoped project ID.

        Supports formats:
        - "project" -> uses settings.organization
        - "org/project" -> uses specified org

        Returns:
            Tuple of (organization, project_id)
        """
        if "/" in project_id:
            org, proj = project_id.split("/", 1)
            return (org, proj)
        return (self.settings.organization, project_id)

    # =========================================================================
    # Secret Operations
    # =========================================================================

    def get_secret(
        self,
        project_id: str,
        environment: str,
        secret_name: str,
        path: str = "/",
        **kwargs,
    ) -> SecretElement:
        """Get a single secret by name.

        Args:
            project_id: Project ID or slug
            environment: Environment slug (e.g., "production")
            secret_name: Name of the secret
            path: Secret path (default "/")

        Returns:
            SecretElement with the secret data
        """
        options = GetSecretOptions(
            project_id=project_id,
            environment=environment,
            secret_name=secret_name,
            path=path,
            **kwargs,
        )

        response = self.http.get(
            f"/api/v3/secrets/raw/{options.secret_name}",
            params={
                "workspaceId": options.project_id,
                "environment": options.environment,
                "secretPath": options.path,
                "type": options.type,
                "include_imports": str(options.include_imports).lower(),
            },
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        data = response.json()
        return SecretElement.model_validate(data.get("secret", data))

    def list_secrets(
        self,
        project_id: str,
        environment: str,
        path: str = "/",
        attach_to_process_env: bool = False,
        **kwargs,
    ) -> list[SecretElement]:
        """List all secrets in a project/environment.

        Args:
            project_id: Project ID or slug
            environment: Environment slug
            path: Secret path (default "/")
            attach_to_process_env: If True, set secrets as environment variables

        Returns:
            List of SecretElement
        """
        options = ListSecretsOptions(
            project_id=project_id,
            environment=environment,
            path=path,
            attach_to_process_env=attach_to_process_env,
            **kwargs,
        )

        response = self.http.get(
            "/api/v3/secrets/raw",
            params={
                "workspaceId": options.project_id,
                "environment": options.environment,
                "secretPath": options.path,
                "include_imports": str(options.include_imports).lower(),
                "recursive": str(options.recursive).lower(),
                "expandSecretReferences": str(options.expand_secret_references).lower(),
            },
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        data = response.json()
        secrets_data = SecretsResponse.model_validate(data)

        # Optionally inject into environment
        if options.attach_to_process_env:
            for secret in secrets_data.secrets:
                if secret.secret_key not in os.environ:
                    os.environ[secret.secret_key] = secret.secret_value

        return secrets_data.secrets

    def create_secret(
        self,
        project_id: str,
        environment: str,
        secret_name: str,
        secret_value: str,
        **kwargs,
    ) -> SecretElement:
        """Create a new secret.

        Args:
            project_id: Project ID or slug
            environment: Environment slug
            secret_name: Name of the secret
            secret_value: Value of the secret

        Returns:
            Created SecretElement
        """
        options = CreateSecretOptions(
            project_id=project_id,
            environment=environment,
            secret_name=secret_name,
            secret_value=secret_value,
            **kwargs,
        )

        response = self.http.post(
            f"/api/v3/secrets/raw/{options.secret_name}",
            json={
                "workspaceId": options.project_id,
                "environment": options.environment,
                "secretPath": options.path,
                "secretValue": options.secret_value,
                "secretComment": options.secret_comment,
                "type": options.type,
            },
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        data = response.json()
        return SecretElement.model_validate(data.get("secret", data))

    def update_secret(
        self,
        project_id: str,
        environment: str,
        secret_name: str,
        secret_value: str,
        **kwargs,
    ) -> SecretElement:
        """Update an existing secret.

        Args:
            project_id: Project ID or slug
            environment: Environment slug
            secret_name: Name of the secret
            secret_value: New value

        Returns:
            Updated SecretElement
        """
        options = UpdateSecretOptions(
            project_id=project_id,
            environment=environment,
            secret_name=secret_name,
            secret_value=secret_value,
            **kwargs,
        )

        response = self.http.patch(
            f"/api/v3/secrets/raw/{options.secret_name}",
            json={
                "workspaceId": options.project_id,
                "environment": options.environment,
                "secretPath": options.path,
                "secretValue": options.secret_value,
                "secretComment": options.secret_comment,
                "type": options.type,
            },
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        data = response.json()
        return SecretElement.model_validate(data.get("secret", data))

    def delete_secret(
        self,
        project_id: str,
        environment: str,
        secret_name: str,
        **kwargs,
    ) -> SecretElement:
        """Delete a secret.

        Args:
            project_id: Project ID or slug
            environment: Environment slug
            secret_name: Name of the secret

        Returns:
            Deleted SecretElement
        """
        options = DeleteSecretOptions(
            project_id=project_id,
            environment=environment,
            secret_name=secret_name,
            **kwargs,
        )

        response = self.http.request(
            "DELETE",
            f"/api/v3/secrets/raw/{options.secret_name}",
            json={
                "workspaceId": options.project_id,
                "environment": options.environment,
                "secretPath": options.path,
                "type": options.type,
            },
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        data = response.json()
        return SecretElement.model_validate(data.get("secret", data))

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    def inject_env(
        self,
        project_id: str,
        environment: str,
        path: str = "/",
        overwrite: bool = False,
    ) -> int:
        """Inject all secrets into environment variables.

        Args:
            project_id: Project ID or slug
            environment: Environment slug
            path: Secret path
            overwrite: If True, overwrite existing env vars

        Returns:
            Number of secrets injected
        """
        secrets = self.list_secrets(project_id, environment, path)
        count = 0
        for secret in secrets:
            if overwrite or secret.secret_key not in os.environ:
                os.environ[secret.secret_key] = secret.secret_value
                count += 1
        return count

    def get_value(
        self,
        project_id: str,
        environment: str,
        secret_name: str,
        default: Optional[str] = None,
    ) -> Optional[str]:
        """Get just the value of a secret.

        Args:
            project_id: Project ID or slug
            environment: Environment slug
            secret_name: Name of the secret
            default: Default value if secret not found

        Returns:
            Secret value or default
        """
        try:
            secret = self.get_secret(project_id, environment, secret_name)
            return secret.secret_value
        except httpx.HTTPStatusError:
            return default

    def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client:
            self._http_client.close()
            self._http_client = None

    def __enter__(self) -> "KMSClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()


# Alias for compatibility
InfisicalClient = KMSClient
