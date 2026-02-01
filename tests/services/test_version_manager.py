# tests/services/test_version_manager.py
"""Tests for AssetVersionManager service.

Implements US-023: Asset versioning with retention policies.

Author: DevSkyy Platform Team
"""

from unittest.mock import MagicMock

import pytest

from services.storage import (
    AssetNotFoundError,
    AssetVersionManager,
    CreateVersionRequest,
    RetentionPolicy,
    RevertVersionRequest,
    UpdateRetentionRequest,
    VersioningError,
    VersionNotFoundError,
    VersionStatus,
)


@pytest.fixture
def mock_r2_client() -> MagicMock:
    """Create a mock R2 client."""
    client = MagicMock()
    client.delete_object = MagicMock()
    return client


@pytest.fixture
def version_manager(mock_r2_client: MagicMock) -> AssetVersionManager:
    """Create version manager for testing."""
    return AssetVersionManager(r2_client=mock_r2_client)


class TestAssetCreation:
    """Tests for asset creation."""

    @pytest.mark.asyncio
    async def test_create_asset(self, version_manager: AssetVersionManager) -> None:
        """Should create a new asset with default values."""
        asset = await version_manager.create_asset(
            name="test_image.jpg",
            category="original",
        )

        assert asset.name == "test_image.jpg"
        assert asset.category == "original"
        assert asset.current_version == 0
        assert asset.total_versions == 0
        assert asset.retention_policy == RetentionPolicy.KEEP_ALL
        assert asset.retention_value is None

    @pytest.mark.asyncio
    async def test_create_asset_with_product_id(self, version_manager: AssetVersionManager) -> None:
        """Should create asset linked to a product."""
        asset = await version_manager.create_asset(
            name="product_image.jpg",
            category="enhanced",
            product_id="prod_123",
        )

        assert asset.product_id == "prod_123"

    @pytest.mark.asyncio
    async def test_create_asset_with_retention_policy(
        self, version_manager: AssetVersionManager
    ) -> None:
        """Should create asset with custom retention policy."""
        asset = await version_manager.create_asset(
            name="temp_image.jpg",
            category="processed",
            retention_policy=RetentionPolicy.KEEP_LAST_N,
            retention_value=5,
        )

        assert asset.retention_policy == RetentionPolicy.KEEP_LAST_N
        assert asset.retention_value == 5


class TestVersionCreation:
    """Tests for version creation."""

    @pytest.mark.asyncio
    async def test_create_first_version(self, version_manager: AssetVersionManager) -> None:
        """First version should be marked as original."""
        asset = await version_manager.create_asset(
            name="image.jpg",
            category="original",
        )

        version = await version_manager.create_version(
            CreateVersionRequest(
                asset_id=asset.asset_id,
                content_hash="sha256_abc123",
                r2_key=f"versioned/{asset.asset_id}/v1/image.jpg",
                file_size_bytes=1024,
                mime_type="image/jpeg",
            )
        )

        assert version.version_number == 1
        assert version.is_original is True
        assert version.is_current is True
        assert version.status == VersionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_create_second_version(self, version_manager: AssetVersionManager) -> None:
        """Second version should archive the first."""
        asset = await version_manager.create_asset(
            name="image.jpg",
            category="original",
        )

        # Create v1
        v1 = await version_manager.create_version(
            CreateVersionRequest(
                asset_id=asset.asset_id,
                content_hash="sha256_v1",
                r2_key=f"versioned/{asset.asset_id}/v1/image.jpg",
                file_size_bytes=1024,
            )
        )

        # Create v2
        v2 = await version_manager.create_version(
            CreateVersionRequest(
                asset_id=asset.asset_id,
                content_hash="sha256_v2",
                r2_key=f"versioned/{asset.asset_id}/v2/image.jpg",
                file_size_bytes=2048,
                change_description="Enhanced lighting",
            )
        )

        assert v2.version_number == 2
        assert v2.is_original is False
        assert v2.is_current is True
        assert v2.change_description == "Enhanced lighting"

        # Verify v1 is now archived
        v1_updated = await version_manager.get_version(asset.asset_id, 1)
        assert v1_updated.is_current is False
        assert v1_updated.status == VersionStatus.ARCHIVED

    @pytest.mark.asyncio
    async def test_create_version_nonexistent_asset(
        self, version_manager: AssetVersionManager
    ) -> None:
        """Should raise error for nonexistent asset."""
        with pytest.raises(AssetNotFoundError):
            await version_manager.create_version(
                CreateVersionRequest(
                    asset_id="nonexistent_id",
                    content_hash="sha256_abc",
                    r2_key="versioned/nonexistent/v1/image.jpg",
                    file_size_bytes=1024,
                )
            )


class TestVersionRetrieval:
    """Tests for version retrieval."""

    @pytest.mark.asyncio
    async def test_get_version(self, version_manager: AssetVersionManager) -> None:
        """Should retrieve specific version."""
        asset = await version_manager.create_asset(name="test.jpg", category="original")
        await version_manager.create_version(
            CreateVersionRequest(
                asset_id=asset.asset_id,
                content_hash="sha256_abc",
                r2_key=f"versioned/{asset.asset_id}/v1/test.jpg",
                file_size_bytes=1024,
            )
        )

        version = await version_manager.get_version(asset.asset_id, 1)

        assert version.version_number == 1
        assert version.content_hash == "sha256_abc"

    @pytest.mark.asyncio
    async def test_get_nonexistent_version(self, version_manager: AssetVersionManager) -> None:
        """Should raise error for nonexistent version."""
        asset = await version_manager.create_asset(name="test.jpg", category="original")
        await version_manager.create_version(
            CreateVersionRequest(
                asset_id=asset.asset_id,
                content_hash="sha256_abc",
                r2_key=f"versioned/{asset.asset_id}/v1/test.jpg",
                file_size_bytes=1024,
            )
        )

        with pytest.raises(VersionNotFoundError):
            await version_manager.get_version(asset.asset_id, 99)

    @pytest.mark.asyncio
    async def test_list_versions(self, version_manager: AssetVersionManager) -> None:
        """Should list all versions."""
        asset = await version_manager.create_asset(name="test.jpg", category="original")

        # Create 3 versions
        for i in range(1, 4):
            await version_manager.create_version(
                CreateVersionRequest(
                    asset_id=asset.asset_id,
                    content_hash=f"sha256_v{i}",
                    r2_key=f"versioned/{asset.asset_id}/v{i}/test.jpg",
                    file_size_bytes=1024 * i,
                )
            )

        response = await version_manager.list_versions(asset.asset_id)

        assert response.total == 3
        assert response.current_version == 3
        assert len(response.versions) == 3
        # Should be sorted newest first
        assert response.versions[0].version_number == 3

    @pytest.mark.asyncio
    async def test_list_versions_excludes_deleted(
        self, version_manager: AssetVersionManager
    ) -> None:
        """Should exclude deleted versions by default."""
        asset = await version_manager.create_asset(name="test.jpg", category="original")

        # Create 2 versions
        for i in range(1, 3):
            await version_manager.create_version(
                CreateVersionRequest(
                    asset_id=asset.asset_id,
                    content_hash=f"sha256_v{i}",
                    r2_key=f"versioned/{asset.asset_id}/v{i}/test.jpg",
                    file_size_bytes=1024,
                )
            )

        # Mark v1 for deletion (not original since it's now v2)
        # Actually, let's create v3 and mark v2 for deletion
        await version_manager.create_version(
            CreateVersionRequest(
                asset_id=asset.asset_id,
                content_hash="sha256_v3",
                r2_key=f"versioned/{asset.asset_id}/v3/test.jpg",
                file_size_bytes=1024,
            )
        )
        await version_manager.delete_version(asset.asset_id, 2)

        # Default excludes deleted
        response = await version_manager.list_versions(asset.asset_id)
        assert response.total == 2

        # Include deleted
        response_all = await version_manager.list_versions(asset.asset_id, include_deleted=True)
        assert response_all.total == 3


class TestVersionRevert:
    """Tests for version revert functionality."""

    @pytest.mark.asyncio
    async def test_revert_creates_new_version(self, version_manager: AssetVersionManager) -> None:
        """Revert should create a new version with old content."""
        asset = await version_manager.create_asset(name="test.jpg", category="original")

        # Create v1 and v2
        await version_manager.create_version(
            CreateVersionRequest(
                asset_id=asset.asset_id,
                content_hash="sha256_original",
                r2_key=f"versioned/{asset.asset_id}/v1/test.jpg",
                file_size_bytes=1024,
            )
        )
        await version_manager.create_version(
            CreateVersionRequest(
                asset_id=asset.asset_id,
                content_hash="sha256_modified",
                r2_key=f"versioned/{asset.asset_id}/v2/test.jpg",
                file_size_bytes=2048,
            )
        )

        # Revert to v1
        reverted = await version_manager.revert_version(
            RevertVersionRequest(
                asset_id=asset.asset_id,
                target_version=1,
                create_new_version=True,
            )
        )

        assert reverted.version_number == 3  # New version created
        assert reverted.content_hash == "sha256_original"  # Same content as v1
        assert reverted.source_version == 1
        assert "Reverted to version 1" in reverted.change_description

    @pytest.mark.asyncio
    async def test_revert_pointer_only(self, version_manager: AssetVersionManager) -> None:
        """Revert with create_new_version=False should just update pointer."""
        asset = await version_manager.create_asset(name="test.jpg", category="original")

        # Create v1 and v2
        await version_manager.create_version(
            CreateVersionRequest(
                asset_id=asset.asset_id,
                content_hash="sha256_v1",
                r2_key=f"versioned/{asset.asset_id}/v1/test.jpg",
                file_size_bytes=1024,
            )
        )
        await version_manager.create_version(
            CreateVersionRequest(
                asset_id=asset.asset_id,
                content_hash="sha256_v2",
                r2_key=f"versioned/{asset.asset_id}/v2/test.jpg",
                file_size_bytes=2048,
            )
        )

        # Revert pointer only
        reverted = await version_manager.revert_version(
            RevertVersionRequest(
                asset_id=asset.asset_id,
                target_version=1,
                create_new_version=False,
            )
        )

        assert reverted.version_number == 1
        asset_info = await version_manager.get_asset(asset.asset_id)
        assert asset_info.current_version == 1

    @pytest.mark.asyncio
    async def test_revert_nonexistent_version(self, version_manager: AssetVersionManager) -> None:
        """Should raise error when reverting to nonexistent version."""
        asset = await version_manager.create_asset(name="test.jpg", category="original")
        await version_manager.create_version(
            CreateVersionRequest(
                asset_id=asset.asset_id,
                content_hash="sha256_v1",
                r2_key=f"versioned/{asset.asset_id}/v1/test.jpg",
                file_size_bytes=1024,
            )
        )

        with pytest.raises(VersionNotFoundError):
            await version_manager.revert_version(
                RevertVersionRequest(
                    asset_id=asset.asset_id,
                    target_version=99,
                )
            )


class TestVersionDeletion:
    """Tests for version deletion."""

    @pytest.mark.asyncio
    async def test_delete_version(self, version_manager: AssetVersionManager) -> None:
        """Should mark version as pending delete."""
        asset = await version_manager.create_asset(name="test.jpg", category="original")

        # Create multiple versions
        for i in range(1, 4):
            await version_manager.create_version(
                CreateVersionRequest(
                    asset_id=asset.asset_id,
                    content_hash=f"sha256_v{i}",
                    r2_key=f"versioned/{asset.asset_id}/v{i}/test.jpg",
                    file_size_bytes=1024,
                )
            )

        # Delete v2
        await version_manager.delete_version(asset.asset_id, 2)

        v2 = await version_manager.get_version(asset.asset_id, 2)
        assert v2.status == VersionStatus.PENDING_DELETE

    @pytest.mark.asyncio
    async def test_cannot_delete_original(self, version_manager: AssetVersionManager) -> None:
        """Should not allow deleting original version."""
        asset = await version_manager.create_asset(name="test.jpg", category="original")
        await version_manager.create_version(
            CreateVersionRequest(
                asset_id=asset.asset_id,
                content_hash="sha256_v1",
                r2_key=f"versioned/{asset.asset_id}/v1/test.jpg",
                file_size_bytes=1024,
            )
        )

        with pytest.raises(VersioningError) as exc_info:
            await version_manager.delete_version(asset.asset_id, 1)

        assert "original version" in str(exc_info.value).lower()


class TestRetentionPolicies:
    """Tests for retention policy functionality."""

    @pytest.mark.asyncio
    async def test_update_retention_keep_last_n(self, version_manager: AssetVersionManager) -> None:
        """Should update to KEEP_LAST_N policy."""
        asset = await version_manager.create_asset(name="test.jpg", category="original")

        updated = await version_manager.update_retention(
            UpdateRetentionRequest(
                asset_id=asset.asset_id,
                policy=RetentionPolicy.KEEP_LAST_N,
                value=3,
            )
        )

        assert updated.retention_policy == RetentionPolicy.KEEP_LAST_N
        assert updated.retention_value == 3

    @pytest.mark.asyncio
    async def test_retention_keep_last_n_requires_value(
        self, version_manager: AssetVersionManager
    ) -> None:
        """KEEP_LAST_N requires a value."""
        asset = await version_manager.create_asset(name="test.jpg", category="original")

        with pytest.raises(VersioningError):
            await version_manager.update_retention(
                UpdateRetentionRequest(
                    asset_id=asset.asset_id,
                    policy=RetentionPolicy.KEEP_LAST_N,
                    value=None,
                )
            )

    @pytest.mark.asyncio
    async def test_retention_marks_old_versions(self, version_manager: AssetVersionManager) -> None:
        """Retention policy should mark old versions for deletion."""
        asset = await version_manager.create_asset(
            name="test.jpg",
            category="original",
            retention_policy=RetentionPolicy.KEEP_LAST_N,
            retention_value=2,
        )

        # Create 4 versions
        for i in range(1, 5):
            await version_manager.create_version(
                CreateVersionRequest(
                    asset_id=asset.asset_id,
                    content_hash=f"sha256_v{i}",
                    r2_key=f"versioned/{asset.asset_id}/v{i}/test.jpg",
                    file_size_bytes=1024,
                )
            )

        # Check that v2 is marked for deletion (v1 is original, preserved)
        v2 = await version_manager.get_version(asset.asset_id, 2)
        assert v2.status == VersionStatus.PENDING_DELETE

        # v1 should be preserved (original)
        v1 = await version_manager.get_version(asset.asset_id, 1)
        assert v1.status != VersionStatus.PENDING_DELETE


class TestCleanup:
    """Tests for version cleanup."""

    @pytest.mark.asyncio
    async def test_cleanup_removes_pending_delete(
        self, version_manager: AssetVersionManager, mock_r2_client: MagicMock
    ) -> None:
        """Cleanup should remove versions marked for deletion."""
        asset = await version_manager.create_asset(name="test.jpg", category="original")

        # Create versions
        for i in range(1, 4):
            await version_manager.create_version(
                CreateVersionRequest(
                    asset_id=asset.asset_id,
                    content_hash=f"sha256_v{i}",
                    r2_key=f"versioned/{asset.asset_id}/v{i}/test.jpg",
                    file_size_bytes=1024,
                )
            )

        # Mark v2 for deletion
        await version_manager.delete_version(asset.asset_id, 2)

        # Run cleanup
        results = await version_manager.cleanup_deleted_versions()

        assert asset.asset_id in results
        assert results[asset.asset_id].versions_deleted == 1
        mock_r2_client.delete_object.assert_called_once()


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_get_asset_not_found(self, version_manager: AssetVersionManager) -> None:
        """Should raise error for nonexistent asset."""
        with pytest.raises(AssetNotFoundError):
            await version_manager.get_asset("nonexistent_id")

    @pytest.mark.asyncio
    async def test_get_asset_with_versions(self, version_manager: AssetVersionManager) -> None:
        """Should include versions when requested."""
        asset = await version_manager.create_asset(name="test.jpg", category="original")
        await version_manager.create_version(
            CreateVersionRequest(
                asset_id=asset.asset_id,
                content_hash="sha256_v1",
                r2_key=f"versioned/{asset.asset_id}/v1/test.jpg",
                file_size_bytes=1024,
            )
        )

        asset_with_versions = await version_manager.get_asset(asset.asset_id, include_versions=True)

        assert asset_with_versions.versions is not None
        assert len(asset_with_versions.versions) == 1

    @pytest.mark.asyncio
    async def test_version_key_generation(self, version_manager: AssetVersionManager) -> None:
        """Should generate correct R2 keys."""
        key = version_manager._generate_versioned_key("asset_123", 2, "image.jpg")
        assert key == "versioned/asset_123/v2/image.jpg"
