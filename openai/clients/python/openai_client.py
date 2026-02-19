"""
OpenAI Client for Python — DevSkyy
Covers: Chat, Streaming, Vision, Embeddings, Images, Assistants, Agents SDK
SDK: openai >= 1.84, openai-agents >= 0.0.16
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


class OpenAIClient:
    """OpenAI client with rate limiting, error handling, and full capability coverage"""

    def __init__(self, api_key: Optional[str] = None, **options):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError('OpenAI API key required. Set OPENAI_API_KEY in .env')

        self.client = openai.OpenAI(api_key=self.api_key)

        settings_path = Path(__file__).parent.parent / 'config' / 'settings.json'
        with open(settings_path) as f:
            self.settings = json.load(f)

        models_path = Path(__file__).parent.parent / 'config' / 'models.json'
        with open(models_path) as f:
            self.model_configs = json.load(f)

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

    def generate_content(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **config
    ) -> Dict[str, Any]:
        """Generate content from text prompt"""
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

    def generate_content_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **config
    ) -> Generator[Dict[str, Any], None, None]:
        """Generate content with streaming"""
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

    def start_chat(
        self,
        system_prompt: str = '',
        history: Optional[List[Dict]] = None,
        model: Optional[str] = None
    ):
        """Start a multi-turn chat session"""
        client = self.client
        model_name = model or self.default_model
        gen_config = self.generation_config

        class ChatSession:
            def __init__(self):
                self.model = model_name
                self.history: List[Dict] = []
                if system_prompt:
                    self.history.append({'role': 'system', 'content': system_prompt})
                if history:
                    self.history.extend(history)

            def send_message(self, message: str) -> Dict[str, Any]:
                self.history.append({'role': 'user', 'content': message})
                response = client.chat.completions.create(
                    model=self.model, messages=self.history, **gen_config
                )
                reply = response.choices[0].message.content
                self.history.append({'role': 'assistant', 'content': reply})
                return {'text': reply, 'usage': response.usage}

        return ChatSession()

    def analyze_image(
        self,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        prompt: str = 'Describe this image',
        model: str = 'gpt-4o',
        detail: str = 'auto'
    ) -> Dict[str, Any]:
        """Analyze image with GPT-4o vision"""
        self._rate_limit()

        if image_path:
            with open(image_path, 'rb') as f:
                data = base64.b64encode(f.read()).decode()
            ext = Path(image_path).suffix.lstrip('.').replace('jpg', 'jpeg')
            image_content = {
                'type': 'image_url',
                'image_url': {'url': f'data:image/{ext};base64,{data}', 'detail': detail}
            }
        elif image_url:
            image_content = {'type': 'image_url', 'image_url': {'url': image_url, 'detail': detail}}
        else:
            raise ValueError('Either image_path or image_url required')

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{'role': 'user', 'content': [
                    {'type': 'text', 'text': prompt},
                    image_content
                ]}],
                max_tokens=self.generation_config.get('max_tokens', 1024)
            )
            return {'text': response.choices[0].message.content, 'usage': response.usage}
        except Exception as e:
            return self._handle_error(e)

    def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict],
        model: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Function/tool calling"""
        self._rate_limit()
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})

        openai_tools = [
            {'type': 'function', 'function': {
                'name': t['name'],
                'description': t['description'],
                'parameters': t['parameters']
            }} for t in tools
        ]

        try:
            response = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                tools=openai_tools,
                tool_choice='auto'
            )
            msg = response.choices[0].message
            tool_call = None
            if msg.tool_calls:
                tc = msg.tool_calls[0]
                tool_call = {'name': tc.function.name, 'args': json.loads(tc.function.arguments)}
            return {
                'text': msg.content or '',
                'tool_call': tool_call,
                'usage': response.usage
            }
        except Exception as e:
            return self._handle_error(e)

    def embed_content(
        self,
        text,
        model: str = 'text-embedding-3-small'
    ):
        """Generate embeddings — single string or list of strings"""
        self._rate_limit()
        is_batch = isinstance(text, list)
        input_data = text if is_batch else [text]

        try:
            response = self.client.embeddings.create(model=model, input=input_data)
            embeddings = [d.embedding for d in response.data]
            return embeddings if is_batch else embeddings[0]
        except Exception as e:
            return self._handle_error(e)

    def generate_image(
        self,
        prompt: str,
        model: str = 'gpt-image-1',
        size: str = '1024x1024',
        quality: str = 'standard',
        n: int = 1
    ) -> List[Dict[str, Any]]:
        """Generate images with DALL·E or gpt-image-1"""
        self._rate_limit()
        try:
            response = self.client.images.generate(
                model=model, prompt=prompt, size=size, quality=quality, n=n
            )
            return [{'url': img.url, 'b64': img.b64_json} for img in response.data]
        except Exception as e:
            return self._handle_error(e)

    def transcribe_audio(
        self,
        file_path: str,
        model: str = 'whisper-1',
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe audio with Whisper"""
        try:
            with open(file_path, 'rb') as f:
                kwargs = {'model': model, 'file': f}
                if language:
                    kwargs['language'] = language
                response = self.client.audio.transcriptions.create(**kwargs)
            return {'text': response.text}
        except Exception as e:
            return self._handle_error(e)

    def text_to_speech(
        self,
        text: str,
        voice: str = 'alloy',
        model: str = 'tts-1-hd',
        output_path: Optional[str] = None
    ) -> bytes:
        """Convert text to speech"""
        try:
            response = self.client.audio.speech.create(model=model, voice=voice, input=text)
            audio = response.content
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(audio)
            return audio
        except Exception as e:
            return self._handle_error(e)

    def _handle_error(self, error: Exception) -> Dict[str, Any]:
        response = {'error': True, 'message': str(error), 'type': type(error).__name__}

        msg = str(error).lower()
        if 'authentication' in msg or 'api key' in msg or '401' in msg:
            response.update(type='AuthenticationError', message='Invalid API key. Check OPENAI_API_KEY')
        elif 'rate limit' in msg or '429' in msg:
            response.update(type='RateLimitError', message='Rate limit exceeded. Please wait and retry')
        elif '400' in msg:
            response['type'] = 'BadRequestError'

        if self.settings['logging']['logRequests']:
            print(f'OpenAI API Error: {response}')

        raise Exception(response)

    def get_available_models(self) -> List[Dict[str, Any]]:
        return self.model_configs['models']

    def get_recommended_model(self, task_type: str) -> str:
        return self.model_configs['modelSelection'].get(task_type, self.default_model)

    def list_models(self) -> List:
        try:
            return list(self.client.models.list())
        except Exception as e:
            return self._handle_error(e)
