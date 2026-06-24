"""
scripts.flux_lora — FLUX LoRA training + inference package for SkyyRose brand.

Error hierarchy:
  FluxLoraError                 base
    DatasetError                dataset validation / loading failures
    RequiresConfirmationError   STOP-AND-SHOW gate: call raised when confirmed=False
    UserAbortError              user typed 'n' at confirmation prompt
    TrainingError               Replicate API / training job failures
"""


class FluxLoraError(Exception):
    """Base error for all flux_lora failures."""


class DatasetError(FluxLoraError):
    """Dataset validation or loading failure."""


class RequiresConfirmationError(FluxLoraError):
    """
    Raised when a paid Replicate call is attempted without confirmed=True.

    Callers must print a STOP-AND-SHOW manifest and receive explicit 'y'
    from the user before re-calling with confirmed=True.
    """


class UserAbortError(FluxLoraError):
    """Raised when the user declines the STOP-AND-SHOW confirmation."""


class TrainingError(FluxLoraError):
    """Replicate API error or training job failure."""
