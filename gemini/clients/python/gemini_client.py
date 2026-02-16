"""
Gemini AI Client for Python
Complete integration with Google's Gemini API
Updated for new google-genai SDK (v1.59.0+)
"""

import os
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Generator
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')


class GeminiClient:
    """Google Gemini AI client with rate limiting and error handling"""

    def __init__(self, api_key: Optional[str] = None, **options):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')

        if not self.api_key:
            raise ValueError('Gemini API key is required. Set GEMINI_API_KEY in .env file')

        # Initialize new SDK client
        self.client = genai.Client(api_key=self.api_key)

        # Load settings
        settings_path = Path(__file__).parent.parent / 'config' / 'settings.json'
        with open(settings_path) as f:
            self.settings = json.load(f)

        # Load model configurations
        models_path = Path(__file__).parent.parent / 'config' / 'models.json'
        with open(models_path) as f:
            self.model_configs = json.load(f)

        self.default_model = options.get('model', self.settings['defaultModel'])

        # Generation config
        self.generation_config = {
            **self.settings['generationConfig'],
            **options.get('generation_config', {})
        }

        # Safety settings (new SDK format)
        self.safety_settings = [
            {
                'category': s['category'],
                'threshold': s['threshold']
            }
            for s in self.settings['safetySettings']
        ]

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 60.0 / self.settings['rateLimit']['requestsPerMinute']

    def _rate_limit(self):
        """Apply rate limiting"""
        now = time.time()
        time_since_last = now - self.last_request_time

        if time_since_last < self.min_request_interval:
            delay = self.min_request_interval - time_since_last
            time.sleep(delay)

        self.last_request_time = time.time()

    def generate_content(
        self,
        prompt: str,
        model: Optional[str] = None,
        **config
    ) -> Dict[str, Any]:
        """Generate content from text prompt"""
        self._rate_limit()

        model_name = model or self.default_model

        try:
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    **self.generation_config,
                    **config,
                    'safety_settings': self.safety_settings
                }
            )

            return {
                'text': response.text,
                'candidates': [c.to_dict() for c in response.candidates] if hasattr(response, 'candidates') else [],
                'prompt_feedback': response.prompt_feedback.to_dict() if hasattr(response, 'prompt_feedback') else None,
                'usage_metadata': {
                    'prompt_token_count': response.usage_metadata.prompt_token_count,
                    'candidates_token_count': response.usage_metadata.candidates_token_count,
                    'total_token_count': response.usage_metadata.total_token_count
                } if hasattr(response, 'usage_metadata') else None
            }
        except Exception as e:
            return self._handle_error(e)

    def generate_content_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        **config
    ) -> Generator[Dict[str, Any], None, None]:
        """Generate content with streaming"""
        self._rate_limit()

        model_name = model or self.default_model

        try:
            stream = self.client.models.generate_content_stream(
                model=model_name,
                contents=prompt,
                config={
                    **self.generation_config,
                    **config,
                    'safety_settings': self.safety_settings
                }
            )

            for chunk in stream:
                yield {
                    'text': chunk.text if hasattr(chunk, 'text') else '',
                    'done': False
                }

            # Final chunk
            yield {
                'text': '',
                'done': True
            }
        except Exception as e:
            raise self._handle_error(e)

    def start_chat(
        self,
        history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None,
        **config
    ):
        """Start a chat conversation"""
        model_name = model or self.default_model

        class ChatSession:
            def __init__(self, client, model, history, generation_config, safety_settings):
                self.client = client
                self.model = model
                self.history = history or []
                self.generation_config = generation_config
                self.safety_settings = safety_settings

            def send_message(self, message: str):
                # Build contents from history
                contents = []
                for msg in self.history:
                    contents.append({
                        'role': msg['role'],
                        'parts': [{'text': msg['content']}]
                    })
                contents.append({
                    'role': 'user',
                    'parts': [{'text': message}]
                })

                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config={
                        **self.generation_config,
                        'safety_settings': self.safety_settings
                    }
                )

                # Update history
                self.history.append({'role': 'user', 'content': message})
                self.history.append({'role': 'model', 'content': response.text})

                return response

        return ChatSession(
            self.client,
            model_name,
            history,
            self.generation_config,
            self.safety_settings
        )

    def analyze_image(
        self,
        image_path: Optional[str] = None,
        image_data: Optional[Any] = None,
        prompt: str = "Describe this image",
        model: str = 'gemini-2.5-flash'
    ) -> Dict[str, Any]:
        """Analyze an image"""
        self._rate_limit()

        if image_path:
            from PIL import Image
            image = Image.open(image_path)
        elif image_data:
            image = image_data
        else:
            raise ValueError('Either image_path or image_data must be provided')

        try:
            response = self.client.models.generate_content(
                model=model,
                contents=[
                    {
                        'role': 'user',
                        'parts': [
                            {'text': prompt},
                            {'inline_data': image}
                        ]
                    }
                ],
                config={
                    **self.generation_config,
                    'safety_settings': self.safety_settings
                }
            )

            return {
                'text': response.text,
                'candidates': [c.to_dict() for c in response.candidates] if hasattr(response, 'candidates') else [],
                'usage_metadata': {
                    'total_token_count': response.usage_metadata.total_token_count
                } if hasattr(response, 'usage_metadata') else None
            }
        except Exception as e:
            return self._handle_error(e)

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """Count tokens in text"""
        model_name = model or self.default_model

        try:
            result = self.client.models.count_tokens(
                model=model_name,
                contents=text
            )
            return result.total_tokens
        except Exception as e:
            return self._handle_error(e)

    def embed_content(self, text: str, model: str = 'text-embedding-004') -> List[float]:
        """Embed text for semantic search"""
        self._rate_limit()

        try:
            result = self.client.models.embed_content(
                model=model,
                content=text
            )
            return result.embedding.values
        except Exception as e:
            return self._handle_error(e)

    def _handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle API errors"""
        error_response = {
            'error': True,
            'message': str(error),
            'type': type(error).__name__
        }

        error_msg = str(error).lower()

        if 'api key' in error_msg or 'authentication' in error_msg:
            error_response['type'] = 'AuthenticationError'
            error_response['message'] = 'Invalid API key. Check your GEMINI_API_KEY'
        elif 'quota' in error_msg or 'rate limit' in error_msg:
            error_response['type'] = 'RateLimitError'
            error_response['message'] = 'Rate limit exceeded. Please wait and retry'
        elif 'safety' in error_msg:
            error_response['type'] = 'SafetyError'
            error_response['message'] = 'Content blocked by safety filters'

        if self.settings['logging']['logRequests']:
            print(f"Gemini API Error: {error_response}")

        raise Exception(error_response)

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available models from config"""
        return self.model_configs['models']

    def get_recommended_model(self, task_type: str) -> str:
        """Get recommended model for task"""
        return self.model_configs['modelSelection'].get(task_type, self.default_model)

    def list_models(self):
        """List models from API"""
        try:
            models = self.client.models.list()
            return models
        except Exception as e:
            return self._handle_error(e)
