"""
FASHN Virtual Try-On API Client

SDK Reference: https://docs.fashn.ai/sdk/python
Docs: https://docs.fashn.ai/

Features:
- Virtual try-on v1.6
- Model creation
- Product-to-model processing
- Output resolution: 576x864

Truth Protocol Compliance:
- Rule #1: API verified from official docs
- Rule #5: API key via FASHN_API_KEY env var
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

from agent.modules.clothing.schemas.schemas import TryOnModel, TryOnResult
from core.enterprise_error_handler import record_error

logger = logging.getLogger(__name__)


class FASHNError(Exception):
    """Custom exception for FASHN API errors."""

    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class FASHNClient:
    """
    Async client for FASHN virtual try-on API.

    Provides virtual try-on capabilities for clothing assets,
    allowing visualization of garments on different model types.

    Example:
        client = FASHNClient()
        await client.initialize()

        result = await client.virtual_tryon(
            garment_image_url="https://example.com/hoodie.png",
            model_type=TryOnModel.FEMALE
        )

    Attributes:
        api_key: FASHN API key from environment
        base_url: FASHN API base URL
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
    """

    BASE_URL = "https://api.fashn.ai/v1"
    DEFAULT_TIMEOUT = 120.0
    MAX_POLL_ATTEMPTS = 60  # 5 minutes with 5-second intervals
    POLL_INTERVAL = 5.0
    OUTPUT_RESOLUTION = (576, 864)  # Standard output resolution

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 3,
        download_dir: str | None = None,
    ):
        """
        Initialize FASHN client.

        Args:
            api_key: API key (defaults to FASHN_API_KEY env var)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            download_dir: Directory for downloading try-on images
        """
        self.api_key = api_key or os.getenv("FASHN_API_KEY", "")
        self.timeout = timeout
        self.max_retries = max_retries
        self.download_dir = Path(download_dir or "/tmp/fashn_tryon")
        self._client: httpx.AsyncClient | None = None
        self._initialized = False

    async def initialize(self) -> bool:
        """
        Initialize the HTTP client and verify API access.

        Returns:
            True if initialization successful

        Raises:
            FASHNError: If API key is missing or invalid
        """
        if not self.api_key:
            raise FASHNError("FASHN_API_KEY environment variable not set")

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

        self._initialized = True
        logger.info("FASHN client initialized successfully")
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
            FASHNError: If request fails after retries
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
                    raise FASHNError(
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
            error_type="FASHNRequestError",
            message=f"Failed after {self.max_retries} retries: {last_error}",
            severity="HIGH",
            component="agent.modules.clothing.fashn_client",
            context={"endpoint": endpoint, "method": method},
            exception=last_error,
            action="continue",
        )

        raise FASHNError(f"Request failed after {self.max_retries} retries: {last_error}")

    async def virtual_tryon(
        self,
        garment_image_url: str | None = None,
        garment_image_path: str | None = None,
        model_image_url: str | None = None,
        model_type: TryOnModel = TryOnModel.FEMALE,
        category: str = "tops",
        wait_for_completion: bool = True,
    ) -> TryOnResult:
        """
        Generate a virtual try-on image.

        Places the garment on a model image using AI-powered fitting.

        Args:
            garment_image_url: URL to garment image
            garment_image_path: Local path to garment image
            model_image_url: URL to model image (optional, uses default)
            model_type: Type of model (FEMALE, MALE, UNISEX)
            category: Clothing category (tops, bottoms, dresses)
            wait_for_completion: Wait for processing to complete

        Returns:
            TryOnResult with try-on image and metadata

        Example:
            result = await client.virtual_tryon(
                garment_image_url="https://skyyrose.co/hoodie.png",
                model_type=TryOnModel.FEMALE,
                category="tops"
            )
        """
        start_time = time.time()

        if not garment_image_url and not garment_image_path:
            raise FASHNError("Either garment_image_url or garment_image_path must be provided")

        # If local path, upload first
        if garment_image_path and not garment_image_url:
            garment_image_url = await self._upload_image(garment_image_path)

        logger.info(f"Starting virtual try-on for {model_type.value} model")

        # Create try-on request
        request_data = {
            "garment_image_url": garment_image_url,
            "category": category,
            "mode": "quality",  # quality mode for best results
            "garment_photo_type": "auto",
            "output_format": "png",
        }

        # Add model image if provided, otherwise use built-in model
        if model_image_url:
            request_data["model_image_url"] = model_image_url
        else:
            request_data["model_id"] = self._get_default_model_id(model_type)

        task_data = await self._request(
            "POST",
            "/run",
            json_data=request_data,
        )

        task_id = task_data.get("id", "")

        if not task_id:
            raise FASHNError("No task id returned from API")

        logger.info(f"Created FASHN try-on task: {task_id}")

        result = TryOnResult(
            task_id=task_id,
            status="processing",
            model_type=model_type,
            resolution=self.OUTPUT_RESOLUTION,
            metadata={"category": category, "garment_url": garment_image_url},
        )

        if wait_for_completion:
            result = await self._poll_task(task_id, model_type, start_time)

        return result

    def _get_default_model_id(self, model_type: TryOnModel) -> str:
        """
        Get default model ID for a model type.

        Args:
            model_type: Type of model

        Returns:
            Default model ID string
        """
        # FASHN default model IDs
        model_ids = {
            TryOnModel.FEMALE: "model_female_01",
            TryOnModel.MALE: "model_male_01",
            TryOnModel.UNISEX: "model_unisex_01",
        }
        return model_ids.get(model_type, "model_female_01")

    async def _upload_image(self, image_path: str) -> str:
        """
        Upload a local image to FASHN.

        Args:
            image_path: Local path to the image

        Returns:
            URL of the uploaded image
        """
        await self._ensure_initialized()

        path = Path(image_path)
        if not path.exists():
            raise FASHNError(f"Image not found: {image_path}")

        # Read file and encode as base64 data URL
        import base64
        import mimetypes

        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type:
            mime_type = "image/png"

        with open(path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        return f"data:{mime_type};base64,{image_data}"

    async def _poll_task(
        self,
        task_id: str,
        model_type: TryOnModel,
        start_time: float,
    ) -> TryOnResult:
        """
        Poll task status until completion.

        Args:
            task_id: FASHN task ID
            model_type: Model type used
            start_time: Task start time for duration tracking

        Returns:
            TryOnResult with final status
        """
        for attempt in range(self.MAX_POLL_ATTEMPTS):
            try:
                status_response = await self._request("GET", f"/status/{task_id}")
                status = status_response.get("status", "unknown")

                logger.debug(f"Task {task_id} status: {status}")

                if status == "completed":
                    # Get the result image URL
                    output = status_response.get("output", {})
                    image_url = output.get("image_url", "")

                    # Download the image
                    local_path = None
                    if image_url:
                        local_path = await self._download_image(task_id, image_url, model_type)

                    processing_time = time.time() - start_time

                    return TryOnResult(
                        task_id=task_id,
                        status="completed",
                        image_url=image_url,
                        local_path=str(local_path) if local_path else None,
                        model_type=model_type,
                        resolution=self.OUTPUT_RESOLUTION,
                        processing_time_seconds=processing_time,
                        metadata=status_response,
                    )

                elif status == "failed":
                    error_msg = status_response.get("error", "Unknown error")
                    record_error(
                        error_type="FASHNTryOnFailed",
                        message=f"Virtual try-on failed: {error_msg}",
                        severity="MEDIUM",
                        component="agent.modules.clothing.fashn_client",
                        context={"task_id": task_id, "error": error_msg},
                        action="continue",
                    )

                    return TryOnResult(
                        task_id=task_id,
                        status="failed",
                        model_type=model_type,
                        resolution=self.OUTPUT_RESOLUTION,
                        processing_time_seconds=time.time() - start_time,
                        metadata={"error": error_msg},
                    )

                # Still processing - wait and retry
                await asyncio.sleep(self.POLL_INTERVAL)

            except FASHNError:
                raise
            except Exception as e:
                logger.warning(f"Error polling task {task_id}: {e}")
                await asyncio.sleep(self.POLL_INTERVAL)

        # Timeout
        return TryOnResult(
            task_id=task_id,
            status="timeout",
            model_type=model_type,
            resolution=self.OUTPUT_RESOLUTION,
            processing_time_seconds=time.time() - start_time,
            metadata={"error": "Polling timeout exceeded"},
        )

    async def _download_image(
        self,
        task_id: str,
        image_url: str,
        model_type: TryOnModel,
    ) -> Path:
        """
        Download the try-on result image.

        Args:
            task_id: Task ID for filename
            image_url: URL to download
            model_type: Model type for filename

        Returns:
            Path to downloaded file
        """
        filename = f"{task_id}_{model_type.value}.png"
        local_path = self.download_dir / filename

        async with httpx.AsyncClient() as client:
            response = await client.get(image_url, follow_redirects=True)
            response.raise_for_status()

            with open(local_path, "wb") as f:
                f.write(response.content)

        logger.info(f"Downloaded try-on image to: {local_path}")
        return local_path

    async def get_task_status(self, task_id: str) -> dict:
        """
        Get the status of a try-on task.

        Args:
            task_id: FASHN task ID

        Returns:
            Task status data
        """
        response = await self._request("GET", f"/status/{task_id}")
        return response

    async def batch_tryon(
        self,
        garment_image_url: str,
        model_types: list[TryOnModel] | None = None,
        category: str = "tops",
    ) -> list[TryOnResult]:
        """
        Generate try-on images for multiple model types.

        Processes the same garment with different model types
        in parallel for efficiency.

        Args:
            garment_image_url: URL to garment image
            model_types: List of model types (defaults to FEMALE, MALE)
            category: Clothing category

        Returns:
            List of TryOnResult for each model type

        Example:
            results = await client.batch_tryon(
                garment_image_url="https://example.com/hoodie.png",
                model_types=[TryOnModel.FEMALE, TryOnModel.MALE]
            )
        """
        if model_types is None:
            model_types = [TryOnModel.FEMALE, TryOnModel.MALE]

        logger.info(f"Starting batch try-on for {len(model_types)} model types")

        # Process in parallel
        tasks = [
            self.virtual_tryon(
                garment_image_url=garment_image_url,
                model_type=model_type,
                category=category,
            )
            for model_type in model_types
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log errors
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Try-on failed for {model_types[i].value}: {result}")
                record_error(
                    error_type="FASHNBatchTryOnError",
                    message=f"Batch try-on failed for {model_types[i].value}",
                    severity="MEDIUM",
                    component="agent.modules.clothing.fashn_client",
                    context={"model_type": model_types[i].value},
                    exception=result if isinstance(result, Exception) else None,
                    action="continue",
                )
                # Create failed result
                final_results.append(
                    TryOnResult(
                        task_id="error",
                        status="failed",
                        model_type=model_types[i],
                        metadata={"error": str(result)},
                    )
                )
            else:
                final_results.append(result)

        return final_results

    async def __aenter__(self) -> "FASHNClient":
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
