# 增加 Azure provider 的請求
_Exported on 2025/10/27 at 11:35:18 [GMT+8] from Cursor (2.0.14)_

---

**User**

請參考@openai.py 增加一個 Azure 的 provider (azure.py)



---

**Cursor**


檢查專案現有結構與 Azure 相關程式碼。


檢查 Azure 相關檔案與現有註冊：


參考 openai.py，準備建立 azure.py，並更新 patterns 與 builtin_registry。


```python
# Copyright 2025 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Azure OpenAI provider for LangExtract."""
# pylint: disable=duplicate-code

from __future__ import annotations

import concurrent.futures
import dataclasses
from typing import Any, Iterator, Sequence

from langextract.core import base_model
from langextract.core import data
from langextract.core import exceptions
from langextract.core import schema
from langextract.core import types as core_types
from langextract.providers import patterns
from langextract.providers import router


@router.register(
    *patterns.AZURE_PATTERNS,
    priority=patterns.AZURE_PRIORITY,
)
@dataclasses.dataclass(init=False)
class AzureLanguageModel(base_model.BaseLanguageModel):
  """Language model inference using Azure OpenAI's API with structured output."""

  deployment_name: str = 'gpt-4o-mini'
  api_key: str | None = None
  endpoint: str | None = None
  api_version: str = '2024-02-15-preview'
  format_type: data.FormatType = data.FormatType.JSON
  temperature: float | None = None
  max_workers: int = 10
  _client: Any = dataclasses.field(default=None, repr=False, compare=False)
  _extra_kwargs: dict[str, Any] = dataclasses.field(
      default_factory=dict, repr=False, compare=False
  )

  @property
  def requires_fence_output(self) -> bool:
    """Azure OpenAI JSON mode returns raw JSON without fences."""
    if self.format_type == data.FormatType.JSON:
      return False
    return super().requires_fence_output

  def __init__(
      self,
      deployment_name: str = 'gpt-4o-mini',
      api_key: str | None = None,
      endpoint: str | None = None,
      api_version: str = '2024-02-15-preview',
      format_type: data.FormatType = data.FormatType.JSON,
      temperature: float | None = None,
      max_workers: int = 10,
      **kwargs,
  ) -> None:
    """Initialize the Azure OpenAI language model.

    Args:
      deployment_name: The Azure deployment name to use (e.g., 'gpt-4o-mini').
      api_key: API key for Azure OpenAI service.
      endpoint: Azure OpenAI endpoint URL (e.g.,
        'https://your-resource.openai.azure.com').
      api_version: Azure OpenAI API version.
      format_type: Output format (JSON or YAML).
      temperature: Sampling temperature.
      max_workers: Maximum number of parallel API calls.
      **kwargs: Ignored extra parameters so callers can pass a superset of
        arguments shared across back-ends without raising ``TypeError``.
    """
    # Lazy import: OpenAI package required
    try:
      # pylint: disable=import-outside-toplevel
      import openai
    except ImportError as e:
      raise exceptions.InferenceConfigError(
          'Azure provider requires openai package. '
          'Install with: pip install langextract[openai]'
      ) from e

    self.deployment_name = deployment_name
    self.api_key = api_key
    self.endpoint = endpoint
    self.api_version = api_version
    self.format_type = format_type
    self.temperature = temperature
    self.max_workers = max_workers

    if not self.api_key:
      raise exceptions.InferenceConfigError('API key not provided.')
    if not self.endpoint:
      raise exceptions.InferenceConfigError('Endpoint not provided.')

    # Initialize the Azure OpenAI client
    self._client = openai.AzureOpenAI(
        api_key=self.api_key,
        azure_endpoint=self.endpoint,
        api_version=self.api_version,
    )

    super().__init__(
        constraint=schema.Constraint(constraint_type=schema.ConstraintType.NONE)
    )
    self._extra_kwargs = kwargs or {}

  def _normalize_reasoning_params(self, config: dict) -> dict:
    """Normalize reasoning parameters for API compatibility.

    Converts flat 'reasoning_effort' to nested 'reasoning' structure.
    Merges with existing reasoning dict if present.
    """
    result = config.copy()

    if 'reasoning_effort' in result:
      effort = result.pop('reasoning_effort')
      reasoning = result.get('reasoning', {}) or {}
      reasoning.setdefault('effort', effort)
      result['reasoning'] = reasoning

    return result

  def _process_single_prompt(
      self, prompt: str, config: dict
  ) -> core_types.ScoredOutput:
    """Process a single prompt and return a ScoredOutput."""
    try:
      normalized_config = self._normalize_reasoning_params(config)

      system_message = ''
      if self.format_type == data.FormatType.JSON:
        system_message = (
            'You are a helpful assistant that responds in JSON format.'
        )
      elif self.format_type == data.FormatType.YAML:
        system_message = (
            'You are a helpful assistant that responds in YAML format.'
        )

      messages = [{'role': 'user', 'content': prompt}]
      if system_message:
        messages.insert(0, {'role': 'system', 'content': system_message})

      api_params = {
          'model': self.deployment_name,
          'messages': messages,
          'n': 1,
      }

      temp = normalized_config.get('temperature', self.temperature)
      if temp is not None:
        api_params['temperature'] = temp

      if self.format_type == data.FormatType.JSON:
        api_params.setdefault('response_format', {'type': 'json_object'})

      if (v := normalized_config.get('max_output_tokens')) is not None:
        api_params['max_tokens'] = v
      if (v := normalized_config.get('top_p')) is not None:
        api_params['top_p'] = v
      for key in [
          'frequency_penalty',
          'presence_penalty',
          'seed',
          'stop',
          'logprobs',
          'top_logprobs',
          'reasoning',
          'response_format',
      ]:
        if (v := normalized_config.get(key)) is not None:
          api_params[key] = v

      response = self._client.chat.completions.create(**api_params)

      # Extract the response text using the v1.x response format
      output_text = response.choices[0].message.content

      return core_types.ScoredOutput(score=1.0, output=output_text)

    except Exception as e:
      raise exceptions.InferenceRuntimeError(
          f'Azure OpenAI API error: {str(e)}', original=e
      ) from e

  def infer(
      self, batch_prompts: Sequence[str], **kwargs
  ) -> Iterator[Sequence[core_types.ScoredOutput]]:
    """Runs inference on a list of prompts via Azure OpenAI's API.

    Args:
      batch_prompts: A list of string prompts.
      **kwargs: Additional generation params (temperature, top_p, etc.)

    Yields:
      Lists of ScoredOutputs.
    """
    merged_kwargs = self.merge_kwargs(kwargs)

    config = {}

    temp = merged_kwargs.get('temperature', self.temperature)
    if temp is not None:
      config['temperature'] = temp
    if 'max_output_tokens' in merged_kwargs:
      config['max_output_tokens'] = merged_kwargs['max_output_tokens']
    if 'top_p' in merged_kwargs:
      config['top_p'] = merged_kwargs['top_p']

    for key in [
        'frequency_penalty',
        'presence_penalty',
        'seed',
        'stop',
        'logprobs',
        'top_logprobs',
        'reasoning_effort',
        'reasoning',
        'response_format',
    ]:
      if key in merged_kwargs:
        config[key] = merged_kwargs[key]

    # Use parallel processing for batches larger than 1
    if len(batch_prompts) > 1 and self.max_workers > 1:
      with concurrent.futures.ThreadPoolExecutor(
          max_workers=min(self.max_workers, len(batch_prompts))
      ) as executor:
        future_to_index = {
            executor.submit(
                self._process_single_prompt, prompt, config.copy()
            ): i
            for i, prompt in enumerate(batch_prompts)
        }

        results: list[core_types.ScoredOutput | None] = [None] * len(
            batch_prompts
        )
        for future in concurrent.futures.as_completed(future_to_index):
          index = future_to_index[future]
          try:
            results[index] = future.result()
          except Exception as e:
            raise exceptions.InferenceRuntimeError(
                f'Parallel inference error: {str(e)}', original=e
            ) from e

        for result in results:
          if result is None:
            raise exceptions.InferenceRuntimeError(
                'Failed to process one or more prompts'
            )
          yield [result]
    else:
      # Sequential processing for single prompt or worker
      for prompt in batch_prompts:
        result = self._process_single_prompt(prompt, config.copy())
        yield [result]  # pylint: disable=duplicate-code

```

```python
# Copyright 2025 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Centralized pattern definitions for built-in providers.

This module defines all patterns and priorities for built-in providers
in one place to avoid duplication.
"""

# Gemini provider patterns
GEMINI_PATTERNS = (r'^gemini',)
GEMINI_PRIORITY = 10

# OpenAI provider patterns
OPENAI_PATTERNS = (
    r'^gpt-4',
    r'^gpt4\.',
    r'^gpt-5',
    r'^gpt5\.',
)
OPENAI_PRIORITY = 10

# Azure OpenAI provider patterns
AZURE_PATTERNS = (
    r'^azure',  # azure deployment names
    r'^gpt-4o-mini-azure',  # specific azure model names
    r'^gpt-4o-azure',
    r'^gpt-35-turbo-azure',
)
AZURE_PRIORITY = 15  # Higher priority than OpenAI to handle Azure-specific configs

# Ollama provider patterns
OLLAMA_PATTERNS = (
    # Standard Ollama naming patterns
    r'^gemma',  # gemma2:2b, gemma2:9b, etc.
    r'^llama',  # llama3.2:1b, llama3.1:8b, etc.
    r'^mistral',  # mistral:7b, mistral-nemo:12b, etc.
    r'^mixtral',  # mixtral:8x7b, mixtral:8x22b, etc.
    r'^phi',  # phi3:3.8b, phi3:14b, etc.
    r'^qwen',  # qwen2.5:0.5b to 72b
    r'^deepseek',  # deepseek-coder-v2, etc.
    r'^command-r',  # command-r:35b, command-r-plus:104b
    r'^starcoder',  # starcoder2:3b, starcoder2:7b, etc.
    r'^codellama',  # codellama:7b, codellama:13b, etc.
    r'^codegemma',  # codegemma:2b, codegemma:7b
    r'^tinyllama',  # tinyllama:1.1b
    r'^wizardcoder',  # wizardcoder:7b, wizardcoder:13b, etc.
    r'^gpt-oss',  # Open source GPT variants
    # HuggingFace model patterns
    r'^meta-llama/[Ll]lama',
    r'^google/gemma',
    r'^mistralai/[Mm]istral',
    r'^mistralai/[Mm]ixtral',
    r'^microsoft/phi',
    r'^Qwen/',
    r'^deepseek-ai/',
    r'^bigcode/starcoder',
    r'^codellama/',
    r'^TinyLlama/',
    r'^WizardLM/',
)
OLLAMA_PRIORITY = 10

```

```python
# Copyright 2025 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Built-in provider registration configuration.

This module defines the registration details for all built-in providers,
using patterns from the centralized patterns module.
"""

from typing import TypedDict

from langextract.providers import patterns


class ProviderConfig(TypedDict):
  """Configuration for a provider registration."""

  patterns: tuple[str, ...]
  target: str
  priority: int


# Built-in provider configurations using centralized patterns
BUILTIN_PROVIDERS: list[ProviderConfig] = [
    {
        'patterns': patterns.GEMINI_PATTERNS,
        'target': 'langextract.providers.gemini:GeminiLanguageModel',
        'priority': patterns.GEMINI_PRIORITY,
    },
    {
        'patterns': patterns.AZURE_PATTERNS,
        'target': 'langextract.providers.azure:AzureLanguageModel',
        'priority': patterns.AZURE_PRIORITY,
    },
    {
        'patterns': patterns.OLLAMA_PATTERNS,
        'target': 'langextract.providers.ollama:OllamaLanguageModel',
        'priority': patterns.OLLAMA_PRIORITY,
    },
    {
        'patterns': patterns.OPENAI_PATTERNS,
        'target': 'langextract.providers.openai:OpenAILanguageModel',
        'priority': patterns.OPENAI_PRIORITY,
    },
]

```

檢查並更新 `__init__.py` 以匯出 azure 模組：


```python
# Copyright 2025 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Provider package for LangExtract.

This package contains provider implementations for various LLM backends.
Each provider can be imported independently for fine-grained dependency
management in build systems.
"""

import importlib
from importlib import metadata
import os

from absl import logging

from langextract.providers import router
from langextract.providers.builtin_registry import BUILTIN_PROVIDERS
from langextract.providers.router import register
from langextract.providers.router import register_lazy

registry = router  # Backward compat alias

__all__ = [
    'azure',
    'gemini',
    'openai',
    'ollama',
    'router',
    'registry',  # Backward compat
    'schemas',
    'load_plugins_once',
    'load_builtins_once',
]

# Track provider loading for lazy initialization
_PLUGINS_LOADED = False
_BUILTINS_LOADED = False


def load_builtins_once() -> None:
  """Load built-in providers to register their patterns.

  Idempotent function that ensures provider patterns are available
  for model resolution. Uses lazy registration to ensure providers
  can be re-registered after registry.clear() even if their modules
  are already in sys.modules.
  """
  global _BUILTINS_LOADED  # pylint: disable=global-statement

  if _BUILTINS_LOADED:
    return

  # Register built-ins lazily so they can be re-registered after a registry.clear()
  # even if their modules were already imported earlier in the test run.
  for config in BUILTIN_PROVIDERS:
    register_lazy(
        *config['patterns'],
        target=config['target'],
        priority=config['priority'],
    )

  _BUILTINS_LOADED = True


def load_plugins_once() -> None:
  """Load provider plugins from installed packages.

  Discovers and loads langextract provider plugins using entry points.
  This function is idempotent - multiple calls have no effect.
  """
  global _PLUGINS_LOADED  # pylint: disable=global-statement
  if _PLUGINS_LOADED:
    return

  # Check if plugin loading is disabled
  if os.environ.get('LANGEXTRACT_DISABLE_PLUGINS', '').lower() in (
      '1',
      'true',
      'yes',
  ):
    logging.info('Plugin loading disabled via LANGEXTRACT_DISABLE_PLUGINS')
    _PLUGINS_LOADED = True
    return

  # Load built-in providers first
  load_builtins_once()

  try:
    # Get entry points using the metadata API
    eps = metadata.entry_points()

    # Try different APIs based on what's available
    if hasattr(eps, 'select'):
      # Python 3.10+ API
      provider_eps = eps.select(group='langextract.providers')
    elif hasattr(eps, 'get'):
      # Python 3.9 API
      provider_eps = eps.get('langextract.providers', [])
    else:
      # Fallback for older versions
      provider_eps = [
          ep
          for ep in eps
          if getattr(ep, 'group', None) == 'langextract.providers'
      ]

    for entry_point in provider_eps:
      try:
        # Load the entry point
        provider_class = entry_point.load()
        logging.info('Loaded provider plugin: %s', entry_point.name)

        # Register if it has pattern information
        if hasattr(provider_class, 'get_model_patterns'):
          patterns = provider_class.get_model_patterns()
          for pattern in patterns:
            register(
                pattern,
                priority=getattr(
                    provider_class,
                    'pattern_priority',
                    20,  # Default plugin priority
                ),
            )(provider_class)
          logging.info(
              'Registered %d patterns for %s', len(patterns), entry_point.name
          )
      except Exception as e:
        logging.warning(
            'Failed to load provider plugin %s: %s', entry_point.name, e
        )

  except Exception as e:
    logging.warning('Error discovering provider plugins: %s', e)

  _PLUGINS_LOADED = True


def _reset_for_testing() -> None:
  """Reset plugin loading state for testing. Should only be used in tests."""
  global _PLUGINS_LOADED, _BUILTINS_LOADED  # pylint: disable=global-statement
  _PLUGINS_LOADED = False
  _BUILTINS_LOADED = False


def __getattr__(name: str):
  """Lazy loading for submodules."""
  if name == 'router':
    return importlib.import_module('langextract.providers.router')
  elif name == 'schemas':
    return importlib.import_module('langextract.providers.schemas')
  elif name == '_PLUGINS_LOADED':
    return _PLUGINS_LOADED
  elif name == '_BUILTINS_LOADED':
    return _BUILTINS_LOADED
  raise AttributeError(f'module {__name__!r} has no attribute {name!r}')

```

檢查 lint 錯誤：


已新增 Azure provider。變更如下：

## 完成的工作

### 1. **建立 `langextract/providers/azure.py`**
   - 以 `OpenAILanguageModel` 為基礎
   - 包含 `api_key`、`endpoint`、`api_version`
   - 支援並行處理
   - 支援 JSON 與 YAML
   - 使用 `openai.AzureOpenAI` 初始化客戶端

### 2. **更新 `langextract/providers/patterns.py`**
   - 新增 `AZURE_PATTERNS` 以識別 Azure 部署名稱
   - 設定 `AZURE_PRIORITY = 15`

### 3. **更新 `langextract/providers/builtin_registry.py`**
   - 註冊 `AzureLanguageModel`

### 4. **更新 `langextract/providers/__init__.py`**
   - 在 `__all__` 加入 `'azure'`

Azure provider 可透過 `factory.create_model` 使用，或直接實例化 `AzureLanguageModel`。

範例：
```python
import langextract as lx

config = lx.factory.ModelConfig(
    model_id="azure",
    provider="AzureLanguageModel",
    provider_kwargs={
        "api_key": "your-azure-api-key",
        "endpoint": "https://your-resource.openai.azure.com",
        "deployment_name": "gpt-4o-mini"
    }
)
model = lx.factory.create_model(config)
```

```python
import langextract as lx

config = lx.factory.ModelConfig(
    model_id="azure",
    provider="AzureLanguageModel",
    provider_kwargs={
        "api_key": "your-azure-api-key",
        "endpoint": "https://your-resource.openai.azure.com",
        "deployment_name": "gpt-4o-mini"
    }
)
model = lx.factory.create_model(config)
```

