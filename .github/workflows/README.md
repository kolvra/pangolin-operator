# GitHub Workflows

Este directorio contiene los workflows de GitHub Actions para el proyecto Pangolin Operator.

## Workflows Disponibles

### 1. `docker-build-push.yml` - Build y Push Unificado

**Propósito**: Workflow único que maneja tanto builds manuales como releases oficiales.

**Se ejecuta cuando**:
- Push a ramas `main` o `develop` (build y push)
- Pull requests hacia `main` (solo build para testing)
- Tags que empiecen con `v*` (release automático)
- Manualmente via `workflow_dispatch` (con opciones avanzadas)

**Lo que hace**:
- 🏗️ **Multi-arch builds**: Construye para AMD64 y ARM64 simultáneamente
- 🐳 **Smart pushing**: Push automático excepto en PRs
- 🔒 **Security scanning**: Escaneo de vulnerabilidades con Trivy
- 📋 **SBOM generation**: Software Bill of Materials automático
- 🛡️ **Build attestations**: Verificaciones criptográficas firmadas
- ⚡ **GitHub Actions cache**: Cache distribuido para builds ultra-rápidos
- 📝 **Auto-releases**: Releases de GitHub automáticos para tags

**Tags generados automáticamente**:
- **Branches**: `main`, `develop`, `main-abc1234`
- **PRs**: `pr-123`
- **Tags semver**: `v1.2.3`, `1.2.3`, `1.2`, `1`, `latest`
- **Manual**: Tags personalizados o `latest`

### 2. `demo.yaml` - Demo con Self-Hosted Runners

**Propósito**: Workflow de demostración para runners auto-hospedados.

## Tecnologías Utilizadas

### Docker Buildx con GitHub Actions

El workflow utiliza las **mejores prácticas oficiales de GitHub** con Docker Buildx:

**Características Premium**:
- 🏗️ **Multi-arquitectura**: Soporte nativo para AMD64 y ARM64
- 🔒 **Seguridad avanzada**: Trivy vulnerability scanning
- 📋 **SBOM**: Software Bill of Materials automático
- 🛡️ **Attestations**: Build provenance y verificaciones firmadas
- ⚡ **GitHub Actions Cache**: Cache distribuido ultra-rápido
- 🎯 **Smart tagging**: Tags automáticos según evento

**Configuración optimizada**:
- Runners: `ubuntu-latest` (GitHub-hosted)
- BuildKit con QEMU para cross-platform builds
- Cache: GitHub Actions cache (type=gha)
- Security: Trivy + GitHub Security tab integration
- Provenance: Firmado con GitHub OIDC

## Configuración Requerida

### Permisos de GitHub

Los workflows requieren estos permisos (ya configurados en los archivos):
- `contents: read` - Para leer el código del repositorio
- `packages: write` - Para subir imágenes al Container Registry

### Variables de Entorno

- `REGISTRY`: `ghcr.io` (GitHub Container Registry)
- `IMAGE_NAME`: Se establece automáticamente como `${{ github.repository }}`

## Uso

### Para Construcción Manual

#### Opción 1: Sin tag específico
1. Ve a Actions en tu repositorio de GitHub
2. Selecciona "Build and Push Docker Image"
3. Haz clic en "Run workflow" (deja el campo tag vacío)
4. La imagen estará disponible en `ghcr.io/[usuario]/[repo]:manual-YYYYMMDD-HHMMSS`

#### Opción 2: Con tag personalizado
1. Ve a Actions en tu repositorio de GitHub
2. Selecciona "Build and Push Docker Image"
3. Haz clic en "Run workflow"
4. Introduce tu tag personalizado (ej: `dev`, `test`, `feature-xyz`)
5. La imagen estará disponible en `ghcr.io/[usuario]/[repo]:tu-tag`

### Para Crear un Release Oficial

```bash
# Crear y subir un tag
git tag v1.0.0
git push origin v1.0.0
```

Esto automáticamente:
1. 🐳 Construirá la imagen Docker con Kaniko
2. 🏷️ La subirá con tags `v1.0.0`, `1.0.0`, `1.0`, `1`, y `latest`
3. 📝 Creará un release de GitHub con notas automáticas
4. 🛡️ Generará attestations de seguridad

### Para Usar las Imágenes

```bash
# Última versión estable
docker pull ghcr.io/[usuario]/[repo]:latest

# Versión específica
docker pull ghcr.io/[usuario]/[repo]:v1.0.0
```

## Troubleshooting

### Error de Permisos

Si obtienes errores de permisos al subir al registry:

1. Verifica que el repositorio tenga habilitado GitHub Container Registry
2. Ve a Settings > Actions > General > Workflow permissions
3. Selecciona "Read and write permissions"

### Error de Build

Si el build falla:

1. Verifica que el `Dockerfile` esté en la raíz del proyecto
2. Revisa que todas las dependencias estén especificadas correctamente
3. Comprueba los logs del workflow para errores específicos

### Imagen No Encontrada

Si no puedes encontrar la imagen:

1. Ve a la página del repositorio en GitHub
2. Busca la sección "Packages" en la barra lateral derecha
3. Las imágenes aparecerán allí una vez subidas exitosamente
