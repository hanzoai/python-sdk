"""models — the catalog, with no credential at all.

``GET /v1/models`` (operationId ``get_models``): every model the router can
reach, with its owner and its per-token price.

This is the flow that runs before you have a key, and the only one that can. The
document marks four of its 2479 operations ``security: []`` and this is one of
them: the catalog is the same for every caller, so the operation takes no
principal and the generated method sends no ``Authorization`` header. That is
visible in the generated code — ``_get_models_serialize`` carries an empty
``_auth_settings``, where all 2498 other call sites carry ``['bearer']``.

So this doubles as the install check. If it prints a count, the package imports,
the host resolves, and the client speaks the API. If it prints a count when you
expected a refusal, that is not a broken key — this route never looks at one.

The payload is read through the generated ``*_without_preload_content`` variant
because the operation declares no response ``content``: 834 of the document's
operations model no body, so the typed method returns None. It becomes an
ordinary typed call now that the schema has landed, which is what this is.

    python -m examples.models
"""

from hanzoai.cloud import AiApi

from examples.client import BASE_URL, public, run


def main() -> None:
    with public() as api:
        catalogue = AiApi(api).get_models()

    models = catalogue.data or []
    print(f"{BASE_URL} serves {len(models)} models, no credential required")
    for model in models[:10]:
        price = model.pricing.input if model.pricing else None
        rate = f"${price}/Mtok in" if price is not None else "unpriced"
        print(f"  {model.id} · {model.owned_by or 'unowned'} · {rate}")
    if len(models) > 10:
        print(f"  … and {len(models) - 10} more")


if __name__ == "__main__":
    run(main)
