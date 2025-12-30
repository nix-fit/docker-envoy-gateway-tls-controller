import copy

import kopf

import src.common.config_lib as config_lib
import src.common.format_lib as format_lib
from src.common.kubernetes_lib import custom_api
import kubernetes

app_config: dict = config_lib.app_config.get_config()


@kopf.on.update("httproutes")
@kopf.on.create("httproutes")
def create_certificate(
    spec: dict, annotations: dict, name: str, namespace: str, logger, **kwargs
):
    annotation_label = app_config.get("kubernetes", {}).get(
        "route_annotation_label", ""
    )
    annotation_value = app_config.get("kubernetes", {}).get(
        "route_annotation_value", ""
    )
    route_annotation_value = annotations.get(annotation_label, "")
    if (
        not route_annotation_value
        or route_annotation_value.lower() != annotation_value.lower()
    ):
        raise kopf.PermanentError(
            f"Annotations for HTTPRoute are not valid. {annotations=}"
        )
    route_hostnames = spec.get("hostnames", [])
    if not route_hostnames:
        raise kopf.PermanentError(
            f"HTTPRoute must contain at least one hostname. Got {len(route_hostnames)!r} hostnames."
        )
    logger.info(
        f"Received new HTTPRoute kind with hostnames: {', '.join(route_hostnames)}"
    )
    tmpl = config_lib.get_yaml_contents("certificate")
    data = format_lib.format_certificate(
        data=tmpl,
        cert_name=name,
        alt_names=route_hostnames,
        namespace=namespace,
        logger=logger,
    )
    if data is None:
        raise kopf.PermanentError(f"Error while formatting certificate.")
    logger.info(f"Gathered certificate info: {data}")
    certificate_params = (
        app_config.get("kubernetes", {}).get("crd", {}).get("certificate", {})
    )
    envoy_namespace = (
        app_config.get("kubernetes", {})
        .get("crd", {})
        .get("envoy_getaway", {})
        .get("namespace", "")
    )
    logger.info(certificate_params)
    api = custom_api.get_api()
    obj = api.create_namespaced_custom_object(
        group=certificate_params.get("group", ""),
        version=certificate_params.get("version", "v1"),
        namespace=envoy_namespace,
        plural=certificate_params.get("plural", "certificates"),
        body=data,
    )
    logger.info(f"Created certificate object {obj}")


@kopf.on.create("certificates")
def update_envoy(spec: dict, status: dict, name: str, namespace: str, logger, **kwargs):
    cert_statuses = status.get("conditions", [])
    if not cert_statuses:
        raise kopf.TemporaryError(f"Cannot retrieve statuses from certificate {name}")
    cert_current_status = cert_statuses[0].get("message", "")
    if cert_current_status not in [
        app_config.get("certificate", {}).get("readiness_string", "")
    ]:
        raise kopf.TemporaryError(
            f"Invalid certificate {name} status: {cert_current_status}"
        )
    logger.info(f"Certificate {name} is ready. Starting patching gateway.")
    envoy_params = (
        app_config.get("kubernetes", {}).get("crd", {}).get("envoy_getaway", {})
    )
    api = kubernetes.client.CustomObjectsApi()
    gateway = api.get_namespaced_custom_object(
        group=envoy_params.get("group", ""),
        version=envoy_params.get("version", "v1"),
        namespace=namespace,
        plural=envoy_params.get("plural", "gateways"),
        name=envoy_params.get("name", "envoy-gateway"),
    )
    listeners = gateway.get("spec", {}).get("listeners", [])
    if not listeners:
        raise kopf.PermanentError(f"Invalid gateway object - no {listeners=} found.")
    certs_names = []
    listener_info = {}
    for index, listener in enumerate(listeners):
        cert_refs = listener.get("tls", {}).get("certificateRefs", [])
        if not cert_refs:
            continue
        for cert_ref in cert_refs:
            cert_name = cert_ref.get("name", None)
            if cert_name is not None:
                certs_names.append(cert_name)
        listener_info[str(index)] = copy.deepcopy(certs_names)
        certs_names.clear()
    if not listener_info.keys():
        raise kopf.PermanentError(f"Invalid gateway object - no tls config found.")
    needs_patching = False
    for key, certs in listener_info.items():
        if name not in certs:
            logger.info(f"Adding certificate {name} to gateway.")
            needs_patching = True
            gateway["spec"]["listeners"][int(key)]["tls"]["certificateRefs"].append(
                {"group": "", "kind": "Secret", "name": name}
            )
    if needs_patching:
        obj = api.patch_namespaced_custom_object(
            group=envoy_params.get("group", ""),
            version=envoy_params.get("version", "v1"),
            namespace=namespace,
            plural=envoy_params.get("plural", "gateways"),
            name=envoy_params.get("name", "gateways"),
            body=gateway,
        )
    else:
        raise kopf.PermanentError(
            f"Patching is not needed. Aborting working with certificate {name}."
        )
