"""Safely retrieve environment variables and API keys.

This module loads environment variables from .env file and provides
safe access to API keys without exposing them in version control.

Usage:
    from src.env_get import get_gemini_api_key, get_kimi_api_key

    gemini_key = get_gemini_api_key()
    kimi_key = get_kimi_api_key()
"""
import os
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


def load_env_file(env_path: Optional[Path] = None) -> bool:
    """Load environment variables from .env file.

    Args:
        env_path: Path to .env file. If None, searches for .env in:
                  1. Current directory
                  2. Parent directory
                  3. Project root

    Returns:
        True if .env file was loaded, False otherwise
    """
    if not DOTENV_AVAILABLE:
        return False

    if env_path is None:
        # Search for .env file
        search_paths = [
            Path.cwd() / ".env",
            Path.cwd().parent / ".env",
            Path(__file__).parent.parent / ".env",  # Project root
        ]

        for path in search_paths:
            if path.exists():
                env_path = path
                break

    if env_path and env_path.exists():
        load_dotenv(env_path)
        return True

    return False


# Auto-load .env file on module import
_env_loaded = load_env_file()


def get_env_var(var_name: str, required: bool = True, default: Optional[str] = None) -> Optional[str]:
    """Safely get environment variable.

    Args:
        var_name: Name of environment variable
        required: If True, raises ValueError if not set
        default: Default value if not set

    Returns:
        Environment variable value or None

    Raises:
        ValueError: If required=True and variable not set
    """
    value = os.getenv(var_name, default)

    if required and value is None:
        raise ValueError(
            f"Environment variable '{var_name}' is not set. "
            f"Please set it in .env file or environment."
        )

    return value


def get_gemini_api_key() -> str:
    """Get Gemini API key from environment.

    Returns:
        Gemini API key

    Raises:
        ValueError: If GEMINI_API_KEY not set
    """
    return get_env_var("GEMINI_API_KEY", required=True)


def get_kimi_api_key() -> str:
    """Get Kimi API key from environment.

    Looks for KIMI_API_KEY_v3 first, then falls back to KIMI_API_KEY.

    Returns:
        Kimi API key

    Raises:
        ValueError: If neither KIMI_API_KEY_v3 nor KIMI_API_KEY is set
    """
    key = get_env_var("KIMI_API_KEY_v3", required=False)
    if key:
        return key

    key = get_env_var("KIMI_API_KEY", required=False)
    if key:
        return key

    raise ValueError(
        "Kimi API key not set. Please set KIMI_API_KEY_v3 or KIMI_API_KEY "
        "in .env file or environment."
    )


def get_mlflow_tracking_uri() -> Optional[str]:
    """Get MLflow tracking URI from environment.

    Returns:
        MLflow tracking URI or None if not set
    """
    return get_env_var("MLFLOW_TRACKING_URI", required=False)


def get_redis_config() -> dict:
    """Get Redis configuration from environment.

    Returns:
        Dict with 'host' and 'port' keys
    """
    return {
        "host": get_env_var("REDIS_HOST", required=False, default="localhost"),
        "port": int(get_env_var("REDIS_PORT", required=False, default="6379"))
    }


def check_env_status() -> dict:
    """Check status of environment variables.

    Returns:
        Dict with status information
    """
    status = {
        "dotenv_available": DOTENV_AVAILABLE,
        "env_file_loaded": _env_loaded,
        "gemini_api_key_set": os.getenv("GEMINI_API_KEY") is not None,
        "kimi_api_key_set": (
            os.getenv("KIMI_API_KEY_v3") is not None or
            os.getenv("KIMI_API_KEY") is not None
        ),
        "mlflow_tracking_uri_set": os.getenv("MLFLOW_TRACKING_URI") is not None,
    }

    return status


if __name__ == "__main__":
    """Test environment variable loading."""
    print("Environment Status:")
    print("=" * 60)

    status = check_env_status()
    for key, value in status.items():
        icon = "✓" if value else "✗"
        print(f"{icon} {key}: {value}")

    print("\nTesting API key retrieval:")
    print("-" * 60)

    try:
        gemini_key = get_gemini_api_key()
        print(f"✓ Gemini API Key: {gemini_key[:20]}...")
    except ValueError as e:
        print(f"✗ Gemini API Key: {e}")

    try:
        kimi_key = get_kimi_api_key()
        print(f"✓ Kimi API Key: {kimi_key[:20]}...")
    except ValueError as e:
        print(f"✗ Kimi API Key: {e}")

    print("\n" + "=" * 60)
