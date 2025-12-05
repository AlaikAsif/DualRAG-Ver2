"""Main entry point for DualRAG application."""

import logging
import os

from api.server import app

if __name__ == "__main__":
    import uvicorn
    
    log_level = "info"
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=debug,
        log_level=log_level
    )
