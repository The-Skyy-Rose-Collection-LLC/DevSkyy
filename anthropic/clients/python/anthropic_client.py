"""
Anthropic Claude Client for Python — DevSkyy
Claude 4.5/4.6: Sonnet, Opus, Haiku
Capabilities: Chat, streaming, vision, tool use, long context (200K)
"""

import os
import json
import time
import base64
from pathlib import Path
from typing import Optional, List, Dict, Any, Generator
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / '.env')


class AnthropicClient:
    """Anthropic Claude client"""

    def __init__(self, api_key: Optional[str] = None, **options):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError('Anthropic API key required. Set ANTHROPIC_API_KEY in .env')

        settings_path = Path(__file__).parent.parent / 'config' / 'settings.json'
        with open(settings_path) as f:
            self.settings = json.load(f)

        models_path = Path(__file__).parent.parent / 'config' / 'models.json'
        with open(models_path) as f:
            self.model_configs = json.load(f)

        self.client = Anthropic(
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
        messages = [{'role': 'user', 'content': prompt}]

        try:
            response = self.client.messages.create(
                model=model or self.default_model,
                messages=messages,
                system=system_prompt,
                **{**self.generation_config, **config}
            )
            return {
                'text': response.content[0].text,
                'stop_reason': response.stop_reason,
                'usage': {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens
                }
            }
        except Exception as e:
            return self._handle_error(e)

    def generate_content_stream(self, prompt: str, model: Optional[str] = None,
                                system_prompt: Optional[str] = None, **config) -> Generator:
        self._rate_limit()
        messages = [{'role': 'user', 'content': prompt}]

        try:
            with self.client.messages.stream(
                model=model or self.default_model,
                messages=messages,
                system=system_prompt,
                **{**self.generation_config, **config}
            ) as stream:
                for event in stream:
                    if hasattr(event, 'delta') and hasattr(event.delta, 'text'):
                        yield {'text': event.delta.text, 'done': False}
            yield {'text': '', 'done': True}
        except Exception as e:
            raise self._handle_error(e)

    def analyze_image(self, image_path: Optional[str] = None, image_url: Optional[str] = None,
                      prompt: str = 'Describe this image', model: Optional[str] = None) -> Dict[str, Any]:
        self._rate_limit()
        if image_path:
            with open(image_path, 'rb') as f:
                data = base64.b64encode(f.read()).decode()
            ext = Path(image_path).suffix.lstrip('.').replace('jpg', 'jpeg')
            image_content = {
                'type': 'image',
                'source': {
                    'type': 'base64',
                    'media_type': f'image/{ext}',
                    'data': data
                }
            }
        elif image_url:
            image_content = {
                'type': 'image',
                'source': {'type': 'url', 'url': image_url}
            }
        else:
            raise ValueError('Either image_path or image_url required')

        try:
            response = self.client.messages.create(
                model=model or self.default_model,
                messages=[{
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': prompt},
                        image_content
                    ]
                }],
                max_tokens=self.generation_config.get('max_tokens', 4096)
            )
            return {'text': response.content[0].text, 'usage': response.usage}
        except Exception as e:
            return self._handle_error(e)

    def _handle_error(self, error: Exception) -> Dict[str, Any]:
        response = {'error': True, 'message': str(error), 'type': type(error).__name__}
        msg = str(error).lower()
        if '401' in msg or 'authentication' in msg:
            response.update(type='AuthenticationError', message='Invalid API key. Check ANTHROPIC_API_KEY')
        elif '429' in msg or 'rate limit' in msg:
            response.update(type='RateLimitError', message='Rate limit exceeded')
        if self.settings['logging']['logRequests']:
            print(f'Anthropic API Error: {response}')
        raise Exception(response)

    def get_available_models(self) -> List[Dict]:
        return self.model_configs['models']

    def get_recommended_model(self, task_type: str) -> str:
        return self.model_configs['modelSelection'].get(task_type, self.default_model)
