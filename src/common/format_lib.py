import typing

import yaml

from src.common.config_lib import app_config


def format_certificate(
    data: str, cert_name: str, alt_names: list, namespace: str, logger
) -> typing.Any | None:
    try:
        cert_obj = yaml.safe_load(data)
    except yaml.YAMLError as e:
        logger.error(f"Error while parsing YAML for certificate: {e}.")
        return None
    if not cert_obj.get("spec", {}) or not cert_obj.get("metadata", {}):
        logger.error(f"No key spec found in {data}.")
        return None
    cert_name_suffix = app_config.config.get("certificate", {}).get(
        "cert_name_suffix", ""
    )
    cert_name_format = f"{cert_name}-{cert_name_suffix}"
    cert_obj["spec"]["secretName"] = cert_name_format
    cert_obj["spec"]["dnsNames"] = alt_names
    cert_obj["metadata"]["name"] = cert_name_format
    cert_obj["metadata"]["namespace"] = namespace
    return cert_obj
