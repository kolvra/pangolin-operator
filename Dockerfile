# Usar imagen base oficial de Python con versión específica y slim para menor tamaño
FROM python:3.11-slim

# Establecer metadatos de la imagen
LABEL maintainer="your-email@example.com" \
      description="Pangolin Operator - Kubernetes Operator for Pangolin Ingress management" \
      version="0.1.0"

# Instalar dependencias del sistema necesarias para compilar algunas librerías Python
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para seguridad
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Instalar uv para gestión rápida de dependencias Python
RUN pip install --no-cache-dir uv

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de configuración de dependencias primero para aprovechar cache de Docker
COPY pyproject.toml uv.lock ./

# Instalar dependencias usando uv (más rápido que pip)
RUN uv sync --frozen --no-dev

# Copiar el código fuente
COPY handler.py ./
COPY pangolin-ingress-crd.yml ./

# Cambiar la propiedad de los archivos al usuario no-root
RUN chown -R appuser:appuser /app

# Cambiar al usuario no-root
USER appuser

# Configurar variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Comando por defecto para ejecutar el operador
CMD ["python", "-m", "kopf", "run", "handler.py", "--verbose"]

# Healthcheck para monitoreo del contenedor
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1