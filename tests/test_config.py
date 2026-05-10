"""
Tests for configuration module
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_config_imports():
    """Test that config imports correctly"""
    try:
        import config
        assert hasattr(config, 'BOT_TOKEN')
        assert hasattr(config, 'SHOP_NAME')
        assert hasattr(config, 'MONGO_URI')
        assert hasattr(config, 'logger')
        print(f"✅ Config OK - Shop: {config.SHOP_NAME}")
    except Exception as e:
        pytest.fail(f"Config import failed: {e}")

def test_utils_import():
    """Test that utils import correctly"""
    try:
        from utils.bale_api import bot, BaleAPI
        assert bot is not None
        assert BaleAPI is not None
        print("✅ BaleAPI import OK")
    except Exception as e:
        pytest.fail(f"BaleAPI import failed: {e}")

def test_requirements():
    """Test requirements file is valid"""
    req_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
    assert os.path.exists(req_path), "requirements.txt not found!"
    with open(req_path) as f:
        lines = f.readlines()
    assert len(lines) > 0, "requirements.txt is empty!"
    print(f"✅ requirements.txt OK ({len(lines)} dependencies)")

if __name__ == '__main__':
    test_config_imports()
    test_utils_import()
    test_requirements()
    print("\n🎉 All tests passed!")
