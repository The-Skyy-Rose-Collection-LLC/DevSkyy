"""FastAPI surface for the clothing 3D pipeline.

Mount this router in ``main_enterprise.py``:

.. code-block:: python

    from api.v1.clothing_3d.router import router as clothing_3d_router
    app.include_router(clothing_3d_router, prefix="/v1/clothing-3d")
"""

from api.v1.clothing_3d.router import router

__all__ = ["router"]
