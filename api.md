# HanzoAI

Types:

```python
from Hanzo_AI.types import GetHomeResponse
```

Methods:

- <code title="get /">client.<a href="./src/Hanzo_AI/_client.py">get_home</a>() -> <a href="./src/Hanzo_AI/types/get_home_response.py">object</a></code>

# Models

Types:

```python
from Hanzo_AI.types import ModelListResponse
```

Methods:

- <code title="get /v1/models">client.models.<a href="./src/Hanzo_AI/resources/models.py">list</a>(\*\*<a href="src/Hanzo_AI/types/model_list_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/model_list_response.py">object</a></code>

# OpenAI

Types:

```python
from Hanzo_AI.types import (
    OpenAICreateResponse,
    OpenAIRetrieveResponse,
    OpenAIUpdateResponse,
    OpenAIDeleteResponse,
    OpenAIPatchResponse,
)
```

Methods:

- <code title="post /openai/{endpoint}">client.openai.<a href="./src/Hanzo_AI/resources/openai/openai.py">create</a>(endpoint) -> <a href="./src/Hanzo_AI/types/openai_create_response.py">object</a></code>
- <code title="get /openai/{endpoint}">client.openai.<a href="./src/Hanzo_AI/resources/openai/openai.py">retrieve</a>(endpoint) -> <a href="./src/Hanzo_AI/types/openai_retrieve_response.py">object</a></code>
- <code title="put /openai/{endpoint}">client.openai.<a href="./src/Hanzo_AI/resources/openai/openai.py">update</a>(endpoint) -> <a href="./src/Hanzo_AI/types/openai_update_response.py">object</a></code>
- <code title="delete /openai/{endpoint}">client.openai.<a href="./src/Hanzo_AI/resources/openai/openai.py">delete</a>(endpoint) -> <a href="./src/Hanzo_AI/types/openai_delete_response.py">object</a></code>
- <code title="patch /openai/{endpoint}">client.openai.<a href="./src/Hanzo_AI/resources/openai/openai.py">patch</a>(endpoint) -> <a href="./src/Hanzo_AI/types/openai_patch_response.py">object</a></code>

## Deployments

Types:

```python
from Hanzo_AI.types.openai import DeploymentCompleteResponse, DeploymentEmbedResponse
```

Methods:

- <code title="post /openai/deployments/{model}/completions">client.openai.deployments.<a href="./src/Hanzo_AI/resources/openai/deployments/deployments.py">complete</a>(model) -> <a href="./src/Hanzo_AI/types/openai/deployment_complete_response.py">object</a></code>
- <code title="post /openai/deployments/{model}/embeddings">client.openai.deployments.<a href="./src/Hanzo_AI/resources/openai/deployments/deployments.py">embed</a>(model) -> <a href="./src/Hanzo_AI/types/openai/deployment_embed_response.py">object</a></code>

### Chat

Types:

```python
from Hanzo_AI.types.openai.deployments import ChatCompleteResponse
```

Methods:

- <code title="post /openai/deployments/{model}/chat/completions">client.openai.deployments.chat.<a href="./src/Hanzo_AI/resources/openai/deployments/chat.py">complete</a>(model) -> <a href="./src/Hanzo_AI/types/openai/deployments/chat_complete_response.py">object</a></code>

# Engines

Types:

```python
from Hanzo_AI.types import EngineCompleteResponse, EngineEmbedResponse
```

Methods:

- <code title="post /engines/{model}/completions">client.engines.<a href="./src/Hanzo_AI/resources/engines/engines.py">complete</a>(model) -> <a href="./src/Hanzo_AI/types/engine_complete_response.py">object</a></code>
- <code title="post /engines/{model}/embeddings">client.engines.<a href="./src/Hanzo_AI/resources/engines/engines.py">embed</a>(model) -> <a href="./src/Hanzo_AI/types/engine_embed_response.py">object</a></code>

## Chat

Types:

```python
from Hanzo_AI.types.engines import ChatCompleteResponse
```

Methods:

- <code title="post /engines/{model}/chat/completions">client.engines.chat.<a href="./src/Hanzo_AI/resources/engines/chat.py">complete</a>(model) -> <a href="./src/Hanzo_AI/types/engines/chat_complete_response.py">object</a></code>

# Chat

## Completions

Types:

```python
from Hanzo_AI.types.chat import CompletionCreateResponse
```

Methods:

- <code title="post /v1/chat/completions">client.chat.completions.<a href="./src/Hanzo_AI/resources/chat/completions.py">create</a>(\*\*<a href="src/Hanzo_AI/types/chat/completion_create_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/chat/completion_create_response.py">object</a></code>

# Completions

Types:

```python
from Hanzo_AI.types import CompletionCreateResponse
```

Methods:

- <code title="post /completions">client.completions.<a href="./src/Hanzo_AI/resources/completions.py">create</a>(\*\*<a href="src/Hanzo_AI/types/completion_create_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/completion_create_response.py">object</a></code>

# Embeddings

Types:

```python
from Hanzo_AI.types import EmbeddingCreateResponse
```

Methods:

- <code title="post /embeddings">client.embeddings.<a href="./src/Hanzo_AI/resources/embeddings.py">create</a>(\*\*<a href="src/Hanzo_AI/types/embedding_create_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/embedding_create_response.py">object</a></code>

# Images

## Generations

Types:

```python
from Hanzo_AI.types.images import GenerationCreateResponse
```

Methods:

- <code title="post /v1/images/generations">client.images.generations.<a href="./src/Hanzo_AI/resources/images/generations.py">create</a>() -> <a href="./src/Hanzo_AI/types/images/generation_create_response.py">object</a></code>

# Audio

## Speech

Types:

```python
from Hanzo_AI.types.audio import SpeechCreateResponse
```

Methods:

- <code title="post /v1/audio/speech">client.audio.speech.<a href="./src/Hanzo_AI/resources/audio/speech.py">create</a>() -> <a href="./src/Hanzo_AI/types/audio/speech_create_response.py">object</a></code>

## Transcriptions

Types:

```python
from Hanzo_AI.types.audio import TranscriptionCreateResponse
```

Methods:

- <code title="post /v1/audio/transcriptions">client.audio.transcriptions.<a href="./src/Hanzo_AI/resources/audio/transcriptions.py">create</a>(\*\*<a href="src/Hanzo_AI/types/audio/transcription_create_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/audio/transcription_create_response.py">object</a></code>

# Assistants

Types:

```python
from Hanzo_AI.types import AssistantCreateResponse, AssistantListResponse, AssistantDeleteResponse
```

Methods:

- <code title="post /v1/assistants">client.assistants.<a href="./src/Hanzo_AI/resources/assistants.py">create</a>() -> <a href="./src/Hanzo_AI/types/assistant_create_response.py">object</a></code>
- <code title="get /v1/assistants">client.assistants.<a href="./src/Hanzo_AI/resources/assistants.py">list</a>() -> <a href="./src/Hanzo_AI/types/assistant_list_response.py">object</a></code>
- <code title="delete /v1/assistants/{assistant_id}">client.assistants.<a href="./src/Hanzo_AI/resources/assistants.py">delete</a>(assistant_id) -> <a href="./src/Hanzo_AI/types/assistant_delete_response.py">object</a></code>

# Threads

Types:

```python
from Hanzo_AI.types import ThreadCreateResponse, ThreadRetrieveResponse
```

Methods:

- <code title="post /v1/threads">client.threads.<a href="./src/Hanzo_AI/resources/threads/threads.py">create</a>() -> <a href="./src/Hanzo_AI/types/thread_create_response.py">object</a></code>
- <code title="get /v1/threads/{thread_id}">client.threads.<a href="./src/Hanzo_AI/resources/threads/threads.py">retrieve</a>(thread_id) -> <a href="./src/Hanzo_AI/types/thread_retrieve_response.py">object</a></code>

## Messages

Types:

```python
from Hanzo_AI.types.threads import MessageCreateResponse, MessageListResponse
```

Methods:

- <code title="post /v1/threads/{thread_id}/messages">client.threads.messages.<a href="./src/Hanzo_AI/resources/threads/messages.py">create</a>(thread_id) -> <a href="./src/Hanzo_AI/types/threads/message_create_response.py">object</a></code>
- <code title="get /v1/threads/{thread_id}/messages">client.threads.messages.<a href="./src/Hanzo_AI/resources/threads/messages.py">list</a>(thread_id) -> <a href="./src/Hanzo_AI/types/threads/message_list_response.py">object</a></code>

## Runs

Types:

```python
from Hanzo_AI.types.threads import RunCreateResponse
```

Methods:

- <code title="post /v1/threads/{thread_id}/runs">client.threads.runs.<a href="./src/Hanzo_AI/resources/threads/runs.py">create</a>(thread_id) -> <a href="./src/Hanzo_AI/types/threads/run_create_response.py">object</a></code>

# Moderations

Types:

```python
from Hanzo_AI.types import ModerationCreateResponse
```

Methods:

- <code title="post /v1/moderations">client.moderations.<a href="./src/Hanzo_AI/resources/moderations.py">create</a>() -> <a href="./src/Hanzo_AI/types/moderation_create_response.py">object</a></code>

# Utils

Types:

```python
from Hanzo_AI.types import (
    UtilGetSupportedOpenAIParamsResponse,
    UtilTokenCounterResponse,
    UtilTransformRequestResponse,
)
```

Methods:

- <code title="get /utils/supported_openai_params">client.utils.<a href="./src/Hanzo_AI/resources/utils.py">get_supported_openai_params</a>(\*\*<a href="src/Hanzo_AI/types/util_get_supported_openai_params_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/util_get_supported_openai_params_response.py">object</a></code>
- <code title="post /utils/token_counter">client.utils.<a href="./src/Hanzo_AI/resources/utils.py">token_counter</a>(\*\*<a href="src/Hanzo_AI/types/util_token_counter_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/util_token_counter_response.py">UtilTokenCounterResponse</a></code>
- <code title="post /utils/transform_request">client.utils.<a href="./src/Hanzo_AI/resources/utils.py">transform_request</a>(\*\*<a href="src/Hanzo_AI/types/util_transform_request_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/util_transform_request_response.py">UtilTransformRequestResponse</a></code>

# Model

Types:

```python
from Hanzo_AI.types import (
    ConfigurableClientsideParamsCustomAuth,
    ModelInfo,
    ModelCreateResponse,
    ModelDeleteResponse,
)
```

Methods:

- <code title="post /model/new">client.model.<a href="./src/Hanzo_AI/resources/model/model.py">create</a>(\*\*<a href="src/Hanzo_AI/types/model_create_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/model_create_response.py">object</a></code>
- <code title="post /model/delete">client.model.<a href="./src/Hanzo_AI/resources/model/model.py">delete</a>(\*\*<a href="src/Hanzo_AI/types/model_delete_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/model_delete_response.py">object</a></code>

## Info

Types:

```python
from Hanzo_AI.types.model import InfoListResponse
```

Methods:

- <code title="get /model/info">client.model.info.<a href="./src/Hanzo_AI/resources/model/info.py">list</a>(\*\*<a href="src/Hanzo_AI/types/model/info_list_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/model/info_list_response.py">object</a></code>

## Update

Types:

```python
from Hanzo_AI.types.model import UpdateDeployment, UpdateFullResponse, UpdatePartialResponse
```

Methods:

- <code title="post /model/update">client.model.update.<a href="./src/Hanzo_AI/resources/model/update.py">full</a>(\*\*<a href="src/Hanzo_AI/types/model/update_full_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/model/update_full_response.py">object</a></code>
- <code title="patch /model/{model_id}/update">client.model.update.<a href="./src/Hanzo_AI/resources/model/update.py">partial</a>(model_id, \*\*<a href="src/Hanzo_AI/types/model/update_partial_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/model/update_partial_response.py">object</a></code>

# ModelGroup

Types:

```python
from Hanzo_AI.types import ModelGroupRetrieveInfoResponse
```

Methods:

- <code title="get /model_group/info">client.model_group.<a href="./src/Hanzo_AI/resources/model_group.py">retrieve_info</a>(\*\*<a href="src/Hanzo_AI/types/model_group_retrieve_info_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/model_group_retrieve_info_response.py">object</a></code>

# Routes

Types:

```python
from Hanzo_AI.types import RouteListResponse
```

Methods:

- <code title="get /routes">client.routes.<a href="./src/Hanzo_AI/resources/routes.py">list</a>() -> <a href="./src/Hanzo_AI/types/route_list_response.py">object</a></code>

# Responses

Types:

```python
from Hanzo_AI.types import ResponseCreateResponse, ResponseRetrieveResponse, ResponseDeleteResponse
```

Methods:

- <code title="post /v1/responses">client.responses.<a href="./src/Hanzo_AI/resources/responses/responses.py">create</a>() -> <a href="./src/Hanzo_AI/types/response_create_response.py">object</a></code>
- <code title="get /v1/responses/{response_id}">client.responses.<a href="./src/Hanzo_AI/resources/responses/responses.py">retrieve</a>(response_id) -> <a href="./src/Hanzo_AI/types/response_retrieve_response.py">object</a></code>
- <code title="delete /v1/responses/{response_id}">client.responses.<a href="./src/Hanzo_AI/resources/responses/responses.py">delete</a>(response_id) -> <a href="./src/Hanzo_AI/types/response_delete_response.py">object</a></code>

## InputItems

Types:

```python
from Hanzo_AI.types.responses import InputItemListResponse
```

Methods:

- <code title="get /v1/responses/{response_id}/input_items">client.responses.input_items.<a href="./src/Hanzo_AI/resources/responses/input_items.py">list</a>(response_id) -> <a href="./src/Hanzo_AI/types/responses/input_item_list_response.py">object</a></code>

# Batches

Types:

```python
from Hanzo_AI.types import (
    BatchCreateResponse,
    BatchRetrieveResponse,
    BatchListResponse,
    BatchCancelWithProviderResponse,
    BatchCreateWithProviderResponse,
    BatchListWithProviderResponse,
    BatchRetrieveWithProviderResponse,
)
```

Methods:

- <code title="post /v1/batches">client.batches.<a href="./src/Hanzo_AI/resources/batches/batches.py">create</a>(\*\*<a href="src/Hanzo_AI/types/batch_create_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/batch_create_response.py">object</a></code>
- <code title="get /v1/batches/{batch_id}">client.batches.<a href="./src/Hanzo_AI/resources/batches/batches.py">retrieve</a>(batch_id, \*\*<a href="src/Hanzo_AI/types/batch_retrieve_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/batch_retrieve_response.py">object</a></code>
- <code title="get /v1/batches">client.batches.<a href="./src/Hanzo_AI/resources/batches/batches.py">list</a>(\*\*<a href="src/Hanzo_AI/types/batch_list_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/batch_list_response.py">object</a></code>
- <code title="post /{provider}/v1/batches/{batch_id}/cancel">client.batches.<a href="./src/Hanzo_AI/resources/batches/batches.py">cancel_with_provider</a>(batch_id, \*, provider) -> <a href="./src/Hanzo_AI/types/batch_cancel_with_provider_response.py">object</a></code>
- <code title="post /{provider}/v1/batches">client.batches.<a href="./src/Hanzo_AI/resources/batches/batches.py">create_with_provider</a>(provider) -> <a href="./src/Hanzo_AI/types/batch_create_with_provider_response.py">object</a></code>
- <code title="get /{provider}/v1/batches">client.batches.<a href="./src/Hanzo_AI/resources/batches/batches.py">list_with_provider</a>(provider, \*\*<a href="src/Hanzo_AI/types/batch_list_with_provider_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/batch_list_with_provider_response.py">object</a></code>
- <code title="get /{provider}/v1/batches/{batch_id}">client.batches.<a href="./src/Hanzo_AI/resources/batches/batches.py">retrieve_with_provider</a>(batch_id, \*, provider) -> <a href="./src/Hanzo_AI/types/batch_retrieve_with_provider_response.py">object</a></code>

## Cancel

Types:

```python
from Hanzo_AI.types.batches import CancelCancelResponse
```

Methods:

- <code title="post /batches/{batch_id}/cancel">client.batches.cancel.<a href="./src/Hanzo_AI/resources/batches/cancel.py">cancel</a>(batch_id, \*\*<a href="src/Hanzo_AI/types/batches/cancel_cancel_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/batches/cancel_cancel_response.py">object</a></code>

# Rerank

Types:

```python
from Hanzo_AI.types import RerankCreateResponse, RerankCreateV1Response, RerankCreateV2Response
```

Methods:

- <code title="post /rerank">client.rerank.<a href="./src/Hanzo_AI/resources/rerank.py">create</a>() -> <a href="./src/Hanzo_AI/types/rerank_create_response.py">object</a></code>
- <code title="post /v1/rerank">client.rerank.<a href="./src/Hanzo_AI/resources/rerank.py">create_v1</a>() -> <a href="./src/Hanzo_AI/types/rerank_create_v1_response.py">object</a></code>
- <code title="post /v2/rerank">client.rerank.<a href="./src/Hanzo_AI/resources/rerank.py">create_v2</a>() -> <a href="./src/Hanzo_AI/types/rerank_create_v2_response.py">object</a></code>

# FineTuning

## Jobs

Types:

```python
from Hanzo_AI.types.fine_tuning import (
    LiteLlmFineTuningJobCreate,
    JobCreateResponse,
    JobRetrieveResponse,
    JobListResponse,
)
```

Methods:

- <code title="post /v1/fine_tuning/jobs">client.fine_tuning.jobs.<a href="./src/Hanzo_AI/resources/fine_tuning/jobs/jobs.py">create</a>(\*\*<a href="src/Hanzo_AI/types/fine_tuning/job_create_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/fine_tuning/job_create_response.py">object</a></code>
- <code title="get /v1/fine_tuning/jobs/{fine_tuning_job_id}">client.fine_tuning.jobs.<a href="./src/Hanzo_AI/resources/fine_tuning/jobs/jobs.py">retrieve</a>(fine_tuning_job_id, \*\*<a href="src/Hanzo_AI/types/fine_tuning/job_retrieve_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/fine_tuning/job_retrieve_response.py">object</a></code>
- <code title="get /v1/fine_tuning/jobs">client.fine_tuning.jobs.<a href="./src/Hanzo_AI/resources/fine_tuning/jobs/jobs.py">list</a>(\*\*<a href="src/Hanzo_AI/types/fine_tuning/job_list_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/fine_tuning/job_list_response.py">object</a></code>

### Cancel

Types:

```python
from Hanzo_AI.types.fine_tuning.jobs import CancelCreateResponse
```

Methods:

- <code title="post /v1/fine_tuning/jobs/{fine_tuning_job_id}/cancel">client.fine_tuning.jobs.cancel.<a href="./src/Hanzo_AI/resources/fine_tuning/jobs/cancel.py">create</a>(fine_tuning_job_id) -> <a href="./src/Hanzo_AI/types/fine_tuning/jobs/cancel_create_response.py">object</a></code>

# Credentials

Types:

```python
from Hanzo_AI.types import (
    CredentialItem,
    CredentialCreateResponse,
    CredentialRetrieveResponse,
    CredentialUpdateResponse,
    CredentialListResponse,
    CredentialDeleteResponse,
)
```

Methods:

- <code title="post /credentials">client.credentials.<a href="./src/Hanzo_AI/resources/credentials.py">create</a>(\*\*<a href="src/Hanzo_AI/types/credential_create_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/credential_create_response.py">object</a></code>
- <code title="get /credentials/{credential_name}">client.credentials.<a href="./src/Hanzo_AI/resources/credentials.py">retrieve</a>(credential_name) -> <a href="./src/Hanzo_AI/types/credential_retrieve_response.py">object</a></code>
- <code title="put /credentials/{credential_name}">client.credentials.<a href="./src/Hanzo_AI/resources/credentials.py">update</a>(path_credential_name, \*\*<a href="src/Hanzo_AI/types/credential_update_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/credential_update_response.py">object</a></code>
- <code title="get /credentials">client.credentials.<a href="./src/Hanzo_AI/resources/credentials.py">list</a>() -> <a href="./src/Hanzo_AI/types/credential_list_response.py">object</a></code>
- <code title="delete /credentials/{credential_name}">client.credentials.<a href="./src/Hanzo_AI/resources/credentials.py">delete</a>(credential_name) -> <a href="./src/Hanzo_AI/types/credential_delete_response.py">object</a></code>

# VertexAI

Types:

```python
from Hanzo_AI.types import (
    VertexAICreateResponse,
    VertexAIRetrieveResponse,
    VertexAIUpdateResponse,
    VertexAIDeleteResponse,
    VertexAIPatchResponse,
)
```

Methods:

- <code title="post /vertex_ai/{endpoint}">client.vertex_ai.<a href="./src/Hanzo_AI/resources/vertex_ai.py">create</a>(endpoint) -> <a href="./src/Hanzo_AI/types/vertex_ai_create_response.py">object</a></code>
- <code title="get /vertex_ai/{endpoint}">client.vertex_ai.<a href="./src/Hanzo_AI/resources/vertex_ai.py">retrieve</a>(endpoint) -> <a href="./src/Hanzo_AI/types/vertex_ai_retrieve_response.py">object</a></code>
- <code title="put /vertex_ai/{endpoint}">client.vertex_ai.<a href="./src/Hanzo_AI/resources/vertex_ai.py">update</a>(endpoint) -> <a href="./src/Hanzo_AI/types/vertex_ai_update_response.py">object</a></code>
- <code title="delete /vertex_ai/{endpoint}">client.vertex_ai.<a href="./src/Hanzo_AI/resources/vertex_ai.py">delete</a>(endpoint) -> <a href="./src/Hanzo_AI/types/vertex_ai_delete_response.py">object</a></code>
- <code title="patch /vertex_ai/{endpoint}">client.vertex_ai.<a href="./src/Hanzo_AI/resources/vertex_ai.py">patch</a>(endpoint) -> <a href="./src/Hanzo_AI/types/vertex_ai_patch_response.py">object</a></code>

# Gemini

Types:

```python
from Hanzo_AI.types import (
    GeminiCreateResponse,
    GeminiRetrieveResponse,
    GeminiUpdateResponse,
    GeminiDeleteResponse,
    GeminiPatchResponse,
)
```

Methods:

- <code title="post /gemini/{endpoint}">client.gemini.<a href="./src/Hanzo_AI/resources/gemini.py">create</a>(endpoint) -> <a href="./src/Hanzo_AI/types/gemini_create_response.py">object</a></code>
- <code title="get /gemini/{endpoint}">client.gemini.<a href="./src/Hanzo_AI/resources/gemini.py">retrieve</a>(endpoint) -> <a href="./src/Hanzo_AI/types/gemini_retrieve_response.py">object</a></code>
- <code title="put /gemini/{endpoint}">client.gemini.<a href="./src/Hanzo_AI/resources/gemini.py">update</a>(endpoint) -> <a href="./src/Hanzo_AI/types/gemini_update_response.py">object</a></code>
- <code title="delete /gemini/{endpoint}">client.gemini.<a href="./src/Hanzo_AI/resources/gemini.py">delete</a>(endpoint) -> <a href="./src/Hanzo_AI/types/gemini_delete_response.py">object</a></code>
- <code title="patch /gemini/{endpoint}">client.gemini.<a href="./src/Hanzo_AI/resources/gemini.py">patch</a>(endpoint) -> <a href="./src/Hanzo_AI/types/gemini_patch_response.py">object</a></code>

# Cohere

Types:

```python
from Hanzo_AI.types import (
    CohereCreateResponse,
    CohereRetrieveResponse,
    CohereUpdateResponse,
    CohereDeleteResponse,
    CohereModifyResponse,
)
```

Methods:

- <code title="post /cohere/{endpoint}">client.cohere.<a href="./src/Hanzo_AI/resources/cohere.py">create</a>(endpoint) -> <a href="./src/Hanzo_AI/types/cohere_create_response.py">object</a></code>
- <code title="get /cohere/{endpoint}">client.cohere.<a href="./src/Hanzo_AI/resources/cohere.py">retrieve</a>(endpoint) -> <a href="./src/Hanzo_AI/types/cohere_retrieve_response.py">object</a></code>
- <code title="put /cohere/{endpoint}">client.cohere.<a href="./src/Hanzo_AI/resources/cohere.py">update</a>(endpoint) -> <a href="./src/Hanzo_AI/types/cohere_update_response.py">object</a></code>
- <code title="delete /cohere/{endpoint}">client.cohere.<a href="./src/Hanzo_AI/resources/cohere.py">delete</a>(endpoint) -> <a href="./src/Hanzo_AI/types/cohere_delete_response.py">object</a></code>
- <code title="patch /cohere/{endpoint}">client.cohere.<a href="./src/Hanzo_AI/resources/cohere.py">modify</a>(endpoint) -> <a href="./src/Hanzo_AI/types/cohere_modify_response.py">object</a></code>

# Anthropic

Types:

```python
from Hanzo_AI.types import (
    AnthropicCreateResponse,
    AnthropicRetrieveResponse,
    AnthropicUpdateResponse,
    AnthropicDeleteResponse,
    AnthropicModifyResponse,
)
```

Methods:

- <code title="post /anthropic/{endpoint}">client.anthropic.<a href="./src/Hanzo_AI/resources/anthropic.py">create</a>(endpoint) -> <a href="./src/Hanzo_AI/types/anthropic_create_response.py">object</a></code>
- <code title="get /anthropic/{endpoint}">client.anthropic.<a href="./src/Hanzo_AI/resources/anthropic.py">retrieve</a>(endpoint) -> <a href="./src/Hanzo_AI/types/anthropic_retrieve_response.py">object</a></code>
- <code title="put /anthropic/{endpoint}">client.anthropic.<a href="./src/Hanzo_AI/resources/anthropic.py">update</a>(endpoint) -> <a href="./src/Hanzo_AI/types/anthropic_update_response.py">object</a></code>
- <code title="delete /anthropic/{endpoint}">client.anthropic.<a href="./src/Hanzo_AI/resources/anthropic.py">delete</a>(endpoint) -> <a href="./src/Hanzo_AI/types/anthropic_delete_response.py">object</a></code>
- <code title="patch /anthropic/{endpoint}">client.anthropic.<a href="./src/Hanzo_AI/resources/anthropic.py">modify</a>(endpoint) -> <a href="./src/Hanzo_AI/types/anthropic_modify_response.py">object</a></code>

# Bedrock

Types:

```python
from Hanzo_AI.types import (
    BedrockCreateResponse,
    BedrockRetrieveResponse,
    BedrockUpdateResponse,
    BedrockDeleteResponse,
    BedrockPatchResponse,
)
```

Methods:

- <code title="post /bedrock/{endpoint}">client.bedrock.<a href="./src/Hanzo_AI/resources/bedrock.py">create</a>(endpoint) -> <a href="./src/Hanzo_AI/types/bedrock_create_response.py">object</a></code>
- <code title="get /bedrock/{endpoint}">client.bedrock.<a href="./src/Hanzo_AI/resources/bedrock.py">retrieve</a>(endpoint) -> <a href="./src/Hanzo_AI/types/bedrock_retrieve_response.py">object</a></code>
- <code title="put /bedrock/{endpoint}">client.bedrock.<a href="./src/Hanzo_AI/resources/bedrock.py">update</a>(endpoint) -> <a href="./src/Hanzo_AI/types/bedrock_update_response.py">object</a></code>
- <code title="delete /bedrock/{endpoint}">client.bedrock.<a href="./src/Hanzo_AI/resources/bedrock.py">delete</a>(endpoint) -> <a href="./src/Hanzo_AI/types/bedrock_delete_response.py">object</a></code>
- <code title="patch /bedrock/{endpoint}">client.bedrock.<a href="./src/Hanzo_AI/resources/bedrock.py">patch</a>(endpoint) -> <a href="./src/Hanzo_AI/types/bedrock_patch_response.py">object</a></code>

# EuAssemblyai

Types:

```python
from Hanzo_AI.types import (
    EuAssemblyaiCreateResponse,
    EuAssemblyaiRetrieveResponse,
    EuAssemblyaiUpdateResponse,
    EuAssemblyaiDeleteResponse,
    EuAssemblyaiPatchResponse,
)
```

Methods:

- <code title="post /eu.assemblyai/{endpoint}">client.eu_assemblyai.<a href="./src/Hanzo_AI/resources/eu_assemblyai.py">create</a>(endpoint) -> <a href="./src/Hanzo_AI/types/eu_assemblyai_create_response.py">object</a></code>
- <code title="get /eu.assemblyai/{endpoint}">client.eu_assemblyai.<a href="./src/Hanzo_AI/resources/eu_assemblyai.py">retrieve</a>(endpoint) -> <a href="./src/Hanzo_AI/types/eu_assemblyai_retrieve_response.py">object</a></code>
- <code title="put /eu.assemblyai/{endpoint}">client.eu_assemblyai.<a href="./src/Hanzo_AI/resources/eu_assemblyai.py">update</a>(endpoint) -> <a href="./src/Hanzo_AI/types/eu_assemblyai_update_response.py">object</a></code>
- <code title="delete /eu.assemblyai/{endpoint}">client.eu_assemblyai.<a href="./src/Hanzo_AI/resources/eu_assemblyai.py">delete</a>(endpoint) -> <a href="./src/Hanzo_AI/types/eu_assemblyai_delete_response.py">object</a></code>
- <code title="patch /eu.assemblyai/{endpoint}">client.eu_assemblyai.<a href="./src/Hanzo_AI/resources/eu_assemblyai.py">patch</a>(endpoint) -> <a href="./src/Hanzo_AI/types/eu_assemblyai_patch_response.py">object</a></code>

# Assemblyai

Types:

```python
from Hanzo_AI.types import (
    AssemblyaiCreateResponse,
    AssemblyaiRetrieveResponse,
    AssemblyaiUpdateResponse,
    AssemblyaiDeleteResponse,
    AssemblyaiPatchResponse,
)
```

Methods:

- <code title="post /assemblyai/{endpoint}">client.assemblyai.<a href="./src/Hanzo_AI/resources/assemblyai.py">create</a>(endpoint) -> <a href="./src/Hanzo_AI/types/assemblyai_create_response.py">object</a></code>
- <code title="get /assemblyai/{endpoint}">client.assemblyai.<a href="./src/Hanzo_AI/resources/assemblyai.py">retrieve</a>(endpoint) -> <a href="./src/Hanzo_AI/types/assemblyai_retrieve_response.py">object</a></code>
- <code title="put /assemblyai/{endpoint}">client.assemblyai.<a href="./src/Hanzo_AI/resources/assemblyai.py">update</a>(endpoint) -> <a href="./src/Hanzo_AI/types/assemblyai_update_response.py">object</a></code>
- <code title="delete /assemblyai/{endpoint}">client.assemblyai.<a href="./src/Hanzo_AI/resources/assemblyai.py">delete</a>(endpoint) -> <a href="./src/Hanzo_AI/types/assemblyai_delete_response.py">object</a></code>
- <code title="patch /assemblyai/{endpoint}">client.assemblyai.<a href="./src/Hanzo_AI/resources/assemblyai.py">patch</a>(endpoint) -> <a href="./src/Hanzo_AI/types/assemblyai_patch_response.py">object</a></code>

# Azure

Types:

```python
from Hanzo_AI.types import (
    AzureCreateResponse,
    AzureUpdateResponse,
    AzureDeleteResponse,
    AzureCallResponse,
    AzurePatchResponse,
)
```

Methods:

- <code title="post /azure/{endpoint}">client.azure.<a href="./src/Hanzo_AI/resources/azure.py">create</a>(endpoint) -> <a href="./src/Hanzo_AI/types/azure_create_response.py">object</a></code>
- <code title="put /azure/{endpoint}">client.azure.<a href="./src/Hanzo_AI/resources/azure.py">update</a>(endpoint) -> <a href="./src/Hanzo_AI/types/azure_update_response.py">object</a></code>
- <code title="delete /azure/{endpoint}">client.azure.<a href="./src/Hanzo_AI/resources/azure.py">delete</a>(endpoint) -> <a href="./src/Hanzo_AI/types/azure_delete_response.py">object</a></code>
- <code title="get /azure/{endpoint}">client.azure.<a href="./src/Hanzo_AI/resources/azure.py">call</a>(endpoint) -> <a href="./src/Hanzo_AI/types/azure_call_response.py">object</a></code>
- <code title="patch /azure/{endpoint}">client.azure.<a href="./src/Hanzo_AI/resources/azure.py">patch</a>(endpoint) -> <a href="./src/Hanzo_AI/types/azure_patch_response.py">object</a></code>

# Langfuse

Types:

```python
from Hanzo_AI.types import (
    LangfuseCreateResponse,
    LangfuseRetrieveResponse,
    LangfuseUpdateResponse,
    LangfuseDeleteResponse,
    LangfusePatchResponse,
)
```

Methods:

- <code title="post /langfuse/{endpoint}">client.langfuse.<a href="./src/Hanzo_AI/resources/langfuse.py">create</a>(endpoint) -> <a href="./src/Hanzo_AI/types/langfuse_create_response.py">object</a></code>
- <code title="get /langfuse/{endpoint}">client.langfuse.<a href="./src/Hanzo_AI/resources/langfuse.py">retrieve</a>(endpoint) -> <a href="./src/Hanzo_AI/types/langfuse_retrieve_response.py">object</a></code>
- <code title="put /langfuse/{endpoint}">client.langfuse.<a href="./src/Hanzo_AI/resources/langfuse.py">update</a>(endpoint) -> <a href="./src/Hanzo_AI/types/langfuse_update_response.py">object</a></code>
- <code title="delete /langfuse/{endpoint}">client.langfuse.<a href="./src/Hanzo_AI/resources/langfuse.py">delete</a>(endpoint) -> <a href="./src/Hanzo_AI/types/langfuse_delete_response.py">object</a></code>
- <code title="patch /langfuse/{endpoint}">client.langfuse.<a href="./src/Hanzo_AI/resources/langfuse.py">patch</a>(endpoint) -> <a href="./src/Hanzo_AI/types/langfuse_patch_response.py">object</a></code>

# Config

## PassThroughEndpoint

Types:

```python
from Hanzo_AI.types.config import (
    PassThroughEndpointResponse,
    PassThroughGenericEndpoint,
    PassThroughEndpointCreateResponse,
    PassThroughEndpointUpdateResponse,
)
```

Methods:

- <code title="post /config/pass_through_endpoint">client.config.pass_through_endpoint.<a href="./src/Hanzo_AI/resources/config/pass_through_endpoint.py">create</a>(\*\*<a href="src/Hanzo_AI/types/config/pass_through_endpoint_create_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/config/pass_through_endpoint_create_response.py">object</a></code>
- <code title="post /config/pass_through_endpoint/{endpoint_id}">client.config.pass_through_endpoint.<a href="./src/Hanzo_AI/resources/config/pass_through_endpoint.py">update</a>(endpoint_id) -> <a href="./src/Hanzo_AI/types/config/pass_through_endpoint_update_response.py">object</a></code>
- <code title="get /config/pass_through_endpoint">client.config.pass_through_endpoint.<a href="./src/Hanzo_AI/resources/config/pass_through_endpoint.py">list</a>(\*\*<a href="src/Hanzo_AI/types/config/pass_through_endpoint_list_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/config/pass_through_endpoint_response.py">PassThroughEndpointResponse</a></code>
- <code title="delete /config/pass_through_endpoint">client.config.pass_through_endpoint.<a href="./src/Hanzo_AI/resources/config/pass_through_endpoint.py">delete</a>(\*\*<a href="src/Hanzo_AI/types/config/pass_through_endpoint_delete_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/config/pass_through_endpoint_response.py">PassThroughEndpointResponse</a></code>

# Test

Types:

```python
from Hanzo_AI.types import TestPingResponse
```

Methods:

- <code title="get /test">client.test.<a href="./src/Hanzo_AI/resources/test.py">ping</a>() -> <a href="./src/Hanzo_AI/types/test_ping_response.py">object</a></code>

# Health

Types:

```python
from Hanzo_AI.types import (
    HealthCheckAllResponse,
    HealthCheckLivelinessResponse,
    HealthCheckLivenessResponse,
    HealthCheckReadinessResponse,
    HealthCheckServicesResponse,
)
```

Methods:

- <code title="get /health">client.health.<a href="./src/Hanzo_AI/resources/health.py">check_all</a>(\*\*<a href="src/Hanzo_AI/types/health_check_all_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/health_check_all_response.py">object</a></code>
- <code title="get /health/liveliness">client.health.<a href="./src/Hanzo_AI/resources/health.py">check_liveliness</a>() -> <a href="./src/Hanzo_AI/types/health_check_liveliness_response.py">object</a></code>
- <code title="get /health/liveness">client.health.<a href="./src/Hanzo_AI/resources/health.py">check_liveness</a>() -> <a href="./src/Hanzo_AI/types/health_check_liveness_response.py">object</a></code>
- <code title="get /health/readiness">client.health.<a href="./src/Hanzo_AI/resources/health.py">check_readiness</a>() -> <a href="./src/Hanzo_AI/types/health_check_readiness_response.py">object</a></code>
- <code title="get /health/services">client.health.<a href="./src/Hanzo_AI/resources/health.py">check_services</a>(\*\*<a href="src/Hanzo_AI/types/health_check_services_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/health_check_services_response.py">object</a></code>

# Active

Types:

```python
from Hanzo_AI.types import ActiveListCallbacksResponse
```

Methods:

- <code title="get /active/callbacks">client.active.<a href="./src/Hanzo_AI/resources/active.py">list_callbacks</a>() -> <a href="./src/Hanzo_AI/types/active_list_callbacks_response.py">object</a></code>

# Settings

Types:

```python
from Hanzo_AI.types import SettingRetrieveResponse
```

Methods:

- <code title="get /settings">client.settings.<a href="./src/Hanzo_AI/resources/settings.py">retrieve</a>() -> <a href="./src/Hanzo_AI/types/setting_retrieve_response.py">object</a></code>

# Key

Types:

```python
from Hanzo_AI.types import (
    BlockKeyRequest,
    GenerateKeyResponse,
    KeyUpdateResponse,
    KeyListResponse,
    KeyDeleteResponse,
    KeyBlockResponse,
    KeyCheckHealthResponse,
    KeyRetrieveInfoResponse,
    KeyUnblockResponse,
)
```

Methods:

- <code title="post /key/update">client.key.<a href="./src/Hanzo_AI/resources/key/key.py">update</a>(\*\*<a href="src/Hanzo_AI/types/key_update_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/key_update_response.py">object</a></code>
- <code title="get /key/list">client.key.<a href="./src/Hanzo_AI/resources/key/key.py">list</a>(\*\*<a href="src/Hanzo_AI/types/key_list_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/key_list_response.py">KeyListResponse</a></code>
- <code title="post /key/delete">client.key.<a href="./src/Hanzo_AI/resources/key/key.py">delete</a>(\*\*<a href="src/Hanzo_AI/types/key_delete_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/key_delete_response.py">object</a></code>
- <code title="post /key/block">client.key.<a href="./src/Hanzo_AI/resources/key/key.py">block</a>(\*\*<a href="src/Hanzo_AI/types/key_block_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/key_block_response.py">Optional[KeyBlockResponse]</a></code>
- <code title="post /key/health">client.key.<a href="./src/Hanzo_AI/resources/key/key.py">check_health</a>() -> <a href="./src/Hanzo_AI/types/key_check_health_response.py">KeyCheckHealthResponse</a></code>
- <code title="post /key/generate">client.key.<a href="./src/Hanzo_AI/resources/key/key.py">generate</a>(\*\*<a href="src/Hanzo_AI/types/key_generate_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/generate_key_response.py">GenerateKeyResponse</a></code>
- <code title="post /key/{key}/regenerate">client.key.<a href="./src/Hanzo_AI/resources/key/key.py">regenerate_by_key</a>(path_key, \*\*<a href="src/Hanzo_AI/types/key_regenerate_by_key_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/generate_key_response.py">Optional[GenerateKeyResponse]</a></code>
- <code title="get /key/info">client.key.<a href="./src/Hanzo_AI/resources/key/key.py">retrieve_info</a>(\*\*<a href="src/Hanzo_AI/types/key_retrieve_info_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/key_retrieve_info_response.py">object</a></code>
- <code title="post /key/unblock">client.key.<a href="./src/Hanzo_AI/resources/key/key.py">unblock</a>(\*\*<a href="src/Hanzo_AI/types/key_unblock_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/key_unblock_response.py">object</a></code>

## Regenerate

Types:

```python
from Hanzo_AI.types.key import RegenerateKeyRequest
```

# User

Types:

```python
from Hanzo_AI.types import (
    UserCreateResponse,
    UserUpdateResponse,
    UserListResponse,
    UserDeleteResponse,
    UserRetrieveInfoResponse,
)
```

Methods:

- <code title="post /user/new">client.user.<a href="./src/Hanzo_AI/resources/user.py">create</a>(\*\*<a href="src/Hanzo_AI/types/user_create_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/user_create_response.py">UserCreateResponse</a></code>
- <code title="post /user/update">client.user.<a href="./src/Hanzo_AI/resources/user.py">update</a>(\*\*<a href="src/Hanzo_AI/types/user_update_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/user_update_response.py">object</a></code>
- <code title="get /user/get_users">client.user.<a href="./src/Hanzo_AI/resources/user.py">list</a>(\*\*<a href="src/Hanzo_AI/types/user_list_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/user_list_response.py">object</a></code>
- <code title="post /user/delete">client.user.<a href="./src/Hanzo_AI/resources/user.py">delete</a>(\*\*<a href="src/Hanzo_AI/types/user_delete_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/user_delete_response.py">object</a></code>
- <code title="get /user/info">client.user.<a href="./src/Hanzo_AI/resources/user.py">retrieve_info</a>(\*\*<a href="src/Hanzo_AI/types/user_retrieve_info_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/user_retrieve_info_response.py">object</a></code>

# Team

Types:

```python
from Hanzo_AI.types import (
    BlockTeamRequest,
    LiteLlmModelTable,
    LiteLlmTeamTable,
    LiteLlmUserTable,
    Member,
    TeamUpdateResponse,
    TeamListResponse,
    TeamDeleteResponse,
    TeamAddMemberResponse,
    TeamBlockResponse,
    TeamDisableLoggingResponse,
    TeamListAvailableResponse,
    TeamRemoveMemberResponse,
    TeamRetrieveInfoResponse,
    TeamUnblockResponse,
    TeamUpdateMemberResponse,
)
```

Methods:

- <code title="post /team/new">client.team.<a href="./src/Hanzo_AI/resources/team/team.py">create</a>(\*\*<a href="src/Hanzo_AI/types/team_create_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/lite_llm_team_table.py">LiteLlmTeamTable</a></code>
- <code title="post /team/update">client.team.<a href="./src/Hanzo_AI/resources/team/team.py">update</a>(\*\*<a href="src/Hanzo_AI/types/team_update_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/team_update_response.py">object</a></code>
- <code title="get /team/list">client.team.<a href="./src/Hanzo_AI/resources/team/team.py">list</a>(\*\*<a href="src/Hanzo_AI/types/team_list_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/team_list_response.py">object</a></code>
- <code title="post /team/delete">client.team.<a href="./src/Hanzo_AI/resources/team/team.py">delete</a>(\*\*<a href="src/Hanzo_AI/types/team_delete_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/team_delete_response.py">object</a></code>
- <code title="post /team/member_add">client.team.<a href="./src/Hanzo_AI/resources/team/team.py">add_member</a>(\*\*<a href="src/Hanzo_AI/types/team_add_member_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/team_add_member_response.py">TeamAddMemberResponse</a></code>
- <code title="post /team/block">client.team.<a href="./src/Hanzo_AI/resources/team/team.py">block</a>(\*\*<a href="src/Hanzo_AI/types/team_block_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/team_block_response.py">object</a></code>
- <code title="post /team/{team_id}/disable_logging">client.team.<a href="./src/Hanzo_AI/resources/team/team.py">disable_logging</a>(team_id) -> <a href="./src/Hanzo_AI/types/team_disable_logging_response.py">object</a></code>
- <code title="get /team/available">client.team.<a href="./src/Hanzo_AI/resources/team/team.py">list_available</a>(\*\*<a href="src/Hanzo_AI/types/team_list_available_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/team_list_available_response.py">object</a></code>
- <code title="post /team/member_delete">client.team.<a href="./src/Hanzo_AI/resources/team/team.py">remove_member</a>(\*\*<a href="src/Hanzo_AI/types/team_remove_member_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/team_remove_member_response.py">object</a></code>
- <code title="get /team/info">client.team.<a href="./src/Hanzo_AI/resources/team/team.py">retrieve_info</a>(\*\*<a href="src/Hanzo_AI/types/team_retrieve_info_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/team_retrieve_info_response.py">object</a></code>
- <code title="post /team/unblock">client.team.<a href="./src/Hanzo_AI/resources/team/team.py">unblock</a>(\*\*<a href="src/Hanzo_AI/types/team_unblock_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/team_unblock_response.py">object</a></code>
- <code title="post /team/member_update">client.team.<a href="./src/Hanzo_AI/resources/team/team.py">update_member</a>(\*\*<a href="src/Hanzo_AI/types/team_update_member_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/team_update_member_response.py">TeamUpdateMemberResponse</a></code>

## Model

Types:

```python
from Hanzo_AI.types.team import ModelAddResponse, ModelRemoveResponse
```

Methods:

- <code title="post /team/model/add">client.team.model.<a href="./src/Hanzo_AI/resources/team/model.py">add</a>(\*\*<a href="src/Hanzo_AI/types/team/model_add_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/team/model_add_response.py">object</a></code>
- <code title="post /team/model/delete">client.team.model.<a href="./src/Hanzo_AI/resources/team/model.py">remove</a>(\*\*<a href="src/Hanzo_AI/types/team/model_remove_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/team/model_remove_response.py">object</a></code>

## Callback

Types:

```python
from Hanzo_AI.types.team import CallbackRetrieveResponse, CallbackAddResponse
```

Methods:

- <code title="get /team/{team_id}/callback">client.team.callback.<a href="./src/Hanzo_AI/resources/team/callback.py">retrieve</a>(team_id) -> <a href="./src/Hanzo_AI/types/team/callback_retrieve_response.py">object</a></code>
- <code title="post /team/{team_id}/callback">client.team.callback.<a href="./src/Hanzo_AI/resources/team/callback.py">add</a>(team_id, \*\*<a href="src/Hanzo_AI/types/team/callback_add_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/team/callback_add_response.py">object</a></code>

# Organization

Types:

```python
from Hanzo_AI.types import (
    BudgetTable,
    OrgMember,
    OrganizationMembershipTable,
    OrganizationTableWithMembers,
    UserRoles,
    OrganizationCreateResponse,
    OrganizationListResponse,
    OrganizationDeleteResponse,
    OrganizationAddMemberResponse,
    OrganizationDeleteMemberResponse,
)
```

Methods:

- <code title="post /organization/new">client.organization.<a href="./src/Hanzo_AI/resources/organization/organization.py">create</a>(\*\*<a href="src/Hanzo_AI/types/organization_create_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/organization_create_response.py">OrganizationCreateResponse</a></code>
- <code title="patch /organization/update">client.organization.<a href="./src/Hanzo_AI/resources/organization/organization.py">update</a>(\*\*<a href="src/Hanzo_AI/types/organization_update_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/organization_table_with_members.py">OrganizationTableWithMembers</a></code>
- <code title="get /organization/list">client.organization.<a href="./src/Hanzo_AI/resources/organization/organization.py">list</a>() -> <a href="./src/Hanzo_AI/types/organization_list_response.py">OrganizationListResponse</a></code>
- <code title="delete /organization/delete">client.organization.<a href="./src/Hanzo_AI/resources/organization/organization.py">delete</a>(\*\*<a href="src/Hanzo_AI/types/organization_delete_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/organization_delete_response.py">OrganizationDeleteResponse</a></code>
- <code title="post /organization/member_add">client.organization.<a href="./src/Hanzo_AI/resources/organization/organization.py">add_member</a>(\*\*<a href="src/Hanzo_AI/types/organization_add_member_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/organization_add_member_response.py">OrganizationAddMemberResponse</a></code>
- <code title="delete /organization/member_delete">client.organization.<a href="./src/Hanzo_AI/resources/organization/organization.py">delete_member</a>(\*\*<a href="src/Hanzo_AI/types/organization_delete_member_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/organization_delete_member_response.py">object</a></code>
- <code title="patch /organization/member_update">client.organization.<a href="./src/Hanzo_AI/resources/organization/organization.py">update_member</a>(\*\*<a href="src/Hanzo_AI/types/organization_update_member_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/organization_membership_table.py">OrganizationMembershipTable</a></code>

## Info

Types:

```python
from Hanzo_AI.types.organization import InfoDeprecatedResponse
```

Methods:

- <code title="get /organization/info">client.organization.info.<a href="./src/Hanzo_AI/resources/organization/info.py">retrieve</a>(\*\*<a href="src/Hanzo_AI/types/organization/info_retrieve_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/organization_table_with_members.py">OrganizationTableWithMembers</a></code>
- <code title="post /organization/info">client.organization.info.<a href="./src/Hanzo_AI/resources/organization/info.py">deprecated</a>(\*\*<a href="src/Hanzo_AI/types/organization/info_deprecated_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/organization/info_deprecated_response.py">object</a></code>

# Customer

Types:

```python
from Hanzo_AI.types import (
    BlockUsers,
    LiteLlmEndUserTable,
    CustomerCreateResponse,
    CustomerUpdateResponse,
    CustomerListResponse,
    CustomerDeleteResponse,
    CustomerBlockResponse,
    CustomerUnblockResponse,
)
```

Methods:

- <code title="post /customer/new">client.customer.<a href="./src/Hanzo_AI/resources/customer.py">create</a>(\*\*<a href="src/Hanzo_AI/types/customer_create_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/customer_create_response.py">object</a></code>
- <code title="post /customer/update">client.customer.<a href="./src/Hanzo_AI/resources/customer.py">update</a>(\*\*<a href="src/Hanzo_AI/types/customer_update_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/customer_update_response.py">object</a></code>
- <code title="get /customer/list">client.customer.<a href="./src/Hanzo_AI/resources/customer.py">list</a>() -> <a href="./src/Hanzo_AI/types/customer_list_response.py">CustomerListResponse</a></code>
- <code title="post /customer/delete">client.customer.<a href="./src/Hanzo_AI/resources/customer.py">delete</a>(\*\*<a href="src/Hanzo_AI/types/customer_delete_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/customer_delete_response.py">object</a></code>
- <code title="post /customer/block">client.customer.<a href="./src/Hanzo_AI/resources/customer.py">block</a>(\*\*<a href="src/Hanzo_AI/types/customer_block_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/customer_block_response.py">object</a></code>
- <code title="get /customer/info">client.customer.<a href="./src/Hanzo_AI/resources/customer.py">retrieve_info</a>(\*\*<a href="src/Hanzo_AI/types/customer_retrieve_info_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/lite_llm_end_user_table.py">LiteLlmEndUserTable</a></code>
- <code title="post /customer/unblock">client.customer.<a href="./src/Hanzo_AI/resources/customer.py">unblock</a>(\*\*<a href="src/Hanzo_AI/types/customer_unblock_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/customer_unblock_response.py">object</a></code>

# Spend

Types:

```python
from Hanzo_AI.types import (
    LiteLlmSpendLogs,
    SpendCalculateSpendResponse,
    SpendListLogsResponse,
    SpendListTagsResponse,
)
```

Methods:

- <code title="post /spend/calculate">client.spend.<a href="./src/Hanzo_AI/resources/spend.py">calculate_spend</a>(\*\*<a href="src/Hanzo_AI/types/spend_calculate_spend_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/spend_calculate_spend_response.py">object</a></code>
- <code title="get /spend/logs">client.spend.<a href="./src/Hanzo_AI/resources/spend.py">list_logs</a>(\*\*<a href="src/Hanzo_AI/types/spend_list_logs_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/spend_list_logs_response.py">SpendListLogsResponse</a></code>
- <code title="get /spend/tags">client.spend.<a href="./src/Hanzo_AI/resources/spend.py">list_tags</a>(\*\*<a href="src/Hanzo_AI/types/spend_list_tags_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/spend_list_tags_response.py">SpendListTagsResponse</a></code>

# Global

## Spend

Types:

```python
from Hanzo_AI.types.global_ import (
    SpendListTagsResponse,
    SpendResetResponse,
    SpendRetrieveReportResponse,
)
```

Methods:

- <code title="get /global/spend/tags">client.global*.spend.<a href="./src/Hanzo_AI/resources/global*/spend.py">list*tags</a>(\*\*<a href="src/Hanzo_AI/types/global*/spend*list_tags_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/global*/spend_list_tags_response.py">SpendListTagsResponse</a></code>
- <code title="post /global/spend/reset">client.global*.spend.<a href="./src/Hanzo_AI/resources/global*/spend.py">reset</a>() -> <a href="./src/Hanzo_AI/types/global_/spend_reset_response.py">object</a></code>
- <code title="get /global/spend/report">client.global*.spend.<a href="./src/Hanzo_AI/resources/global*/spend.py">retrieve*report</a>(\*\*<a href="src/Hanzo_AI/types/global*/spend*retrieve_report_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/global*/spend_retrieve_report_response.py">SpendRetrieveReportResponse</a></code>

# Provider

Types:

```python
from Hanzo_AI.types import ProviderListBudgetsResponse
```

Methods:

- <code title="get /provider/budgets">client.provider.<a href="./src/Hanzo_AI/resources/provider.py">list_budgets</a>() -> <a href="./src/Hanzo_AI/types/provider_list_budgets_response.py">ProviderListBudgetsResponse</a></code>

# Cache

Types:

```python
from Hanzo_AI.types import CacheDeleteResponse, CacheFlushAllResponse, CachePingResponse
```

Methods:

- <code title="post /cache/delete">client.cache.<a href="./src/Hanzo_AI/resources/cache/cache.py">delete</a>() -> <a href="./src/Hanzo_AI/types/cache_delete_response.py">object</a></code>
- <code title="post /cache/flushall">client.cache.<a href="./src/Hanzo_AI/resources/cache/cache.py">flush_all</a>() -> <a href="./src/Hanzo_AI/types/cache_flush_all_response.py">object</a></code>
- <code title="get /cache/ping">client.cache.<a href="./src/Hanzo_AI/resources/cache/cache.py">ping</a>() -> <a href="./src/Hanzo_AI/types/cache_ping_response.py">CachePingResponse</a></code>

## Redis

Types:

```python
from Hanzo_AI.types.cache import RediRetrieveInfoResponse
```

Methods:

- <code title="get /cache/redis/info">client.cache.redis.<a href="./src/Hanzo_AI/resources/cache/redis.py">retrieve_info</a>() -> <a href="./src/Hanzo_AI/types/cache/redi_retrieve_info_response.py">object</a></code>

# Guardrails

Types:

```python
from Hanzo_AI.types import GuardrailListResponse
```

Methods:

- <code title="get /guardrails/list">client.guardrails.<a href="./src/Hanzo_AI/resources/guardrails.py">list</a>() -> <a href="./src/Hanzo_AI/types/guardrail_list_response.py">GuardrailListResponse</a></code>

# Add

Types:

```python
from Hanzo_AI.types import IPAddress, AddAddAllowedIPResponse
```

Methods:

- <code title="post /add/allowed_ip">client.add.<a href="./src/Hanzo_AI/resources/add.py">add_allowed_ip</a>(\*\*<a href="src/Hanzo_AI/types/add_add_allowed_ip_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/add_add_allowed_ip_response.py">object</a></code>

# Delete

Types:

```python
from Hanzo_AI.types import DeleteCreateAllowedIPResponse
```

Methods:

- <code title="post /delete/allowed_ip">client.delete.<a href="./src/Hanzo_AI/resources/delete.py">create_allowed_ip</a>(\*\*<a href="src/Hanzo_AI/types/delete_create_allowed_ip_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/delete_create_allowed_ip_response.py">object</a></code>

# Files

Types:

```python
from Hanzo_AI.types import (
    FileCreateResponse,
    FileRetrieveResponse,
    FileListResponse,
    FileDeleteResponse,
)
```

Methods:

- <code title="post /{provider}/v1/files">client.files.<a href="./src/Hanzo_AI/resources/files/files.py">create</a>(provider, \*\*<a href="src/Hanzo_AI/types/file_create_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/file_create_response.py">object</a></code>
- <code title="get /{provider}/v1/files/{file_id}">client.files.<a href="./src/Hanzo_AI/resources/files/files.py">retrieve</a>(file_id, \*, provider) -> <a href="./src/Hanzo_AI/types/file_retrieve_response.py">object</a></code>
- <code title="get /{provider}/v1/files">client.files.<a href="./src/Hanzo_AI/resources/files/files.py">list</a>(provider, \*\*<a href="src/Hanzo_AI/types/file_list_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/file_list_response.py">object</a></code>
- <code title="delete /{provider}/v1/files/{file_id}">client.files.<a href="./src/Hanzo_AI/resources/files/files.py">delete</a>(file_id, \*, provider) -> <a href="./src/Hanzo_AI/types/file_delete_response.py">object</a></code>

## Content

Types:

```python
from Hanzo_AI.types.files import ContentRetrieveResponse
```

Methods:

- <code title="get /{provider}/v1/files/{file_id}/content">client.files.content.<a href="./src/Hanzo_AI/resources/files/content.py">retrieve</a>(file_id, \*, provider) -> <a href="./src/Hanzo_AI/types/files/content_retrieve_response.py">object</a></code>

# Budget

Types:

```python
from Hanzo_AI.types import (
    BudgetNew,
    BudgetCreateResponse,
    BudgetUpdateResponse,
    BudgetListResponse,
    BudgetDeleteResponse,
    BudgetInfoResponse,
    BudgetSettingsResponse,
)
```

Methods:

- <code title="post /budget/new">client.budget.<a href="./src/Hanzo_AI/resources/budget.py">create</a>(\*\*<a href="src/Hanzo_AI/types/budget_create_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/budget_create_response.py">object</a></code>
- <code title="post /budget/update">client.budget.<a href="./src/Hanzo_AI/resources/budget.py">update</a>(\*\*<a href="src/Hanzo_AI/types/budget_update_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/budget_update_response.py">object</a></code>
- <code title="get /budget/list">client.budget.<a href="./src/Hanzo_AI/resources/budget.py">list</a>() -> <a href="./src/Hanzo_AI/types/budget_list_response.py">object</a></code>
- <code title="post /budget/delete">client.budget.<a href="./src/Hanzo_AI/resources/budget.py">delete</a>(\*\*<a href="src/Hanzo_AI/types/budget_delete_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/budget_delete_response.py">object</a></code>
- <code title="post /budget/info">client.budget.<a href="./src/Hanzo_AI/resources/budget.py">info</a>(\*\*<a href="src/Hanzo_AI/types/budget_info_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/budget_info_response.py">object</a></code>
- <code title="get /budget/settings">client.budget.<a href="./src/Hanzo_AI/resources/budget.py">settings</a>(\*\*<a href="src/Hanzo_AI/types/budget_settings_params.py">params</a>) -> <a href="./src/Hanzo_AI/types/budget_settings_response.py">object</a></code>
