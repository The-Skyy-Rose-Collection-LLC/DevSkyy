"""
Tripo3D API Client for 3D Model Generation

SDK Reference: https://github.com/VAST-AI-Research/tripo-python-sdk
Docs: https://docs.tripo3d.ai/

Features:
- Text-to-3D generation
- Image-to-3D generation
- Multiview-to-3D generation
- Async support
- Output formats: GLB, FBX, OBJ

Truth Protocol Compliance:
- Rule #1: API verified from official SDK docs
- Rule #5: API key via TRIPO_API_KEY env var
- Rule #10: Error handling with continue policy
- Rule #12: Performance tracking for SLO compliance
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any

import httpx

from agent.modules.clothing.schemas.schemas import Model3DFormat, Model3DResult
from core.enterprise_error_handler import record_error

logger = logging.getLogger(__name__)


class Tripo3DError(Exception):
    """Custom exception for Tripo3D API errors."""

    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class Tripo3DClient:
    """
    Async client for Tripo3D 3D model generation API.

    Provides text-to-3D and image-to-3D capabilities for clothing assets.
    Follows enterprise patterns with retry logic and structured error handling.

    Example:
        client = Tripo3DClient()
        await client.initialize()

        result = await client.text_to_3d(
            prompt="Black hoodie with rose pattern, luxury streetwear",
            output_format=Model3DFormat.GLB
        )

    Attributes:
        api_key: Tripo3D API key from environment
        base_url: Tripo3D API base URL
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
    """

    BASE_URL = "https://api.tripo3d.ai/v2/openapi"
    DEFAULT_TIMEOUT = 120.0
    MAX_POLL_ATTEMPTS = 60  # 5 minutes with 5-second intervals
    POLL_INTERVAL = 5.0

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 3,
        download_dir: str | None = None,
    ):
        """
        Initialize Tripo3D client.

        Args:
            api_key: API key (defaults to TRIPO_API_KEY env var)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            download_dir: Directory for downloading 3D models
        """
        self.api_key = api_key or os.getenv("TRIPO_API_KEY", "")
        self.timeout = timeout
        self.max_retries = max_retries
        self.download_dir = Path(download_dir or "/tmp/tripo3d_models")
        self._client: httpx.AsyncClient | None = None
        self._initialized = False

    async def initialize(self) -> bool:
        """
        Initialize the HTTP client and verify API access.

        Returns:
            True if initialization successful

        Raises:
            Tripo3DError: If API key is missing or invalid
        """
        if not self.api_key:
            raise Tripo3DError("TRIPO_API_KEY environment variable not set")

        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(self.timeout),
        )

        # Create download directory
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # Verify API access with a simple request
        try:
            response = await self._client.get("/task")
            if response.status_code == 401:
                raise Tripo3DError("Invalid API key", status_code=401)
            self._initialized = True
            logger.info("Tripo3D client initialized successfully")
            return True
        except httpx.RequestError as e:
            logger.warning(f"Could not verify Tripo3D API access: {e}")
            # Continue anyway - API might still work
            self._initialized = True
            return True

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
            self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure client is initialized."""
        if not self._initialized or not self._client:
            await self.initialize()

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: dict | None = None,
        **kwargs: Any,
    ) -> dict:
        """
        Make an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            json_data: JSON body data
            **kwargs: Additional request arguments

        Returns:
            Response JSON data

        Raises:
            Tripo3DError: If request fails after retries
        """
        await self._ensure_initialized()

        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await self._client.request(
                    method=method,
                    url=endpoint,
                    json=json_data,
                    **kwargs,
                )

                if response.status_code == 429:
                    # Rate limited - exponential backoff
                    wait_time = 2 ** (attempt + 1)
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                    await asyncio.sleep(wait_time)
                    continue

                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    raise Tripo3DError(
                        f"API error: {error_data.get('message', response.text)}",
                        status_code=response.status_code,
                        response=error_data,
                    )

                return response.json()

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.max_retries})")
                await asyncio.sleep(2 ** attempt)
            except httpx.RequestError as e:
                last_error = e
                logger.warning(f"Request error (attempt {attempt + 1}/{self.max_retries}): {e}")
                await asyncio.sleep(2 ** attempt)

        # Record error to ledger
        record_error(
            error_type="Tripo3DRequestError",
            message=f"Failed after {self.max_retries} retries: {last_error}",
            severity="HIGH",
            component="agent.modules.clothing.tripo3d_client",
            context={"endpoint": endpoint, "method": method},
            exception=last_error,
            action="continue",
        )

        raise Tripo3DError(f"Request failed after {self.max_retries} retries: {last_error}")

    async def text_to_3d(
        self,
        prompt: str,
        output_format: Model3DFormat = Model3DFormat.GLB,
        wait_for_completion: bool = True,
        texture: bool = True,
        pbr: bool = True,
    ) -> Model3DResult:
        """
        Generate a 3D model from text description.

        Uses Tripo3D's text-to-3D capability to create detailed 3D models
        from natural language descriptions.

        Args:
            prompt: Text description of the 3D model to generate
            output_format: Desired output format (GLB, FBX, OBJ)
            wait_for_completion: Wait for generation to complete
            texture: Generate with textures
            pbr: Use PBR (Physically Based Rendering) materials

        Returns:
            Model3DResult with generation status and model data

        Example:
            result = await client.text_to_3d(
                prompt="Black hoodie with embroidered rose, luxury fabric",
                output_format=Model3DFormat.GLB
            )
        """
        start_time = time.time()

        logger.info(f"Starting text-to-3D generation: {prompt[:50]}...")

        # Create generation task
        task_data = await self._request(
            "POST",
            "/task",
            json_data={
                "type": "text_to_model",
                "prompt": prompt,
                "model_version": "v2.0-20240919",
                "texture": texture,
                "pbr": pbr,
            },
        )

        task_id = task_data.get("data", {}).get("task_id", "")

        if not task_id:
            raise Tripo3DError("No task_id returned from API")

        logger.info(f"Created Tripo3D task: {task_id}")

        result = Model3DResult(
            task_id=task_id,
            status="queued",
            model_format=output_format,
            metadata={"prompt": prompt, "texture": texture, "pbr": pbr},
        )

        if wait_for_completion:
            result = await self._poll_task(task_id, output_format, start_time)

        return result

    async def image_to_3d(
        self,
        image_url: str | None = None,
        image_path: str | None = None,
        output_format: Model3DFormat = Model3DFormat.GLB,
        wait_for_completion: bool = True,
    ) -> Model3DResult:
        """
        Generate a 3D model from a reference image.

        Uses Tripo3D's image-to-3D capability to create 3D models
        that match the provided reference image.

        Args:
            image_url: URL to the reference image
            image_path: Local path to reference image
            output_format: Desired output format
            wait_for_completion: Wait for generation to complete

        Returns:
            Model3DResult with generation status and model data

        Raises:
            Tripo3DError: If neither image_url nor image_path provided
        """
        start_time = time.time()

        if not image_url and not image_path:
            raise Tripo3DError("Either image_url or image_path must be provided")

        # If local path, upload first
        if image_path and not image_url:
            image_url = await self._upload_image(image_path)

        logger.info(f"Starting image-to-3D generation from: {image_url[:50]}...")

        # Create generation task
        task_data = await self._request(
            "POST",
            "/task",
            json_data={
                "type": "image_to_model",
                "file": {"url": image_url},
                "model_version": "v2.0-20240919",
            },
        )

        task_id = task_data.get("data", {}).get("task_id", "")

        if not task_id:
            raise Tripo3DError("No task_id returned from API")

        logger.info(f"Created Tripo3D image task: {task_id}")

        result = Model3DResult(
            task_id=task_id,
            status="queued",
            model_format=output_format,
            metadata={"image_url": image_url},
        )

        if wait_for_completion:
            result = await self._poll_task(task_id, output_format, start_time)

        return result

    async def _upload_image(self, image_path: str) -> str:
        """
        Upload a local image to Tripo3D.

        Args:
            image_path: Local path to the image

        Returns:
            URL of the uploaded image
        """
        await self._ensure_initialized()

        path = Path(image_path)
        if not path.exists():
            raise Tripo3DError(f"Image not found: {image_path}")

        # Get upload token
        token_response = await self._request(
            "POST",
            "/upload",
            json_data={"file_type": path.suffix.lstrip(".")},
        )

        upload_url = token_response.get("data", {}).get("signed_url", "")
        file_token = token_response.get("data", {}).get("file_token", "")

        if not upload_url:
            raise Tripo3DError("Failed to get upload URL")

        # Upload the file
        async with httpx.AsyncClient() as client:
            with open(path, "rb") as f:
                response = await client.put(
                    upload_url,
                    content=f.read(),
                    headers={"Content-Type": f"image/{path.suffix.lstrip('.')}"},
                )
                if response.status_code not in (200, 201):
                    raise Tripo3DError(f"Failed to upload image: {response.text}")

        return file_token

    async def _poll_task(
        self,
        task_id: str,
        output_format: Model3DFormat,
        start_time: float,
    ) -> Model3DResult:
        """
        Poll task status until completion.

        Args:
            task_id: Tripo3D task ID
            output_format: Desired output format
            start_time: Task start time for duration tracking

        Returns:
            Model3DResult with final status
        """
        for attempt in range(self.MAX_POLL_ATTEMPTS):
            try:
                status_response = await self._request("GET", f"/task/{task_id}")
                task_data = status_response.get("data", {})
                status = task_data.get("status", "unknown")

                logger.debug(f"Task {task_id} status: {status}")

                if status == "success":
                    # Get the model download URL
                    model_data = task_data.get("output", {}).get("model", {})
                    model_url = model_data.get("url", "")
                    thumbnail_url = task_data.get("output", {}).get("rendered_image", {}).get("url", "")

                    # Download the model
                    local_path = None
                    if model_url:
                        local_path = await self._download_model(task_id, model_url, output_format)

                    generation_time = time.time() - start_time

                    return Model3DResult(
                        task_id=task_id,
                        status="success",
                        model_url=model_url,
                        model_format=output_format,
                        local_path=str(local_path) if local_path else None,
                        thumbnail_url=thumbnail_url,
                        generation_time_seconds=generation_time,
                        metadata=task_data,
                    )

                elif status == "failed":
                    error_msg = task_data.get("error", "Unknown error")
                    record_error(
                        error_type="Tripo3DGenerationFailed",
                        message=f"3D generation failed: {error_msg}",
                        severity="MEDIUM",
                        component="agent.modules.clothing.tripo3d_client",
                        context={"task_id": task_id, "error": error_msg},
                        action="continue",
                    )

                    return Model3DResult(
                        task_id=task_id,
                        status="failed",
                        model_format=output_format,
                        generation_time_seconds=time.time() - start_time,
                        metadata={"error": error_msg},
                    )

                # Still processing - wait and retry
                await asyncio.sleep(self.POLL_INTERVAL)

            except Tripo3DError:
                raise
            except Exception as e:
                logger.warning(f"Error polling task {task_id}: {e}")
                await asyncio.sleep(self.POLL_INTERVAL)

        # Timeout
        return Model3DResult(
            task_id=task_id,
            status="timeout",
            model_format=output_format,
            generation_time_seconds=time.time() - start_time,
            metadata={"error": "Polling timeout exceeded"},
        )

    async def _download_model(
        self,
        task_id: str,
        model_url: str,
        output_format: Model3DFormat,
    ) -> Path:
        """
        Download the generated 3D model.

        Args:
            task_id: Task ID for filename
            model_url: URL to download
            output_format: Model format for extension

        Returns:
            Path to downloaded file
        """
        filename = f"{task_id}.{output_format.value}"
        local_path = self.download_dir / filename

        async with httpx.AsyncClient() as client:
            response = await client.get(model_url, follow_redirects=True)
            response.raise_for_status()

            with open(local_path, "wb") as f:
                f.write(response.content)

        logger.info(f"Downloaded 3D model to: {local_path}")
        return local_path

    async def get_task_status(self, task_id: str) -> dict:
        """
        Get the status of a generation task.

        Args:
            task_id: Tripo3D task ID

        Returns:
            Task status data
        """
        response = await self._request("GET", f"/task/{task_id}")
        return response.get("data", {})

    async def convert_format(
        self,
        task_id: str,
        target_format: Model3DFormat,
    ) -> Model3DResult:
        """
        Convert an existing model to a different format.

        Args:
            task_id: Original task ID
            target_format: Target format

        Returns:
            Model3DResult with converted model
        """
        start_time = time.time()

        conversion_data = await self._request(
            "POST",
            "/task",
            json_data={
                "type": "convert_model",
                "original_model_task_id": task_id,
                "format": target_format.value.upper(),
            },
        )

        new_task_id = conversion_data.get("data", {}).get("task_id", "")
        return await self._poll_task(new_task_id, target_format, start_time)

    async def __aenter__(self) -> "Tripo3DClient":
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
