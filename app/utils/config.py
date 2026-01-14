"""
Configuration validation and environment variable handling
"""

import os
from typing import Dict, List, Optional
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

class ConfigError(Exception):
    """Raised when configuration validation fails"""
    pass

def validate_required_env_vars(required_vars: List[str]) -> Dict[str, str]:
    """
    Validate that all required environment variables are set.
    
    Args:
        required_vars: List of required environment variable names
        
    Returns:
        Dictionary of environment variable values
        
    Raises:
        ConfigError: If any required variables are missing
    """
    missing_vars = []
    config = {}
    
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            missing_vars.append(var)
        else:
            config[var] = value
    
    if missing_vars:
        raise ConfigError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            f"Please check your .env file or set these variables in your environment."
        )
    
    return config

def get_azure_config() -> Dict[str, str]:
    """Get and validate Azure configuration"""
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_VERSION",
        "AZURE_OPENAI_CHAT_DEPLOYMENT",
        "AZURE_OPENAI_EMBED_DEPLOYMENT",
        "AZURE_OPENAI_KEY"
    ]
    
    config = validate_required_env_vars(required_vars)
    
    # Validate endpoint format
    endpoint = config["AZURE_OPENAI_ENDPOINT"]
    if not endpoint.startswith("https://") or not endpoint.endswith("/"):
        raise ConfigError(
            f"Invalid AZURE_OPENAI_ENDPOINT format: {endpoint}\n"
            f"Expected format: https://your-resource.openai.azure.com/"
        )
    
    return config

def get_cosmos_config() -> Dict[str, str]:
    """Get and validate Cosmos DB configuration"""
    required_vars = [
        "COSMOS_ENDPOINT",
        "COSMOS_DB",
        "COSMOS_CONTAINER",
        "COSMOS_PARTITION_KEY"
    ]
    
    config = validate_required_env_vars(required_vars)
    
    # Check for COSMOS_KEY
    if not os.environ.get("COSMOS_KEY"):
        raise ConfigError(
            "Cosmos DB authentication not configured. "
            "Set COSMOS_KEY environment variable."
        )
    
    # Validate endpoint format
    endpoint = config["COSMOS_ENDPOINT"]
    if not endpoint.startswith("https://") or not endpoint.endswith("/"):
        raise ConfigError(
            f"Invalid COSMOS_ENDPOINT format: {endpoint}\n"
            f"Expected format: https://your-account.documents.azure.com:443/"
        )
    
    return config

def get_optional_config() -> Dict[str, Optional[str]]:
    """Get optional configuration variables"""
    return {
        "PROJECT_ENDPOINT": os.environ.get("PROJECT_ENDPOINT"),
        "AGENT_ID": os.environ.get("AGENT_ID"),
        "BING_CONNECTION_ID": os.environ.get("BING_CONNECTION_ID"),
        "MODEL_DEPLOYMENT_NAME": os.environ.get("MODEL_DEPLOYMENT_NAME"),
        "BING_KEY": os.environ.get("BING_KEY"),
        "PYTHONPATH": os.environ.get("PYTHONPATH")
    }

def validate_all_config() -> Dict[str, any]:
    """
    Validate all configuration and return a complete config dictionary.
    
    Returns:
        Complete configuration dictionary
        
    Raises:
        ConfigError: If configuration validation fails
    """
    try:
        config = {
            "azure": get_azure_config(),
            "cosmos": get_cosmos_config(),
            "optional": get_optional_config()
        }
        
        return config
        
    except ConfigError:
        raise
    except Exception as e:
        raise ConfigError(f"Configuration validation failed: {e}")

def print_config_summary(config: Dict[str, any]) -> None:
    """Print a summary of the current configuration"""
    print("🔧 Configuration Summary")
    print("=" * 40)
    
    # Azure config
    azure = config["azure"]
    print(f"Azure OpenAI Endpoint: {azure['AZURE_OPENAI_ENDPOINT']}")
    print(f"API Version: {azure['AZURE_OPENAI_API_VERSION']}")
    print(f"Chat Deployment: {azure['AZURE_OPENAI_CHAT_DEPLOYMENT']}")
    print(f"Embed Deployment: {azure['AZURE_OPENAI_EMBED_DEPLOYMENT']}")
    print(f"API Key: {'SET' if azure.get('AZURE_OPENAI_KEY') else 'NOT SET'}")
    
    # Cosmos config
    cosmos = config["cosmos"]
    print(f"Cosmos Endpoint: {cosmos['COSMOS_ENDPOINT']}")
    print(f"Database: {cosmos['COSMOS_DB']}")
    print(f"Container: {cosmos['COSMOS_CONTAINER']}")
    
    # Optional config
    optional = config["optional"]
    print(f"Project Endpoint: {'SET' if optional['PROJECT_ENDPOINT'] else 'NOT SET'}")
    print(f"Agent ID: {'SET' if optional['AGENT_ID'] else 'NOT SET'}")
    print(f"Bing Connection ID: {'SET' if optional['BING_CONNECTION_ID'] else 'NOT SET'}")
    print(f"Model Deployment Name: {'SET' if optional['MODEL_DEPLOYMENT_NAME'] else 'NOT SET'}")
    print(f"Bing Key: {'SET' if optional['BING_KEY'] else 'NOT SET'}")
    print(f"Python Path: {'SET' if optional['PYTHONPATH'] else 'NOT SET'}")
    
    print("=" * 40)
