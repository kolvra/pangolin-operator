# GitHub Workflows

Este directorio contiene los workflows de GitHub Actions para el proyecto Pangolin Operator.

## Workflows Disponibles

### 1. `docker-build-push.yml` - Build y Push Automático

**Propósito**: Construye y sube imágenes Docker automáticamente para diferentes eventos.

**Se ejecuta cuando**:
- Se crean tags que empiecen con `v`
- Manualmente via `workflow_dispatch`

**Lo que hace**:
- Construye la imagen Docker usando BuildKit rootless (seguro, moderno)
- Sube la imagen al GitHub Container Registry (`ghcr.io`)
- Genera tags apropiados basados en el evento que lo disparó
- Utiliza cache inline para builds más rápidos
- Genera attestations de seguridad para la imagen
- Se ejecuta en tu cluster K3s usando ARC runners

**Tags generados**:
- Para tags semver: `v1.2.3`, `1.2.3`, `1.2`, `1`, `latest`
- Para ejecución manual: `latest`

### 2. `release.yml` - Releases

**Propósito**: Workflow especializado para crear releases oficiales.

**Se ejecuta cuando**:
- Se crea un tag con formato `v*.*.*` (ej: `v1.0.0`)
- Manualmente especificando un tag

**Lo que hace**:
- Todo lo del workflow anterior, pero enfocado en releases
- Crea un release de GitHub automáticamente
- Genera notas de release automáticas
- Incluye información de las imágenes Docker en las notas

### 3. `demo.yaml` - Demo con Self-Hosted Runners

**Propósito**: Workflow de demostración para runners auto-hospedados.

## Tecnologías Utilizadas

### BuildKit Rootless para Builds Seguros

Los workflows utilizan **BuildKit** en modo rootless para construir imágenes Docker de manera segura:

**Ventajas de BuildKit Rootless**:
- 🔒 **Rootless**: No requiere privilegios root para construir imágenes
- 🛡️ **Seguro**: Desarrollado por el equipo oficial de Docker
- 🚀 **Moderno**: Tecnología actual y mantenida activamente
- 📦 **Compatible**: Funciona con cualquier registry estándar
- ⚡ **Eficiente**: Cache inline y builds paralelos optimizados
- 🔧 **Flexible**: Soporte completo para multi-stage builds

**Configuración**:
- Imagen: `moby/buildkit:rootless`
- Cache inline habilitado para optimización
- Autenticación via credenciales de GitHub

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

1. Ve a Actions en tu repositorio de GitHub
2. Selecciona "Build and Push Docker Image"
3. Haz clic en "Run workflow"
4. La imagen estará disponible en `ghcr.io/[usuario]/[repo]:latest`

### Para Crear un Release

```bash
# Crear y subir un tag
git tag v1.0.0
git push origin v1.0.0
```

Esto automáticamente:
1. Construirá la imagen Docker
2. La subirá con tags `v1.0.0`, `1.0.0`, `1.0`, `1`, y `latest`
3. Creará un release de GitHub con notas automáticas

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
