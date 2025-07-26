"""Unit tests for the encoding module."""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from cachetools import LRUCache

from dev_aci.editor.encoding import EncodingManager, with_encoding


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield Path(path)
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


@pytest.fixture
def encoding_manager():
    """Create an EncodingManager instance for testing."""
    return EncodingManager()


def test_init(encoding_manager):
    """Test initialization of EncodingManager."""
    assert isinstance(encoding_manager, EncodingManager)
    assert isinstance(encoding_manager._encoding_cache, LRUCache)
    assert encoding_manager.default_encoding == 'utf-8'
    assert encoding_manager.confidence_threshold == 0.9


def test_detect_encoding_nonexistent_file(encoding_manager):
    """Test detecting encoding for a nonexistent file."""
    nonexistent_path = Path('/nonexistent/file.txt')
    encoding = encoding_manager.detect_encoding(nonexistent_path)
    assert encoding == encoding_manager.default_encoding


def test_detect_encoding_utf8(encoding_manager, temp_file):
    """Test detecting UTF-8 encoding."""
    # Create a UTF-8 encoded file
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write('Hello, world! UTF-8 encoded text.')

    encoding = encoding_manager.detect_encoding(temp_file)
    assert encoding.lower() in ('utf-8', 'ascii')


def test_detect_encoding_utf8_with_icon(encoding_manager, temp_file):
    """Test detecting UTF-8 encoding with a word and an emoji."""
    # Create a UTF-8 encoded file with a single word and an emoji
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write('Hello 😊')

    encoding = encoding_manager.detect_encoding(temp_file)
    assert encoding.lower() == 'utf-8'


def test_detect_encoding_cp1251(encoding_manager, temp_file):
    """Test detecting CP1251 encoding."""
    # Create a CP1251 encoded file with Cyrillic characters
    with open(temp_file, 'wb') as f:
        f.write('Привет, мир! Текст в кодировке CP1251.'.encode('cp1251'))

    encoding = encoding_manager.detect_encoding(temp_file)
    assert encoding.lower() in ('windows-1251', 'cp1251')


def test_detect_encoding_low_confidence(encoding_manager, temp_file):
    """Test fallback to default encoding when confidence is low."""
    # Create a file with mixed encodings to confuse the detector
    with open(temp_file, 'wb') as f:
        f.write(b'\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f')

    # Mock chardet.detect to return low confidence
    with patch(
        'charset_normalizer.detect',
        return_value={'encoding': 'ascii', 'confidence': 0.3},
    ):
        encoding = encoding_manager.detect_encoding(temp_file)
        assert encoding == encoding_manager.default_encoding


def test_detect_encoding_none_result(encoding_manager, temp_file):
    """Test fallback to default encoding when chardet returns None for encoding."""
    with open(temp_file, 'wb') as f:
        f.write(b'\x00\x01\x02\x03')  # Binary data

    # Mock chardet.detect to return None for encoding
    with patch(
        'charset_normalizer.detect', return_value={'encoding': None, 'confidence': 0.0}
    ):
        encoding = encoding_manager.detect_encoding(temp_file)
        assert encoding == encoding_manager.default_encoding


def test_get_encoding_cache_hit(encoding_manager, temp_file):
    """Test that get_encoding uses cached values when available."""
    # Create a file
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write('Hello, world!')

    # First call should detect encoding
    with patch.object(
        encoding_manager, 'detect_encoding', return_value='utf-8'
    ) as mock_detect:
        encoding1 = encoding_manager.get_encoding(temp_file)
        assert encoding1 == 'utf-8'
        mock_detect.assert_called_once()

    # Second call should use cache
    with patch.object(
        encoding_manager, 'detect_encoding', return_value='utf-8'
    ) as mock_detect:
        encoding2 = encoding_manager.get_encoding(temp_file)
        assert encoding2 == 'utf-8'
        mock_detect.assert_not_called()


def test_get_encoding_cache_invalidation(encoding_manager, temp_file):
    """Test that cache is invalidated when file is modified."""
    # Create a file
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write('Hello, world!')

    # First call should detect encoding
    encoding1 = encoding_manager.get_encoding(temp_file)
    assert encoding1.lower() in ('utf-8', 'ascii')

    # Wait a moment to ensure modification time will be different
    time.sleep(0.1)

    # Modify the file
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write('Modified content')

    # Mock detect_encoding to verify it's called again
    with patch.object(
        encoding_manager, 'detect_encoding', return_value='utf-8'
    ) as mock_detect:
        encoding2 = encoding_manager.get_encoding(temp_file)
        assert encoding2 == 'utf-8'
        mock_detect.assert_called_once()


def test_with_encoding_decorator():
    """Test the with_encoding decorator."""

    # Create a mock class with a method that will be decorated
    class MockEditor:
        def __init__(self):
            self._encoding_manager = EncodingManager()

        @with_encoding
        def read_file(self, path, encoding='utf-8'):
            return f'Reading file with encoding: {encoding}'

    editor = MockEditor()

    # Test with a directory
    with patch.object(Path, 'is_dir', return_value=True):
        with patch.object(
            editor._encoding_manager, 'get_encoding'
        ) as mock_get_encoding:
            result = editor.read_file(Path('/some/dir'))
            assert result == 'Reading file with encoding: utf-8'
            mock_get_encoding.assert_not_called()

    # Test with a nonexistent file
    with patch.object(Path, 'is_dir', return_value=False):
        with patch.object(Path, 'exists', return_value=False):
            result = editor.read_file(Path('/nonexistent/file.txt'))
            assert (
                result
                == f'Reading file with encoding: {editor._encoding_manager.default_encoding}'
            )

    # Test with an existing file
    with patch.object(Path, 'is_dir', return_value=False):
        with patch.object(Path, 'exists', return_value=True):
            with patch.object(
                editor._encoding_manager, 'get_encoding', return_value='latin-1'
            ):
                result = editor.read_file(Path('/existing/file.txt'))
                assert result == 'Reading file with encoding: latin-1'


def test_with_encoding_respects_provided_encoding():
    """Test that the with_encoding decorator respects explicitly provided encoding."""
    # The current implementation of with_encoding always calls get_encoding
    # but doesn't override the provided encoding if it exists in kwargs

    class MockEditor:
        def __init__(self):
            self._encoding_manager = EncodingManager()

        @with_encoding
        def read_file(self, path, encoding='utf-8'):
            return f'Reading file with encoding: {encoding}'

    editor = MockEditor()

    # Test with explicitly provided encoding
    with patch.object(Path, 'is_dir', return_value=False):
        with patch.object(Path, 'exists', return_value=True):
            with patch.object(
                editor._encoding_manager,
                'get_encoding',
                return_value='detected-encoding',
            ):
                result = editor.read_file(Path('/some/file.txt'), encoding='iso-8859-1')
                # The provided encoding should be used, not the detected one
                assert result == 'Reading file with encoding: iso-8859-1'


def test_cache_size_limit(encoding_manager, temp_file):
    """Test that the cache size is limited and LRU entries are evicted."""
    # Create a small cache for testing
    encoding_manager = EncodingManager(max_cache_size=3)

    # Create a file
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write('Test file')

    # Create 4 different paths (using the same file but with different paths)
    paths = [Path(f'{temp_file}.{i}') for i in range(4)]

    # Mock exists and getmtime to return consistent values
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(os.path, 'getmtime', return_value=123456):
            with patch.object(
                encoding_manager, 'detect_encoding', return_value='utf-8'
            ):
                # Access paths in order 0, 1, 2, 3
                for i, path in enumerate(paths):
                    encoding_manager.get_encoding(path)

                # After adding 4th item, the cache should still have 3 items
                assert len(encoding_manager._encoding_cache) == 3
                # Path 0 should have been evicted (LRU)
                assert str(paths[0]) not in encoding_manager._encoding_cache
                # Paths 1, 2, 3 should still be in the cache
                for j in range(1, 4):
                    assert str(paths[j]) in encoding_manager._encoding_cache
