"""Shared utilities for AWS Secrets Manager secret resolution."""

from utils.environment_helpers import get_aws_secret, validate_env_variable


def resolve_secret_value(secret_name_env_var: str) -> str:
    """Resolve secret value from Secrets Manager using secret name from env var.

    Args:
        secret_name_env_var: Environment variable name containing the secret name

    Returns:
        Secret value as string
    """
    secret_name = validate_env_variable(secret_name_env_var)
    return get_aws_secret(secret_name)
