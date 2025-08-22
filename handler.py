"""
Pangolin Operator Handler

kopf run handler.py
"""
import os

import kopf
import requests
from dotenv import load_dotenv

load_dotenv()


def validate_environment():
    """Validate that all required environment variables are set."""
    required_vars = [
        "PANGOLIN_API_URL",
        "PANGOLIN_API_TOKEN",
        "PANGOLIN_ORG",
        "PANGOLIN_SITE_ID",
        "PANGOLIN_DOMAIN_ID"
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing_vars)}")


# Llamar la validación
validate_environment()


PANGOLIN_API_URL = os.getenv("PANGOLIN_API_URL")
API_TOKEN = os.getenv("PANGOLIN_API_TOKEN")
ORGANIZATION_ID = os.getenv("PANGOLIN_ORG")
SITE_ID = os.getenv("PANGOLIN_SITE_ID")
DOMAIN_ID = os.getenv("PANGOLIN_DOMAIN_ID")

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
    "accept": "*/*"
}


def create_resource(resource_data: dict, sso: bool = False):
    """Create a new resource in Pangolin API and optionally disable SSO."""
    url = f"{PANGOLIN_API_URL}/org/{ORGANIZATION_ID}/site/{SITE_ID}/resource"
    try:
        response = requests.put(url, headers=HEADERS,
                                json=resource_data, timeout=10)
        response.raise_for_status()
        resource_created = response.json().get("data", None)
        if sso:
            return resource_created
        else:
            resource_id = resource_created.get("resourceId")
            return disable_sso(resource_id)
    except requests.RequestException as e:
        raise kopf.TemporaryError(f"Failed to create resource: {e}", delay=30)


def disable_sso(resource_id: str):
    """Disable SSO for a resource in Pangolin API."""
    url = f"{PANGOLIN_API_URL}/resource/{resource_id}"
    try:
        response = requests.post(url, headers=HEADERS, json={
                                 "sso": False}, timeout=10)
        response.raise_for_status()
        return response.json().get("data", None)
    except requests.RequestException as e:
        raise kopf.TemporaryError(f"Failed to disable SSO: {e}", delay=30)


def add_target_to_resource(resource_id: str, target_data: dict):
    """Add a target to a resource in Pangolin API."""
    url = f"{PANGOLIN_API_URL}/resource/{resource_id}/target"
    try:
        response = requests.put(url, headers=HEADERS,
                                json=target_data, timeout=10)
        response.raise_for_status()
        return response.json().get("data", None)
    except requests.RequestException as e:
        raise kopf.TemporaryError(f"Failed to add target: {e}", delay=30)


def delete_resource(resource_id: str):
    """Delete a resource in Pangolin API."""
    url = f"{PANGOLIN_API_URL}/resource/{resource_id}"
    try:
        response = requests.delete(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json().get("success", False)
    except requests.RequestException as e:
        raise kopf.TemporaryError(f"Failed to delete resource: {e}", delay=30)


@kopf.on.create('pangolin.sparkfly.dev', 'v1alpha1', 'pangoliningresses')
def create_fn(spec, name, namespace, logger, **_kwargs):
    """Create a new resource in Pangolin API."""
    service = spec['service']
    ssl = spec.get('ssl', False)
    fqdn = f"{spec['subdomain']}.{spec['domain']}"

    logger.info(f"Creating Pangolin resource for {fqdn}")

    created = create_resource({
        "name": f"k8s.po-{name}",
        "subdomain": spec['subdomain'],
        "siteId": int(SITE_ID),
        "http": True,
        "protocol": "tcp",
        "domainId": DOMAIN_ID
    }, sso=spec.get('sso', False))

    if not created:
        raise kopf.TemporaryError(
            "Failed to create Pangolin resource", delay=30)

    service_name = service.get('name', name)
    service_namespace = service.get('namespace', namespace)
    add_target_to_resource(created.get("resourceId"), {
        "ip": f"{service_name}.{service_namespace}.svc.cluster.local",
        "port": service.get("port", 80),
        "method": "https" if ssl else "http",
        "enabled": True,
    })

    logger.info(f"Successfully registered {fqdn} in Pangolin")


@kopf.on.delete('pangolin.sparkfly.dev', 'v1alpha1', 'pangoliningresses')
def delete_fn(spec, name, logger, **_kwargs):
    """Delete a resource in Pangolin API."""
    subdomain = spec['subdomain']
    domain = spec['domain']
    fqdn = f"{subdomain}.{domain}"

    url = f"{PANGOLIN_API_URL}/org/{ORGANIZATION_ID}/resources"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        resources = response.json().get("data", {}).get("resources", [])
        for r in resources:
            if r.get("fullDomain") == fqdn and r.get("name", "").startswith("k8s.po-"):
                resource_id = r.get("resourceId")
                if resource_id:
                    success = delete_resource(resource_id)
                    if success:
                        logger.info(
                            f"Deleted Pangolin resource {resource_id} for {fqdn}")
    except requests.RequestException as e:
        raise kopf.TemporaryError(
            f"Failed to get or delete Pangolin resource: {e}", delay=30)
