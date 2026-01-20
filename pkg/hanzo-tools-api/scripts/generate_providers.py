#!/usr/bin/env python3
"""Generate provider configurations from APIs.guru with LLM-optimized descriptions from oapis.org."""

import asyncio
import json
import re
import sys
from pathlib import Path
import urllib.request
from concurrent.futures import ThreadPoolExecutor

# Common env var patterns
ENV_VAR_PATTERNS = {
    'stripe': ['STRIPE_API_KEY', 'STRIPE_SECRET_KEY'],
    'twilio': ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN'],
    'github': ['GITHUB_TOKEN', 'GH_TOKEN'],
    'gitlab': ['GITLAB_TOKEN'],
    'slack': ['SLACK_TOKEN', 'SLACK_BOT_TOKEN'],
    'discord': ['DISCORD_TOKEN', 'DISCORD_BOT_TOKEN'],
    'shopify': ['SHOPIFY_API_KEY', 'SHOPIFY_ACCESS_TOKEN'],
    'hubspot': ['HUBSPOT_API_KEY', 'HUBSPOT_ACCESS_TOKEN'],
    'mailchimp': ['MAILCHIMP_API_KEY'],
    'sendgrid': ['SENDGRID_API_KEY'],
    'mailgun': ['MAILGUN_API_KEY'],
    'contentful': ['CONTENTFUL_ACCESS_TOKEN'],
    'airtable': ['AIRTABLE_API_KEY'],
    'notion': ['NOTION_API_KEY', 'NOTION_TOKEN'],
    'figma': ['FIGMA_TOKEN', 'FIGMA_ACCESS_TOKEN'],
    'asana': ['ASANA_TOKEN', 'ASANA_ACCESS_TOKEN'],
    'trello': ['TRELLO_API_KEY', 'TRELLO_TOKEN'],
    'jira': ['JIRA_TOKEN', 'JIRA_API_TOKEN'],
    'confluence': ['CONFLUENCE_TOKEN'],
    'bitbucket': ['BITBUCKET_TOKEN'],
    'dropbox': ['DROPBOX_ACCESS_TOKEN'],
    'box': ['BOX_ACCESS_TOKEN'],
    'spotify': ['SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET'],
    'youtube': ['YOUTUBE_API_KEY'],
    'twitter': ['TWITTER_API_KEY', 'TWITTER_BEARER_TOKEN'],
    'linkedin': ['LINKEDIN_ACCESS_TOKEN'],
    'facebook': ['FACEBOOK_ACCESS_TOKEN'],
    'instagram': ['INSTAGRAM_ACCESS_TOKEN'],
    'pinterest': ['PINTEREST_ACCESS_TOKEN'],
    'reddit': ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET'],
    'zendesk': ['ZENDESK_API_TOKEN'],
    'freshdesk': ['FRESHDESK_API_KEY'],
    'intercom': ['INTERCOM_ACCESS_TOKEN'],
    'mixpanel': ['MIXPANEL_TOKEN'],
    'segment': ['SEGMENT_WRITE_KEY'],
    'amplitude': ['AMPLITUDE_API_KEY'],
    'plaid': ['PLAID_CLIENT_ID', 'PLAID_SECRET'],
    'square': ['SQUARE_ACCESS_TOKEN'],
    'paypal': ['PAYPAL_CLIENT_ID', 'PAYPAL_CLIENT_SECRET'],
    'braintree': ['BRAINTREE_MERCHANT_ID'],
    'quickbooks': ['QUICKBOOKS_CLIENT_ID'],
    'xero': ['XERO_CLIENT_ID'],
    'salesforce': ['SALESFORCE_ACCESS_TOKEN'],
    'pipedrive': ['PIPEDRIVE_API_TOKEN'],
    'zoho': ['ZOHO_ACCESS_TOKEN'],
    'monday': ['MONDAY_API_KEY'],
    'clickup': ['CLICKUP_API_KEY'],
    'linear': ['LINEAR_API_KEY'],
    'vercel': ['VERCEL_TOKEN'],
    'netlify': ['NETLIFY_AUTH_TOKEN'],
    'heroku': ['HEROKU_API_KEY'],
    'digitalocean': ['DIGITALOCEAN_TOKEN', 'DO_TOKEN'],
    'linode': ['LINODE_TOKEN'],
    'vultr': ['VULTR_API_KEY'],
    'cloudflare': ['CLOUDFLARE_API_TOKEN', 'CF_API_TOKEN'],
    'datadog': ['DD_API_KEY', 'DATADOG_API_KEY'],
    'newrelic': ['NEW_RELIC_API_KEY'],
    'sentry': ['SENTRY_AUTH_TOKEN'],
    'pagerduty': ['PAGERDUTY_API_KEY'],
    'opsgenie': ['OPSGENIE_API_KEY'],
    'splunk': ['SPLUNK_TOKEN'],
    'elasticsearch': ['ELASTIC_API_KEY'],
    'algolia': ['ALGOLIA_API_KEY'],
    'meilisearch': ['MEILISEARCH_API_KEY'],
    'typesense': ['TYPESENSE_API_KEY'],
    'twitch': ['TWITCH_CLIENT_ID', 'TWITCH_CLIENT_SECRET'],
    'ebay': ['EBAY_APP_ID', 'EBAY_DEV_ID'],
    'etsy': ['ETSY_API_KEY'],
    'walmart': ['WALMART_CLIENT_ID'],
    'bestbuy': ['BESTBUY_API_KEY'],
    'yelp': ['YELP_API_KEY'],
    'foursquare': ['FOURSQUARE_API_KEY'],
    'tripadvisor': ['TRIPADVISOR_API_KEY'],
    'airbnb': ['AIRBNB_API_KEY'],
    'uber': ['UBER_ACCESS_TOKEN'],
    'lyft': ['LYFT_ACCESS_TOKEN'],
    'doordash': ['DOORDASH_API_KEY'],
    'postmates': ['POSTMATES_API_KEY'],
    'mapbox': ['MAPBOX_ACCESS_TOKEN'],
    'here': ['HERE_API_KEY'],
    'tomtom': ['TOMTOM_API_KEY'],
    'openweathermap': ['OPENWEATHERMAP_API_KEY'],
    'weatherapi': ['WEATHERAPI_KEY'],
    'newsapi': ['NEWSAPI_KEY'],
    'nytimes': ['NYTIMES_API_KEY'],
    'guardian': ['GUARDIAN_API_KEY'],
    'giphy': ['GIPHY_API_KEY'],
    'unsplash': ['UNSPLASH_ACCESS_KEY'],
    'pexels': ['PEXELS_API_KEY'],
    'cloudinary': ['CLOUDINARY_API_KEY'],
    'imgix': ['IMGIX_API_KEY'],
    'uploadcare': ['UPLOADCARE_PUBLIC_KEY'],
    'filestack': ['FILESTACK_API_KEY'],
    'agora': ['AGORA_APP_ID'],
    'vonage': ['VONAGE_API_KEY', 'NEXMO_API_KEY'],
    'messagebird': ['MESSAGEBIRD_API_KEY'],
    'bandwidth': ['BANDWIDTH_API_TOKEN'],
    'telnyx': ['TELNYX_API_KEY'],
    'apilayer': ['APILAYER_API_KEY'],
    'currencylayer': ['CURRENCYLAYER_API_KEY'],
    'exchangerate': ['EXCHANGERATE_API_KEY'],
    'coinbase': ['COINBASE_API_KEY'],
    'binance': ['BINANCE_API_KEY'],
    'kraken': ['KRAKEN_API_KEY'],
    'alchemy': ['ALCHEMY_API_KEY'],
    'infura': ['INFURA_PROJECT_ID'],
    'moralis': ['MORALIS_API_KEY'],
    'thegraph': ['THEGRAPH_API_KEY'],
    'openai': ['OPENAI_API_KEY'],
    'anthropic': ['ANTHROPIC_API_KEY'],
    'cohere': ['COHERE_API_KEY'],
    'huggingface': ['HF_TOKEN', 'HUGGINGFACE_TOKEN'],
    'replicate': ['REPLICATE_API_TOKEN'],
    'stability': ['STABILITY_API_KEY'],
    'deepl': ['DEEPL_API_KEY'],
    'ably': ['ABLY_API_KEY'],
    'pusher': ['PUSHER_APP_KEY'],
    'pubnub': ['PUBNUB_SUBSCRIBE_KEY'],
    'firebase': ['FIREBASE_API_KEY'],
    'supabase': ['SUPABASE_API_KEY'],
    'mongodb': ['MONGODB_API_KEY'],
    'redis': ['REDIS_API_KEY'],
    'cockroachdb': ['COCKROACHDB_API_KEY'],
    'planetscale': ['PLANETSCALE_TOKEN'],
    'neon': ['NEON_API_KEY'],
    'upstash': ['UPSTASH_API_KEY'],
    'fauna': ['FAUNA_SECRET'],
    'adyen': ['ADYEN_API_KEY'],
    'sportsdata': ['SPORTSDATA_API_KEY'],
    'amadeus': ['AMADEUS_API_KEY', 'AMADEUS_API_SECRET'],
    'nexmo': ['NEXMO_API_KEY', 'NEXMO_API_SECRET'],
    'mastercard': ['MASTERCARD_API_KEY'],
    'hubapi': ['HUBSPOT_API_KEY'],
    'apideck': ['APIDECK_API_KEY'],
    'codat': ['CODAT_API_KEY'],
    'deutschebahn': ['DEUTSCHEBAHN_API_KEY'],
    'rapidapi': ['RAPIDAPI_KEY'],
    'whapi': ['WHAPI_TOKEN'],
    'vtex': ['VTEX_APP_KEY', 'VTEX_APP_TOKEN'],
    'interzoid': ['INTERZOID_API_KEY'],
}

# Skip cloud-specific APIs that need special auth handling
SKIP_PREFIXES = [
    'amazonaws', 'azure', 'googleapis', 'google.',
    'apisetu', 'parliament', 'gov.', 'opto22',
    'windows', 'o365', 'microsofthealth',
]

# Popular APIs with oapis.org LLM-friendly descriptions
# These get priority loading and better descriptions
OAPIS_POPULAR = [
    'github', 'stripe', 'twilio', 'slack', 'notion', 'discord',
    'shopify', 'spotify', 'twitter', 'openai', 'anthropic',
]


def get_env_vars(name: str) -> list[str]:
    """Get env vars for a provider name."""
    name_lower = name.lower()
    for key, vars in ENV_VAR_PATTERNS.items():
        if key in name_lower:
            return vars
    # Generate default pattern
    clean = re.sub(r'[^a-z0-9]', '_', name_lower).upper()
    return [f'{clean}_API_KEY', f'{clean}_TOKEN']


def clean_name(name: str) -> str:
    """Clean API name for use as provider ID."""
    # Remove version suffixes
    name = re.sub(r':\d+.*$', '', name)
    # Replace dots and colons with hyphens
    name = name.replace('.', '-').replace(':', '-')
    # Remove common suffixes
    name = re.sub(r'-com$|-io$|-net$|-org$|-local$', '', name)
    # Clean up
    name = re.sub(r'[^a-z0-9-]', '', name.lower())
    name = re.sub(r'-+', '-', name).strip('-')
    return name


def fetch_oapis_slop(name: str) -> dict | None:
    """Fetch LLM-optimized description from oapis.org/slop/{name}.

    Returns dict with base_url, endpoints_count, description if available.
    """
    try:
        url = f"https://oapis.org/slop/{name}"
        req = urllib.request.Request(url, headers={'User-Agent': 'hanzo-tools-api/0.2'})
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode()

            # Parse the slop format
            result = {}

            # Extract base URL (usually on a line with https://)
            base_match = re.search(r'Base URL:\s*(https?://[^\s]+)', content, re.IGNORECASE)
            if not base_match:
                base_match = re.search(r'\*\*Base URL\*\*:\s*(https?://[^\s]+)', content, re.IGNORECASE)
            if base_match:
                result['base_url'] = base_match.group(1).rstrip('/')

            # Extract endpoint count
            count_match = re.search(r'(\d+)\s+endpoints?', content, re.IGNORECASE)
            if count_match:
                result['endpoints_count'] = int(count_match.group(1))

            # Extract description (first paragraph after title)
            desc_match = re.search(r'^#[^\n]+\n+([^#\n][^\n]+)', content, re.MULTILINE)
            if desc_match:
                result['description'] = desc_match.group(1).strip()[:200]

            return result if result else None
    except Exception:
        return None


def fetch_apis_guru() -> dict:
    """Fetch API list from APIs.guru."""
    url = "https://api.apis.guru/v2/list.json"
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode())


def fetch_oapis_batch(names: list[str], max_workers: int = 10) -> dict[str, dict]:
    """Fetch oapis.org descriptions for multiple APIs concurrently."""
    results = {}

    def fetch_one(name: str) -> tuple[str, dict | None]:
        return name, fetch_oapis_slop(name)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for name, data in executor.map(lambda n: fetch_one(n), names):
            if data:
                results[name] = data

    return results


def main():
    print("Fetching APIs from APIs.guru...", file=sys.stderr)
    data = fetch_apis_guru()
    print(f"Found {len(data)} APIs", file=sys.stderr)

    # Fetch oapis.org LLM descriptions for popular APIs
    print(f"Fetching LLM descriptions from oapis.org for {len(OAPIS_POPULAR)} popular APIs...", file=sys.stderr)
    oapis_data = fetch_oapis_batch(OAPIS_POPULAR)
    print(f"Got {len(oapis_data)} oapis.org descriptions", file=sys.stderr)

    apis = []
    seen_names = set()

    for name, info in data.items():
        # Skip cloud-specific
        skip = False
        for prefix in SKIP_PREFIXES:
            if name.lower().startswith(prefix.lower()):
                skip = True
                break
        if skip:
            continue

        preferred = info.get('preferred', '')
        if not preferred or preferred not in info.get('versions', {}):
            continue

        version_info = info['versions'][preferred]
        spec_url = version_info.get('swaggerUrl', '')
        if not spec_url:
            continue

        api_info = version_info.get('info', {})
        title = api_info.get('title', name)

        clean = clean_name(name)
        if clean in seen_names or len(clean) < 2:
            continue
        seen_names.add(clean)

        # Get base URL from x-origin
        base_url = ''
        if 'x-origin' in api_info:
            x_origin = api_info['x-origin']
            if isinstance(x_origin, list) and x_origin:
                base_url = x_origin[0].get('url', '')

        # Check for oapis.org enhanced data
        oapis_key = None
        for popular in OAPIS_POPULAR:
            if popular in clean:
                oapis_key = popular
                break

        description = api_info.get('description', '')[:200] if api_info.get('description') else ''
        endpoints_count = None

        if oapis_key and oapis_key in oapis_data:
            oapis_info = oapis_data[oapis_key]
            if oapis_info.get('base_url'):
                base_url = oapis_info['base_url']
            if oapis_info.get('description'):
                description = oapis_info['description']
            if oapis_info.get('endpoints_count'):
                endpoints_count = oapis_info['endpoints_count']

        # Clean strings - remove newlines, escape quotes, limit length
        def clean_str(s: str, max_len: int = 150) -> str:
            if not s:
                return ""
            # Replace various whitespace with single space
            s = ' '.join(s.split())
            # Escape backslashes first, then quotes
            s = s.replace('\\', '\\\\').replace('"', '\\"')
            return s[:max_len]

        apis.append({
            'name': clean,
            'title': clean_str(title, 60),
            'description': clean_str(description, 150),
            'spec_url': spec_url,
            'base_url': base_url,
            'env_vars': get_env_vars(clean),
            'endpoints_count': endpoints_count,
        })

    # Sort by name
    apis.sort(key=lambda x: x['name'])

    # Generate Python code
    print('"""Auto-generated provider configurations from APIs.guru + oapis.org.')
    print()
    print(f'Generated {len(apis)} provider configurations.')
    print('Includes LLM-optimized descriptions from oapis.org for popular APIs.')
    print()
    print('Regenerate with: python scripts/generate_providers.py > hanzo_tools/api/apis_guru_providers.py')
    print('"""')
    print()
    print('from typing import Any')
    print()
    print()
    print('# =============================================================================')
    print('# APIs.guru Provider Configurations (with oapis.org enhancements)')
    print('# =============================================================================')
    print()
    print('APIS_GURU_PROVIDERS: dict[str, dict[str, Any]] = {')

    for api in apis:
        env_str = ', '.join(f'"{v}"' for v in api['env_vars'][:2])
        print(f'    "{api["name"]}": {{')
        print(f'        "display_name": "{api["title"]}",')
        if api['description']:
            print(f'        "description": "{api["description"][:150]}",')
        print(f'        "spec_url": "{api["spec_url"]}",')
        if api['base_url']:
            safe_url = api['base_url'].replace('"', '\\"')
            print(f'        "base_url": "{safe_url}",')
        print(f'        "env_vars": [{env_str}],')
        if api['endpoints_count']:
            print(f'        "endpoints_count": {api["endpoints_count"]},')
        print('    },')

    print('}')
    print()
    print()
    print(f'# Total: {len(apis)} providers')

    print(f"\nGenerated {len(apis)} providers", file=sys.stderr)


if __name__ == '__main__':
    main()
