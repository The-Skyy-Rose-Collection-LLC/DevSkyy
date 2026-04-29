from unittest.mock import MagicMock, patch
from pathlib import Path
from scripts.purge_hallucinations import purge

def test_purge_logic():
    # Mock files
    mock_files = []

    # Rule 1 target
    m0 = MagicMock(spec=Path)
    m0.name = "lh-005-model.jpg"
    m0.is_file.return_value = True
    m0.stat.return_value.st_size = 100 * 1024
    mock_files.append(m0)

    # Rule 2 target
    m1 = MagicMock(spec=Path)
    m1.name = "po-001.jpg"
    m1.is_file.return_value = True
    m1.stat.return_value.st_size = 100 * 1024
    mock_files.append(m1)

    # Rule 3 target
    m2 = MagicMock(spec=Path)
    m2.name = "br-001-model.jpg"
    m2.is_file.return_value = True
    m2.stat.return_value.st_size = 2 * 1024 * 1024 # 2MB
    mock_files.append(m2)

    # Safe file
    m3 = MagicMock(spec=Path)
    m3.name = "br-001.jpg"
    m3.is_file.return_value = True
    m3.stat.return_value.st_size = 500 * 1024 # 500KB
    mock_files.append(m3)

    with patch("scripts.purge_hallucinations.PRODUCTS_DIR") as mock_dir:
        mock_dir.exists.return_value = True
        mock_dir.iterdir.return_value = mock_files

        purge()

        # Verify unlinks
        m0.unlink.assert_called_once()
        m1.unlink.assert_called_once()
        m2.unlink.assert_called_once()
        m3.unlink.assert_not_called()
