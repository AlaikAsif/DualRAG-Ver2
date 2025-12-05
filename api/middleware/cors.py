"""CORS configuration utilities."""

def get_cors_config():
    """Get CORS middleware configuration."""
    return {
        "allow_origins": ["*"],
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }
