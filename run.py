from flask import Flask
from app import create_app
import logging

# ログ設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    logger.debug("Starting application creation...")
    app = create_app()
    logger.debug("Application created successfully")

    if __name__ == '__main__':
        logger.info("Starting Flask server...")
        app.run(debug=True, host='0.0.0.0', port=5000)
except Exception as e:
    logger.error(f"Error occurred: {str(e)}")
    raise
