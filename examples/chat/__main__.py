"""chat — one completion.

``POST /v1/chat/completions`` (operationId ``ai_createChatCompletion``). The
route is OpenAI-compatible, so the request and response shapes are the ones you
already know; only the base URL and the key change.

``stream`` is left False on purpose. Streaming is a different transport (SSE)
that the generated client returns as an opaque body, so a streaming example
here would teach the wrong thing.

    python -m examples.chat
"""

from hanzoai.cloud import AiChatCompletionRequest, AiChatMessage, OpenAICompatibleApi

from examples.client import MODEL, client, run


def main() -> None:
    with client() as api:
        completion = OpenAICompatibleApi(api).ai_create_chat_completion(
            AiChatCompletionRequest(
                model=MODEL,
                messages=[AiChatMessage(role="user", content="Say hello in exactly five words.")],
            )
        )

    choices = completion.choices or []
    if not choices:
        raise SystemExit("no choices returned")
    print(choices[0].message.content if choices[0].message else "(empty message)")

    if completion.usage:
        print(f"tokens: {completion.usage.prompt_tokens} in / {completion.usage.completion_tokens} out")


if __name__ == "__main__":
    run(main)
