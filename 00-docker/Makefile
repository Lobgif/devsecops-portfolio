# Makefile
IMAGE := ghcr.io/myorg/myapp
VERSION := $(shell git describe --tags --always)

.PHONY: build
build:
  docker run --rm \
    -v $(PWD):/workspace \
    -v ~/.docker/config.json:/kaniko/.docker/config.json:ro \
    ghcr.io/osscontainertools/kaniko:v1.28.1 \
    --context=/workspace \
    --destination=$(IMAGE):$(VERSION) \
    --cache=true \
    --cache-repo=$(IMAGE)/cache \
    --snapshot-mode=redo

.PHONY: build-debug
build-debug:
  docker run --rm \
    -v $(PWD):/workspace \
    ghcr.io/osscontainertools/kaniko:v1.28.1-debug \
    --context=/workspace \
    --destination=$(IMAGE):debug \
    --no-push \
    --verbosity=debug
