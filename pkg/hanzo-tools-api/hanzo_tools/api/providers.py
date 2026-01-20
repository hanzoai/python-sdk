"""Provider configurations and environment variable mappings.

Contains built-in configurations for 30+ cloud providers,
plus 1100+ auto-generated configs from APIs.guru + oapis.org.
"""

from __future__ import annotations

from .apis_guru_providers import APIS_GURU_PROVIDERS
from .models import AuthType, ProviderConfig

# =============================================================================
# Environment Variable Mappings
# =============================================================================

ENV_VAR_MAPPINGS: dict[str, list[str]] = {
    # Cloud Providers
    "cloudflare": ["CLOUDFLARE_API_TOKEN", "CF_API_TOKEN", "CLOUDFLARE_API_KEY", "CF_API_KEY"],
    "aws": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "gcp": ["GOOGLE_APPLICATION_CREDENTIALS", "GCP_API_KEY", "GOOGLE_API_KEY"],
    "azure": ["AZURE_API_KEY", "AZURE_SUBSCRIPTION_KEY"],
    "digitalocean": ["DIGITALOCEAN_TOKEN", "DO_TOKEN", "DIGITALOCEAN_ACCESS_TOKEN"],
    "linode": ["LINODE_TOKEN", "LINODE_API_TOKEN"],
    "vultr": ["VULTR_API_KEY"],
    "hetzner": ["HETZNER_API_TOKEN", "HCLOUD_TOKEN"],
    # AI Providers
    "openai": ["OPENAI_API_KEY"],
    "anthropic": ["ANTHROPIC_API_KEY"],
    "together": ["TOGETHER_API_KEY", "TOGETHER_AI_KEY"],
    "replicate": ["REPLICATE_API_TOKEN", "REPLICATE_API_KEY"],
    "huggingface": ["HF_TOKEN", "HUGGINGFACE_TOKEN", "HUGGING_FACE_HUB_TOKEN"],
    "cohere": ["COHERE_API_KEY", "CO_API_KEY"],
    "perplexity": ["PERPLEXITY_API_KEY", "PPLX_API_KEY"],
    "groq": ["GROQ_API_KEY"],
    "mistral": ["MISTRAL_API_KEY"],
    "fireworks": ["FIREWORKS_API_KEY"],
    # Developer Platforms
    "github": ["GITHUB_TOKEN", "GH_TOKEN", "GITHUB_API_TOKEN"],
    "gitlab": ["GITLAB_TOKEN", "GITLAB_API_TOKEN"],
    "bitbucket": ["BITBUCKET_TOKEN", "BITBUCKET_API_TOKEN"],
    # Deployment Platforms
    "vercel": ["VERCEL_TOKEN", "VERCEL_API_TOKEN"],
    "netlify": ["NETLIFY_AUTH_TOKEN", "NETLIFY_TOKEN"],
    "fly": ["FLY_API_TOKEN", "FLY_ACCESS_TOKEN"],
    "railway": ["RAILWAY_TOKEN", "RAILWAY_API_TOKEN"],
    "render": ["RENDER_API_KEY", "RENDER_TOKEN"],
    "heroku": ["HEROKU_API_KEY", "HEROKU_TOKEN"],
    # Payment/Commerce
    "stripe": ["STRIPE_API_KEY", "STRIPE_SECRET_KEY"],
    "shopify": ["SHOPIFY_API_KEY", "SHOPIFY_ACCESS_TOKEN"],
    "paypal": ["PAYPAL_CLIENT_ID", "PAYPAL_CLIENT_SECRET"],
    # Communication
    "twilio": ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"],
    "sendgrid": ["SENDGRID_API_KEY"],
    "resend": ["RESEND_API_KEY"],
    "postmark": ["POSTMARK_API_TOKEN", "POSTMARK_SERVER_TOKEN"],
    "mailgun": ["MAILGUN_API_KEY"],
    "slack": ["SLACK_TOKEN", "SLACK_BOT_TOKEN", "SLACK_API_TOKEN"],
    "discord": ["DISCORD_TOKEN", "DISCORD_BOT_TOKEN"],
    # Databases/Backend
    "supabase": ["SUPABASE_API_KEY", "SUPABASE_SERVICE_KEY"],
    "planetscale": ["PLANETSCALE_TOKEN", "PSCALE_TOKEN"],
    "neon": ["NEON_API_KEY"],
    "upstash": ["UPSTASH_REDIS_REST_TOKEN", "UPSTASH_API_KEY"],
    "mongodb": ["MONGODB_API_KEY", "ATLAS_API_KEY"],
    "redis": ["REDIS_PASSWORD", "REDIS_API_KEY"],
    "fauna": ["FAUNA_SECRET", "FAUNA_KEY"],
    # Search/Analytics
    "algolia": ["ALGOLIA_API_KEY", "ALGOLIA_ADMIN_KEY"],
    "elasticsearch": ["ELASTIC_API_KEY", "ELASTICSEARCH_API_KEY"],
    "meilisearch": ["MEILI_MASTER_KEY", "MEILISEARCH_API_KEY"],
    "typesense": ["TYPESENSE_API_KEY"],
    # Monitoring/Observability
    "datadog": ["DD_API_KEY", "DATADOG_API_KEY"],
    "newrelic": ["NEW_RELIC_API_KEY", "NEWRELIC_API_KEY"],
    "sentry": ["SENTRY_AUTH_TOKEN", "SENTRY_DSN"],
    "grafana": ["GRAFANA_API_KEY", "GF_SECURITY_ADMIN_TOKEN"],
    # Storage/CDN
    "cloudinary": ["CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"],
    "imgix": ["IMGIX_API_KEY"],
    "bunny": ["BUNNY_API_KEY", "BUNNY_ACCESS_KEY"],
    "backblaze": ["B2_APPLICATION_KEY_ID", "B2_APPLICATION_KEY"],
    # Hanzo
    "hanzo": ["HANZO_API_KEY", "HANZO_TOKEN"],
}


# =============================================================================
# Provider Configurations
# =============================================================================

PROVIDER_CONFIGS: dict[str, ProviderConfig] = {
    # Cloud Providers
    "cloudflare": ProviderConfig(
        name="cloudflare",
        display_name="Cloudflare",
        base_url="https://api.cloudflare.com/client/v4",
        auth_type=AuthType.BEARER,
        spec_url="https://raw.githubusercontent.com/cloudflare/api-schemas/main/openapi.json",
        env_vars=["CLOUDFLARE_API_TOKEN", "CF_API_TOKEN", "CLOUDFLARE_API_KEY", "CF_API_KEY"],
    ),
    "digitalocean": ProviderConfig(
        name="digitalocean",
        display_name="DigitalOcean",
        base_url="https://api.digitalocean.com/v2",
        auth_type=AuthType.BEARER,
        spec_url="https://api-engineering.nyc3.cdn.digitaloceanspaces.com/spec-ci/DigitalOcean-public.v2.yaml",
        env_vars=["DIGITALOCEAN_TOKEN", "DO_TOKEN"],
    ),
    "hetzner": ProviderConfig(
        name="hetzner",
        display_name="Hetzner Cloud",
        base_url="https://api.hetzner.cloud/v1",
        auth_type=AuthType.BEARER,
        env_vars=["HETZNER_API_TOKEN", "HCLOUD_TOKEN"],
    ),
    # AI Providers
    "openai": ProviderConfig(
        name="openai",
        display_name="OpenAI",
        base_url="https://api.openai.com/v1",
        auth_type=AuthType.BEARER,
        spec_url="https://raw.githubusercontent.com/openai/openai-openapi/refs/heads/manual_spec/openapi.yaml",
        env_vars=["OPENAI_API_KEY"],
    ),
    "anthropic": ProviderConfig(
        name="anthropic",
        display_name="Anthropic",
        base_url="https://api.anthropic.com/v1",
        auth_type=AuthType.HEADER,
        auth_header="x-api-key",
        auth_prefix="",
        env_vars=["ANTHROPIC_API_KEY"],
        extra_headers={"anthropic-version": "2023-06-01"},
    ),
    "together": ProviderConfig(
        name="together",
        display_name="Together AI",
        base_url="https://api.together.xyz/v1",
        auth_type=AuthType.BEARER,
        env_vars=["TOGETHER_API_KEY"],
    ),
    "groq": ProviderConfig(
        name="groq",
        display_name="Groq",
        base_url="https://api.groq.com/openai/v1",
        auth_type=AuthType.BEARER,
        spec_url="https://raw.githubusercontent.com/janwilmake/handmade-openapis/main/groq.json",
        env_vars=["GROQ_API_KEY"],
    ),
    "mistral": ProviderConfig(
        name="mistral",
        display_name="Mistral AI",
        base_url="https://api.mistral.ai/v1",
        auth_type=AuthType.BEARER,
        env_vars=["MISTRAL_API_KEY"],
    ),
    # Developer Platforms
    "github": ProviderConfig(
        name="github",
        display_name="GitHub",
        base_url="https://api.github.com",
        auth_type=AuthType.BEARER,
        spec_url="https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.json",
        env_vars=["GITHUB_TOKEN", "GH_TOKEN"],
        extra_headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"},
    ),
    "gitlab": ProviderConfig(
        name="gitlab",
        display_name="GitLab",
        base_url="https://gitlab.com/api/v4",
        auth_type=AuthType.HEADER,
        auth_header="PRIVATE-TOKEN",
        auth_prefix="",
        env_vars=["GITLAB_TOKEN"],
    ),
    # Deployment Platforms
    "vercel": ProviderConfig(
        name="vercel",
        display_name="Vercel",
        base_url="https://api.vercel.com",
        auth_type=AuthType.BEARER,
        env_vars=["VERCEL_TOKEN"],
    ),
    "netlify": ProviderConfig(
        name="netlify",
        display_name="Netlify",
        base_url="https://api.netlify.com/api/v1",
        auth_type=AuthType.BEARER,
        env_vars=["NETLIFY_AUTH_TOKEN"],
    ),
    "fly": ProviderConfig(
        name="fly",
        display_name="Fly.io",
        base_url="https://api.fly.io/v1",
        auth_type=AuthType.BEARER,
        env_vars=["FLY_API_TOKEN"],
    ),
    "railway": ProviderConfig(
        name="railway",
        display_name="Railway",
        base_url="https://backboard.railway.app/graphql/v2",
        auth_type=AuthType.BEARER,
        env_vars=["RAILWAY_TOKEN"],
    ),
    "render": ProviderConfig(
        name="render",
        display_name="Render",
        base_url="https://api.render.com/v1",
        auth_type=AuthType.BEARER,
        env_vars=["RENDER_API_KEY"],
    ),
    # Payment
    "stripe": ProviderConfig(
        name="stripe",
        display_name="Stripe",
        base_url="https://api.stripe.com/v1",
        auth_type=AuthType.BASIC,
        spec_url="https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.json",
        env_vars=["STRIPE_API_KEY", "STRIPE_SECRET_KEY"],
    ),
    # Communication
    "sendgrid": ProviderConfig(
        name="sendgrid",
        display_name="SendGrid",
        base_url="https://api.sendgrid.com/v3",
        auth_type=AuthType.BEARER,
        env_vars=["SENDGRID_API_KEY"],
    ),
    "resend": ProviderConfig(
        name="resend",
        display_name="Resend",
        base_url="https://api.resend.com",
        auth_type=AuthType.BEARER,
        env_vars=["RESEND_API_KEY"],
    ),
    "slack": ProviderConfig(
        name="slack",
        display_name="Slack",
        base_url="https://slack.com/api",
        auth_type=AuthType.BEARER,
        env_vars=["SLACK_TOKEN", "SLACK_BOT_TOKEN"],
    ),
    # Databases
    "supabase": ProviderConfig(
        name="supabase",
        display_name="Supabase",
        base_url="https://api.supabase.com/v1",
        auth_type=AuthType.BEARER,
        env_vars=["SUPABASE_API_KEY"],
    ),
    "neon": ProviderConfig(
        name="neon",
        display_name="Neon",
        base_url="https://console.neon.tech/api/v2",
        auth_type=AuthType.BEARER,
        env_vars=["NEON_API_KEY"],
    ),
    "planetscale": ProviderConfig(
        name="planetscale",
        display_name="PlanetScale",
        base_url="https://api.planetscale.com/v1",
        auth_type=AuthType.BEARER,
        env_vars=["PLANETSCALE_TOKEN"],
    ),
    # Monitoring
    "datadog": ProviderConfig(
        name="datadog",
        display_name="Datadog",
        base_url="https://api.datadoghq.com/api/v1",
        auth_type=AuthType.HEADER,
        auth_header="DD-API-KEY",
        auth_prefix="",
        env_vars=["DD_API_KEY", "DATADOG_API_KEY"],
    ),
    "sentry": ProviderConfig(
        name="sentry",
        display_name="Sentry",
        base_url="https://sentry.io/api/0",
        auth_type=AuthType.BEARER,
        env_vars=["SENTRY_AUTH_TOKEN"],
    ),
    # Search
    "algolia": ProviderConfig(
        name="algolia",
        display_name="Algolia",
        base_url="https://api.algolia.com",
        auth_type=AuthType.HEADER,
        auth_header="X-Algolia-API-Key",
        auth_prefix="",
        env_vars=["ALGOLIA_API_KEY"],
    ),
    # Hanzo
    "hanzo": ProviderConfig(
        name="hanzo",
        display_name="Hanzo AI",
        base_url="https://api.hanzo.ai/v1",
        auth_type=AuthType.BEARER,
        env_vars=["HANZO_API_KEY", "HANZO_TOKEN"],
    ),
    # Popular APIs from handmade-openapis
    "notion": ProviderConfig(
        name="notion",
        display_name="Notion",
        base_url="https://api.notion.com/v1",
        auth_type=AuthType.BEARER,
        spec_url="https://raw.githubusercontent.com/janwilmake/handmade-openapis/main/notion.json",
        env_vars=["NOTION_API_KEY", "NOTION_TOKEN"],
        extra_headers={"Notion-Version": "2022-06-28"},
    ),
    "hackernews": ProviderConfig(
        name="hackernews",
        display_name="Hacker News",
        base_url="https://hacker-news.firebaseio.com/v0",
        auth_type=AuthType.BEARER,  # No auth needed but required by system
        spec_url="https://raw.githubusercontent.com/janwilmake/handmade-openapis/main/hackernews.json",
        env_vars=[],
    ),
    "serper": ProviderConfig(
        name="serper",
        display_name="Serper (Google Search)",
        base_url="https://google.serper.dev",
        auth_type=AuthType.HEADER,
        auth_header="X-API-KEY",
        auth_prefix="",
        spec_url="https://raw.githubusercontent.com/janwilmake/handmade-openapis/main/serper.json",
        env_vars=["SERPER_API_KEY"],
    ),
    "jina": ProviderConfig(
        name="jina",
        display_name="Jina Reader",
        base_url="https://r.jina.ai",
        auth_type=AuthType.BEARER,
        spec_url="https://raw.githubusercontent.com/janwilmake/handmade-openapis/main/jina-reader.json",
        env_vars=["JINA_API_KEY"],
    ),
    "upstash-redis": ProviderConfig(
        name="upstash-redis",
        display_name="Upstash Redis",
        base_url="https://global.upstash.io",
        auth_type=AuthType.BEARER,
        spec_url="https://raw.githubusercontent.com/janwilmake/handmade-openapis/main/upstash-redis.json",
        env_vars=["UPSTASH_REDIS_REST_TOKEN"],
    ),
    "devto": ProviderConfig(
        name="devto",
        display_name="DEV.to",
        base_url="https://dev.to/api",
        auth_type=AuthType.HEADER,
        auth_header="api-key",
        auth_prefix="",
        spec_url="https://raw.githubusercontent.com/janwilmake/handmade-openapis/main/devto.json",
        env_vars=["DEV_API_KEY", "DEVTO_API_KEY"],
    ),
}


def get_provider_config(provider: str) -> ProviderConfig | None:
    """Get configuration for a provider.

    Checks built-in configs first, then falls back to APIs.guru.
    """
    # Built-in configs take priority
    if provider in PROVIDER_CONFIGS:
        return PROVIDER_CONFIGS[provider]

    # Check APIs.guru auto-generated configs
    if provider in APIS_GURU_PROVIDERS:
        guru = APIS_GURU_PROVIDERS[provider]
        return ProviderConfig(
            name=provider,
            display_name=guru.get("display_name", provider),
            base_url=guru.get("base_url", ""),
            auth_type=AuthType.BEARER,
            spec_url=guru.get("spec_url"),
            env_vars=guru.get("env_vars", [f"{provider.upper()}_API_KEY"]),
        )

    return None


def get_env_vars(provider: str) -> list[str]:
    """Get environment variable names for a provider."""
    # Check provider config first
    config = PROVIDER_CONFIGS.get(provider)
    if config:
        return config.env_vars

    # Check APIs.guru configs
    guru = APIS_GURU_PROVIDERS.get(provider)
    if guru:
        return guru.get("env_vars", [])

    # Fall back to env mappings
    return ENV_VAR_MAPPINGS.get(provider, [])


def list_providers() -> list[str]:
    """List all known provider names (1100+ providers)."""
    return sorted(
        set(PROVIDER_CONFIGS.keys())
        | set(ENV_VAR_MAPPINGS.keys())
        | set(APIS_GURU_PROVIDERS.keys())
    )


def list_providers_with_specs() -> list[str]:
    """List providers that have OpenAPI spec URLs."""
    providers = []
    for name, config in PROVIDER_CONFIGS.items():
        if config.spec_url:
            providers.append(name)
    for name, guru in APIS_GURU_PROVIDERS.items():
        if guru.get("spec_url") and name not in providers:
            providers.append(name)
    return sorted(providers)
