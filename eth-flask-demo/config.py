import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration."""
    # Flask settings
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    TESTING = False
    
    # Ethereum settings
    ETHEREUM_NODE_URL = os.getenv('ETHEREUM_NODE_URL', 'http://localhost:8545')
    PRIVATE_KEY = os.getenv('PRIVATE_KEY')
    GAS_PRICE_STRATEGY = os.getenv('GAS_PRICE_STRATEGY', 'medium')  # low, medium, high
    GAS_LIMIT = int(os.getenv('GAS_LIMIT', '60000'))
    MAX_GAS_PRICE = int(os.getenv('MAX_GAS_PRICE', '100'))  # in gwei
    
    # IPFS settings
    IPFS_NODE_URL = os.getenv('IPFS_NODE_URL', '/dns4/ipfs/tcp/5001/http')
    IPFS_TIMEOUT = int(os.getenv('IPFS_TIMEOUT', '30'))  # seconds
    
    # API settings
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '16 * 1024 * 1024'))  # 16MB
    RATE_LIMIT = os.getenv('RATE_LIMIT', '100/minute')
    
    # Security settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    API_KEY_HEADER = 'X-API-Key'
    
    # Transaction settings
    TRANSACTION_TIMEOUT = int(os.getenv('TRANSACTION_TIMEOUT', '30'))  # seconds
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    
    # Cache settings
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '300'))  # 5 minutes

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = False
    TESTING = True
    ETHEREUM_NODE_URL = 'http://localhost:8545'
    IPFS_NODE_URL = '/dns4/ipfs/tcp/5001/http'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    # Production-specific settings
    GAS_PRICE_STRATEGY = 'medium'
    MAX_GAS_PRICE = 50  # gwei
    RATE_LIMIT = '1000/minute'
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',')
    CACHE_TYPE = 'redis'
    CACHE_DEFAULT_TIMEOUT = 3600  # 1 hour

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment."""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default']) 