"""
xAI Grok Client for Python — DevSkyy
Grok uses OpenAI-compatible API at https://api.x.ai/v1
Unique features: Live web search, real-time data, X/Twitter access
"""

import os
import json
import time
import base64
from pathlib import Path
from typing import Optional, List, Dict, Any, Generator
import openai
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / '.env')


class GrokClient:
    """xAI Grok client — OpenAI SDK pointed at api.x.ai"""

    def __init__(self, api_key: Optional[str] = None, **options):
        self.api_key = api_key or os.getenv('XAI_API_KEY') or os.getenv('GROK_API_KEY')
        if not self.api_key:
            raise ValueError('xAI API key required. Set XAI_API_KEY in .env')

        settings_path = Path(__file__).parent.parent / 'config' / 'settings.json'
        with open(settings_path) as f:
            self.settings = json.load(f)

        models_path = Path(__file__).parent.parent / 'config' / 'models.json'
        with open(models_path) as f:
            self.model_configs = json.load(f)

        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=options.get('base_url', self.settings['baseURL'])
        )

        self.default_model = options.get('model', self.settings['defaultModel'])
        self.generation_config = {
            **self.settings['generationConfig'],
            **options.get('generation_config', {})
        }
        self.last_request_time = 0.0
        self.min_request_interval = 60.0 / self.settings['rateLimit']['requestsPerMinute']

    def _rate_limit(self):
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def generate_content(self, prompt: str, model: Optional[str] = None,
                         system_prompt: Optional[str] = None, **config) -> Dict[str, Any]:
        self._rate_limit()
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})

        try:
            response = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                **{**self.generation_config, **config}
            )
            return {
                'text': response.choices[0].message.content,
                'finish_reason': response.choices[0].finish_reason,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            }
        except Exception as e:
            return self._handle_error(e)

    def generate_content_stream(self, prompt: str, model: Optional[str] = None,
                                system_prompt: Optional[str] = None, **config) -> Generator:
        self._rate_limit()
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})

        try:
            with self.client.chat.completions.stream(
                model=model or self.default_model,
                messages=messages,
                **{**self.generation_config, **config}
            ) as stream:
                for chunk in stream:
                    delta = chunk.choices[0].delta.content if chunk.choices else ''
                    if delta:
                        yield {'text': delta, 'done': False}
            yield {'text': '', 'done': True}
        except Exception as e:
            raise self._handle_error(e)

    def live_search(self, query: str, model: str = 'grok-3',
                    sources: Optional[List] = None,
                    system_prompt: str = 'You have access to real-time web and X data.') -> Dict[str, Any]:
        """Grok live search — real-time web + X/Twitter grounding"""
        self._rate_limit()
        if sources is None:
            sources = [{'type': 'web'}, {'type': 'x'}]

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': query}
                ],
                search_parameters={'mode': 'on', 'sources': sources},
                max_tokens=self.generation_config.get('max_tokens', 2048)
            )
            msg = response.choices[0].message
            return {
                'text': msg.content,
                'citations': getattr(msg, 'citations', []),
                'usage': response.usage
            }
        except Exception as e:
            return self._handle_error(e)

    def analyze_image(self, image_path: Optional[str] = None, image_url: Optional[str] = None,
                      prompt: str = 'Describe this image', model: str = 'grok-2-vision-1212',
                      detail: str = 'auto') -> Dict[str, Any]:
        self._rate_limit()
        if image_path:
            with open(image_path, 'rb') as f:
                data = base64.b64encode(f.read()).decode()
            ext = Path(image_path).suffix.lstrip('.').replace('jpg', 'jpeg')
            image_content = {'type': 'image_url',
                             'image_url': {'url': f'data:image/{ext};base64,{data}', 'detail': detail}}
        elif image_url:
            image_content = {'type': 'image_url', 'image_url': {'url': image_url, 'detail': detail}}
        else:
            raise ValueError('Either image_path or image_url required')

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{'role': 'user', 'content': [
                    {'type': 'text', 'text': prompt}, image_content
                ]}],
                max_tokens=self.generation_config.get('max_tokens', 1024)
            )
            return {'text': response.choices[0].message.content, 'usage': response.usage}
        except Exception as e:
            return self._handle_error(e)

    def _handle_error(self, error: Exception) -> Dict[str, Any]:
        response = {'error': True, 'message': str(error), 'type': type(error).__name__}
        msg = str(error).lower()
        if '401' in msg or 'authentication' in msg:
            response.update(type='AuthenticationError', message='Invalid API key. Check XAI_API_KEY')
        elif '429' in msg or 'rate limit' in msg:
            response.update(type='RateLimitError', message='Rate limit exceeded')
        if self.settings['logging']['logRequests']:
            print(f'Grok API Error: {response}')
        raise Exception(response)

    def get_available_models(self) -> List[Dict]:
        return self.model_configs['models']

    def get_recommended_model(self, task_type: str) -> str:
        return self.model_configs['modelSelection'].get(task_type, self.default_model)
