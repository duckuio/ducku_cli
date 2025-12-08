from src.helpers.file_system import CachedPath
import os

def test_cached_path():
    # Create a temporary file for testing
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"Hello, World!")
        tmp_path = tmp.name

    try:
        cp = CachedPath(tmp_path)
        content1 = cp.read_text()
        content2 = cp.read_text()
        assert content1 == "Hello, World!"
        assert content1 == content2  # Should be the same and from cache
    finally:
        os.remove(tmp_path)