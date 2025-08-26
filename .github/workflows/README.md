# GitHub Workflows

Este directorio contiene los workflows de GitHub Actions para el proyecto Pangolin Operator.

## Workflows Disponibles

### 1. `docker-build-push.yml` - Build y Push Unificado

**Propósito**: Workflow único que maneja tanto builds manuales como releases oficiales.

**Se ejecuta cuando**:
- Se crean tags que empiecen con `v` (release automático)
- Manualmente via `workflow_dispatch` (con tag opcional)

**Lo que hace**:
- Construye la imagen Docker usando **Kaniko** (rootless, diseñado para Kubernetes)
- Sube la imagen al GitHub Container Registry (`ghcr.io`)
- Genera tags apropiados basados en el evento que lo disparó
- Utiliza cache de Kaniko para builds más rápidos
- Genera attestations de seguridad para la imagen
- Se ejecuta en tu cluster K3s usando ARC runners
- **Crea releases de GitHub automáticamente** para tags oficiales

**Tags generados**:
- **Para releases** (tags `v*`): `v1.2.3`, `1.2.3`, `1.2`, `1`, `latest`
- **Para manual con tag**: `custom-tag`, `latest` (si no es un tag especial)
- **Para manual sin tag**: `manual-YYYYMMDD-HHMMSS`

### 2. `demo.yaml` - Demo con Self-Hosted Runners

**Propósito**: Workflow de demostración para runners auto-hospedados.

## Tecnologías Utilizadas

### Kaniko para Builds Rootless en Kubernetes

El workflow utiliza **Kaniko** para construir imágenes Docker de manera segura en contenedores:

**Ventajas de Kaniko**:
- 🔒 **Rootless**: No requiere privilegios root ni Docker daemon
- 🛡️ **Kubernetes-native**: Diseñado específicamente para contenedores
- 🚀 **Simple**: Una sola imagen con todas las herramientas necesarias
- 📦 **Compatible**: Funciona con cualquier registry estándar
- ⚡ **Eficiente**: Cache integrado y builds optimizados
- 🔧 **Reliable**: Mantenido activamente por Google

**Configuración**:
- Imagen: `gcr.io/kaniko-project/executor:debug`
- Cache habilitado con TTL de 24 horas
- Autenticación via credenciales de GitHub
- Ejecuta como usuario root dentro del contenedor (seguro)

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
