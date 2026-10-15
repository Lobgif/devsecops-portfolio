FROM alpine:3.21@sha256:48b0309ca019d89d40f670aa1bc06e426dc0931948452e8491e3d65087abc07d

# Installer nginx et préparer son répertoire d'exécution
RUN apk add --no-cache nginx \
    && mkdir -p /run/nginx

# Metadata
LABEL org.opencontainers.image.source="https://github.com/me/app"
LABEL org.opencontainers.image.version="1.0.0"

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
