# DevSkyy Docstring Style Guide

## Overview

This guide defines the docstring standards for the DevSkyy Enterprise Platform. We use **Google-style docstrings** for consistency and readability.

## Why Docstrings Matter

- **Self-documenting code**: Clear understanding without reading implementation
- **IDE support**: Better autocomplete and inline help
- **API documentation**: Automatic generation of API docs
- **Maintainability**: Easier for new developers to understand code
- **Testing**: Better understanding of expected behavior

## Google-Style Docstrings

### Module Docstrings

Every Python module should have a docstring at the top:

```python
"""Module for handling product management and inventory operations.

This module provides classes and functions for managing e-commerce products,
including CRUD operations, inventory tracking, and ML-powered recommendations.

Example:
    Basic usage of the ProductManager class:

        from agent.ecommerce.product_manager import ProductManager

        manager = ProductManager()
        product = await manager.create_product({
            "name": "Silk Dress",
            "price": 299.99
        })

Attributes:
    MAX_FILE_SIZE (int): Maximum allowed file size in bytes
    UPLOAD_DIR (Path): Directory for file uploads
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_DIR = Path("uploads")
```

### Class Docstrings

Every class must have a docstring describing its purpose and usage:

```python
class ProductManager:
    """Manages product operations with ML-powered enhancements.

    This class provides comprehensive product management capabilities including
    creation, updates, deletion, and ML-powered features like automated
    description generation and price optimization.

    Attributes:
        db: Database connection instance
        ml_engine: Machine learning engine for product enhancements
        cache: Redis cache instance for performance optimization

    Example:
        Creating and managing products:

            manager = ProductManager()
            product = await manager.create_product({
                "name": "Luxury Handbag",
                "price": 599.99,
                "category": "accessories"
            })

            # Update product
            await manager.update_product(
                product_id=product.id,
                updates={"price": 549.99}
            )
    """

    def __init__(self, db=None, ml_engine=None):
        """Initialize the ProductManager.

        Args:
            db: Database connection instance. If None, uses default connection.
            ml_engine: ML engine instance. If None, creates new instance.
        """
        self.db = db or get_database()
        self.ml_engine = ml_engine or MLEngine()
        self.cache = RedisCache()
```

### Function/Method Docstrings

All public functions and methods must have docstrings:

```python
async def create_product(
    self,
    product_data: Dict[str, Any],
    auto_generate: bool = True
) -> Dict[str, Any]:
    """Create a new product with optional ML enhancements.

    Creates a product in the database and optionally applies ML-powered
    enhancements like automated description generation, SEO optimization,
    and price recommendations.

    Args:
        product_data: Dictionary containing product information. Required keys:
            - name (str): Product name
            - price (float): Product price
            Optional keys:
            - description (str): Product description
            - category (str): Product category
            - material (str): Product material
        auto_generate: If True, uses ML to generate missing fields like
            description and SEO metadata. Defaults to True.

    Returns:
        Dictionary containing the created product with all fields including:
            - product_id (str): Unique product identifier
            - name (str): Product name
            - price (float): Product price
            - description (str): Product description (generated if not provided)
            - seo (dict): SEO metadata
            - created_at (datetime): Creation timestamp

    Raises:
        ValueError: If required fields are missing in product_data
        DatabaseError: If database operation fails
        MLGenerationError: If ML enhancement fails and auto_generate is True

    Example:
        >>> manager = ProductManager()
        >>> product = await manager.create_product({
        ...     "name": "Silk Evening Dress",
        ...     "price": 299.99,
        ...     "material": "silk"
        ... })
        >>> print(product["product_id"])
        'PROD-12345'
    """
    # Validate required fields
    if not product_data.get("name"):
        raise ValueError("Product name is required")

    # Implementation...
    return created_product
```

### Property Docstrings

Properties should have concise docstrings:

```python
@property
def total_products(self) -> int:
    """Get the total number of products in the database.

    Returns:
        Total count of active products.
    """
    return self.db.products.count()

@property
def average_price(self) -> float:
    """Calculate the average price across all products.

    Returns:
        Average product price as a float.
    """
    return sum(p.price for p in self.products) / len(self.products)
```

## Docstring Sections

### Args Section

Document all function parameters:

```python
Args:
    user_id (str): Unique identifier for the user
    include_deleted (bool, optional): Whether to include deleted items.
        Defaults to False.
    limit (int, optional): Maximum number of results to return.
        Defaults to 100.
    filters (dict, optional): Additional filter criteria. Supported keys:
        - category (str): Filter by category
        - min_price (float): Minimum price
        - max_price (float): Maximum price
```

### Returns Section

Describe what the function returns:

```python
Returns:
    List[Dict[str, Any]]: List of product dictionaries, each containing:
        - product_id (str): Unique identifier
        - name (str): Product name
        - price (float): Product price
        - in_stock (bool): Availability status

# For simple returns
Returns:
    str: The generated product ID

# For multiple return values
Returns:
    tuple: A tuple containing:
        - success (bool): Whether operation succeeded
        - message (str): Success or error message
        - data (dict): Operation result data
```

### Raises Section

Document all exceptions that may be raised:

```python
Raises:
    ValueError: If the product_id is invalid or empty
    ProductNotFoundError: If the product doesn't exist in database
    PermissionError: If user lacks permission to perform operation
    DatabaseError: If database operation fails unexpectedly
```

### Example Section

Provide usage examples:

```python
Example:
    Basic usage:

        >>> manager = ProductManager()
        >>> result = await manager.delete_product("PROD-123")
        >>> print(result["success"])
        True

    Advanced usage with error handling:

        >>> try:
        ...     result = await manager.delete_product("INVALID-ID")
        ... except ProductNotFoundError:
        ...     print("Product not found")
        Product not found
```

### Notes Section

Add important notes or warnings:

```python
Note:
    This operation is irreversible. Consider using soft delete by setting
    the `active` field to False instead of permanent deletion.

Warning:
    This function makes external API calls which may be slow. Consider
    using the cached version `get_cached_recommendations()` for better
    performance.
```

## Type Hints

Always use type hints with docstrings:

```python
from typing import List, Dict, Optional, Union, Any

async def search_products(
    query: str,
    category: Optional[str] = None,
    max_results: int = 20
) -> List[Dict[str, Any]]:
    """Search for products matching the query.

    Args:
        query: Search query string
        category: Optional category filter
        max_results: Maximum number of results

    Returns:
        List of matching products
    """
    pass
```

## Special Cases

### Private Functions

Private functions (starting with `_`) should have brief docstrings:

```python
def _validate_product_data(self, data: Dict) -> bool:
    """Validate product data structure and required fields.

    Args:
        data: Product data dictionary to validate

    Returns:
        True if valid, False otherwise
    """
    pass
```

### Async Functions

Document async functions the same way, but mention async behavior if important:

```python
async def fetch_external_data(self, url: str) -> Dict:
    """Fetch data from external API asynchronously.

    Note:
        This is an async function and must be awaited.

    Args:
        url: API endpoint URL

    Returns:
        Parsed JSON response as dictionary
    """
    pass
```

### Generator Functions

Document generators with yield information:

```python
def batch_products(
    self,
    batch_size: int = 100
) -> Generator[List[Dict], None, None]:
    """Generate batches of products for processing.

    Args:
        batch_size: Number of products per batch

    Yields:
        List of product dictionaries of size batch_size (or less for final batch)

    Example:
        >>> for batch in manager.batch_products(batch_size=50):
        ...     process_batch(batch)
    """
    pass
```

### Decorators

Document decorators clearly:

```python
def require_auth(permissions: List[str]):
    """Decorator to require authentication and specific permissions.

    Args:
        permissions: List of required permission strings

    Returns:
        Decorated function that checks authentication and permissions

    Example:
        >>> @require_auth(["products.write", "products.delete"])
        ... async def delete_product(product_id: str):
        ...     # Function implementation
        ...     pass
    """
    def decorator(func):
        # Implementation
        return func
    return decorator
```

## Tools for Checking Docstrings

### pydocstyle

Check docstring compliance:

```bash
# Install
pip install pydocstyle

# Run check
pydocstyle agent/ api/ ml/
```

### interrogate

Measure docstring coverage:

```bash
# Install
pip install interrogate

# Run check
interrogate -v agent/ api/ ml/
```

### darglint

Validate that docstrings match function signatures:

```bash
# Install
pip install darglint

# Run check
darglint agent/ api/ ml/
```

## Integration with IDE

### VS Code

1. Install Python extension
2. Configure in `.vscode/settings.json`:

```json
{
    "python.linting.pydocstyleEnabled": true,
    "autoDocstring.docstringFormat": "google",
    "autoDocstring.startOnNewLine": false
}
```

### PyCharm

1. Go to Settings → Tools → Python Integrated Tools
2. Set Docstring format to "Google"
3. Enable docstring generation on function creation

## Quick Templates

### Basic Function

```python
def function_name(param1: str, param2: int = 0) -> bool:
    """Brief description of what the function does.

    Args:
        param1: Description of param1
        param2: Description of param2. Defaults to 0.

    Returns:
        Description of return value
    """
    pass
```

### Async Function with Exceptions

```python
async def async_function(
    param: str,
    options: Optional[Dict] = None
) -> Dict[str, Any]:
    """Brief description.

    Longer description with more details about the function's behavior
    and any important notes about its usage.

    Args:
        param: Description
        options: Optional configuration. Defaults to None.

    Returns:
        Dictionary containing:
            - key1 (type): Description
            - key2 (type): Description

    Raises:
        ValueError: Description of when this is raised
        CustomError: Description of when this is raised
    """
    pass
```

## Best Practices

1. **Start with a one-line summary** - First line should be a brief summary
2. **Use present tense** - "Returns" not "Will return"
3. **Be specific** - Describe types, formats, and constraints
4. **Include examples** - Show actual usage when helpful
5. **Keep updated** - Update docstrings when code changes
6. **Be consistent** - Use the same style throughout the codebase
7. **Avoid redundancy** - Don't repeat what's obvious from the code
8. **Document edge cases** - Mention special behavior or edge cases

## Anti-Patterns to Avoid

### ❌ Too Vague

```python
def process_data(data):
    """Process the data."""
    pass
```

### ✅ Specific and Clear

```python
def process_data(data: List[Dict]) -> List[Dict]:
    """Validate and normalize product data for database insertion.

    Args:
        data: List of raw product dictionaries from CSV import

    Returns:
        List of validated and normalized product dictionaries
    """
    pass
```

### ❌ Outdated

```python
def calculate_total(items):
    """Calculate total price (includes tax)."""  # Tax removed months ago!
    return sum(item.price for item in items)
```

### ✅ Current

```python
def calculate_total(items: List[Item]) -> float:
    """Calculate total price of items (excluding tax).

    Note:
        Tax calculation was moved to checkout process in v2.0

    Args:
        items: List of cart items

    Returns:
        Total price as float
    """
    return sum(item.price for item in items)
```

---

**Last Updated**: 2025-11-11  
**Version**: 1.0  
**Reference**: [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
