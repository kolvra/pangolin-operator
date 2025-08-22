"""
Pangolin Operator Handler

kopf run handler.py
"""
import os
import time
from functools import wraps

import kopf
import requests
import structlog
from dotenv import load_dotenv

load_dotenv()

# Configurar structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)


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
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
    "accept": "*/*"
}

# Métricas básicas
metrics = {
    'resources_created': 0,
    'resources_deleted': 0,
    'resources_updated': 0,
    'api_errors': 0
}


def retry_with_backoff(max_retries=3, base_delay=1):
    """Decorator para retry con backoff exponencial."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.RequestException as e:
                    if attempt == max_retries - 1:
                        metrics['api_errors'] += 1
                        raise kopf.PermanentError(
                            f"Failed after {max_retries} attempts: {e}")
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
            return None
        return wrapper
    return decorator


def validate_spec(spec):
    """Validate the resource specification."""
    required_fields = ['domain', 'subdomain', 'service']
    for field in required_fields:
        if field not in spec:
            raise kopf.PermanentError(f"Missing required field: {field}")

    # Validar formato de subdomain
    subdomain = spec['subdomain']
    if not subdomain.replace('-', '').replace('_', '').isalnum():
        raise kopf.PermanentError(f"Invalid subdomain format: {subdomain}")

    # Validar service
    service = spec['service']
    if 'name' not in service or 'port' not in service:
        raise kopf.PermanentError("Service must have 'name' and 'port' fields")


@retry_with_backoff()
def create_resource(resource_data: dict, sso: bool = False):
    """Create a new resource in Pangolin API and optionally disable SSO."""
    if DRY_RUN:
        structlog.get_logger().info("DRY RUN: Would create resource",
                                    resource_data=resource_data)
        return {"resourceId": "dry-run-id", "fake": True}

    url = f"{PANGOLIN_API_URL}/org/{ORGANIZATION_ID}/site/{SITE_ID}/resource"
    response = requests.put(url, headers=HEADERS,
                            json=resource_data, timeout=10)
    response.raise_for_status()
    resource_created = response.json().get("data", None)

    if sso:
        return resource_created
    else:
        resource_id = resource_created.get("resourceId")
        return disable_sso(resource_id)


@retry_with_backoff()
def disable_sso(resource_id: str):
    """Disable SSO for a resource in Pangolin API."""
    if DRY_RUN:
        structlog.get_logger().info("DRY RUN: Would disable SSO", resource_id=resource_id)
        return {"resourceId": resource_id, "sso": False}

    url = f"{PANGOLIN_API_URL}/resource/{resource_id}"
    response = requests.post(url, headers=HEADERS, json={
                             "sso": False}, timeout=10)
    response.raise_for_status()
    return response.json().get("data", None)


@retry_with_backoff()
def add_target_to_resource(resource_id: str, target_data: dict):
    """Add a target to a resource in Pangolin API."""
    if DRY_RUN:
        structlog.get_logger().info("DRY RUN: Would add target",
                                    resource_id=resource_id, target_data=target_data)
        return {"success": True}

    url = f"{PANGOLIN_API_URL}/resource/{resource_id}/target"
    response = requests.put(url, headers=HEADERS, json=target_data, timeout=10)
    response.raise_for_status()
    return response.json().get("data", None)


@retry_with_backoff()
def delete_resource(resource_id: str):
    """Delete a resource in Pangolin API."""
    if DRY_RUN:
        structlog.get_logger().info("DRY RUN: Would delete resource", resource_id=resource_id)
        return True

    url = f"{PANGOLIN_API_URL}/resource/{resource_id}"
    response = requests.delete(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.json().get("success", False)


@retry_with_backoff()
def get_resources():
    """Get all resources from Pangolin API."""
    if DRY_RUN:
        return []

    url = f"{PANGOLIN_API_URL}/org/{ORGANIZATION_ID}/resources"
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.json().get("data", {}).get("resources", [])


@kopf.on.create('pangolin.sparkfly.dev', 'v1alpha1', 'pangoliningresses')
def create_fn(spec, name, namespace, patch, logger, **_kwargs):
    """Create a new resource in Pangolin API."""
    # Usar un logger estructurado local, no reasignar el parámetro
    struct_logger = structlog.get_logger().bind(
        resource_name=name,
        namespace=namespace,
        fqdn=f"{spec['subdomain']}.{spec['domain']}"
    )

    try:
        # Validar spec
        validate_spec(spec)

        # Agregar finalizer para cleanup garantizado
        finalizers = patch.metadata.get('finalizers', [])
        if 'pangolin.sparkfly.dev/cleanup' not in finalizers:
            patch.metadata.finalizers = finalizers + \
                ['pangolin.sparkfly.dev/cleanup']

        service = spec['service']
        ssl = spec.get('ssl', False)
        fqdn = f"{spec['subdomain']}.{spec['domain']}"

        struct_logger.info("Starting resource creation")
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

        resource_id = created.get("resourceId")
        service_name = service.get('name', name)
        service_namespace = service.get('namespace', namespace)

        add_target_to_resource(resource_id, {
            "ip": f"{service_name}.{service_namespace}.svc.cluster.local",
            "port": service.get("port", 80),
            "method": "https" if ssl else "http",
            "enabled": True,
        })

        metrics['resources_created'] += 1
        struct_logger.info("Successfully created resource",
                           resource_id=resource_id)
        logger.info(f"Successfully registered {fqdn} in Pangolin")

        # Actualizar status
        return {
            'resourceId': resource_id,
            'fqdn': fqdn,
            'ready': True,
            'message': 'Successfully created',
            'createdAt': time.time()
        }

    except Exception as e:
        struct_logger.error("Failed to create resource", error=str(e))
        # Asegurar que el status refleje el error
        patch.status = {
            'ready': False,
            'message': f'Failed to create: {str(e)}',
            'fqdn': f"{spec['subdomain']}.{spec['domain']}"
        }
        raise


@kopf.on.update('pangolin.sparkfly.dev', 'v1alpha1', 'pangoliningresses')
def update_fn(spec, old, new, name, namespace, patch, logger, **_kwargs):
    """Update a resource in Pangolin API when spec changes."""
    struct_logger = structlog.get_logger().bind(
        resource_name=name,
        namespace=namespace,
        fqdn=f"{spec['subdomain']}.{spec['domain']}"
    )

    try:
        validate_spec(spec)

        # Por simplicidad, por ahora recreamos el recurso si cambió algo importante
        old_spec = old.get('spec', {})
        new_spec = new.get('spec', {})

        # Campos que requieren recreación
        recreate_fields = ['subdomain', 'domain', 'service']
        needs_recreate = any(old_spec.get(field) != new_spec.get(field)
                             for field in recreate_fields)

        if needs_recreate:
            struct_logger.info("Resource needs recreation due to spec changes")

            # Primero eliminar el viejo
            delete_fn(old_spec, name, logger)

            # Luego crear el nuevo
            return create_fn(spec, name, namespace, patch, logger)
        else:
            struct_logger.info("No significant changes detected")
            metrics['resources_updated'] += 1
            return {
                'ready': True,
                'message': 'No changes required',
                'fqdn': f"{spec['subdomain']}.{spec['domain']}"
            }

    except Exception as e:
        struct_logger.error("Failed to update resource", error=str(e))
        patch.status = {
            'ready': False,
            'message': f'Failed to update: {str(e)}',
            'fqdn': f"{spec['subdomain']}.{spec['domain']}"
        }
        raise


@kopf.on.delete('pangolin.sparkfly.dev', 'v1alpha1', 'pangoliningresses')
def delete_fn(spec, name, namespace, patch, logger, **_kwargs):
    """Delete a resource in Pangolin API."""
    struct_logger = structlog.get_logger().bind(
        resource_name=name,
        namespace=namespace,
        fqdn=f"{spec['subdomain']}.{spec['domain']}"
    )

    try:
        subdomain = spec['subdomain']
        domain = spec['domain']
        fqdn = f"{subdomain}.{domain}"

        struct_logger.info("Starting resource deletion")

        resources = get_resources()
        deleted_any = False

        for r in resources:
            if r.get("fullDomain") == fqdn and r.get("name", "").startswith("k8s.po-"):
                resource_id = r.get("resourceId")
                if resource_id:
                    success = delete_resource(resource_id)
                    if success:
                        struct_logger.info(
                            "Deleted resource", resource_id=resource_id)
                        logger.info(
                            f"Deleted Pangolin resource {resource_id} for {fqdn}")
                        deleted_any = True

        if deleted_any:
            metrics['resources_deleted'] += 1

        # Remover finalizer
        if patch and patch.metadata:
            finalizers = patch.metadata.get('finalizers', [])
            if 'pangolin.sparkfly.dev/cleanup' in finalizers:
                finalizers.remove('pangolin.sparkfly.dev/cleanup')
                patch.metadata.finalizers = finalizers

    except Exception as e:
        struct_logger.error("Failed to delete resource", error=str(e))
        raise kopf.TemporaryError(
            f"Failed to delete Pangolin resource: {e}", delay=30)


@kopf.on.probe(id='pangolin-api-health')
def health_check(**_kwargs):
    """Check if Pangolin API is accessible."""
    try:
        # Simple health check - intentar acceder a la API
        response = requests.get(f"{PANGOLIN_API_URL}/org/{ORGANIZATION_ID}/resources",
                                headers=HEADERS, timeout=5)
        return response.status_code == 200
    except:
        return False


@kopf.on.probe(id='operator-metrics')
def metrics_probe(**_kwargs):
    """Expose basic metrics."""
    return {
        'resources_created': metrics['resources_created'],
        'resources_deleted': metrics['resources_deleted'],
        'resources_updated': metrics['resources_updated'],
        'api_errors': metrics['api_errors']
    }
