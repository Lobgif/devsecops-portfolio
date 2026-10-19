#!/bin/bash
set -e

VERSION="1.0.0"
IMAGE_NAME="myapp-nginx"

# 1. Créer conteneur
container=$(buildah from alpine:3.21)

# 2. Installer paquets
buildah run "$container" apk add --no-cache nginx

# 3. Configurer
buildah config --cmd "nginx -g 'daemon off;'" "$container"
buildah config --port 80 "$container"
buildah config --label "version=$VERSION" "$container"

# 4. Créer image
buildah commit "$container" "$IMAGE_NAME:$VERSION"

# 5. Nettoyer
buildah rm "$container"

echo "✅ Image $IMAGE_NAME:$VERSION créée avec succès"
