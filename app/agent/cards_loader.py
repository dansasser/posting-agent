import yaml
import os
from typing import Dict, Any

from app.telemetry.logger import get_logger

logger = get_logger(__name__)

RECIPES_DIR = os.path.join(os.path.dirname(__file__), '..', 'recipes')
PROTOCOLS_DIR = os.path.join(os.path.dirname(__file__), '..', 'protocols')

def _load_yaml_file(filepath: str) -> Dict[str, Any]:
    """
    Loads a single YAML file and returns its content.
    """
    try:
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file {filepath}: {e}")
        raise

def load_recipe(recipe_name: str) -> Dict[str, Any]:
    """
    Loads a specific recipe card from the recipes directory.

    Args:
        recipe_name: The filename of the recipe to load (e.g., "recipe_thread_post.yaml").

    Returns:
        A dictionary containing the recipe's configuration.
    """
    filepath = os.path.join(RECIPES_DIR, recipe_name)
    logger.info(f"Loading recipe card: {recipe_name}")
    return _load_yaml_file(filepath)

def load_protocol(protocol_name: str) -> Dict[str, Any]:
    """
    Loads a specific protocol card from the protocols directory.

    Args:
        protocol_name: The filename of the protocol to load (e.g., "protocol_card.yaml").

    Returns:
        A dictionary containing the protocol's rules.
    """
    filepath = os.path.join(PROTOCOLS_DIR, protocol_name)
    logger.info(f"Loading protocol card: {protocol_name}")
    return _load_yaml_file(filepath)