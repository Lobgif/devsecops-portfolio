variable "TAG" {
  default = "dev"
}

variable "REGISTRY" {
  default = "ghcr.io/lahigic"
}

variable "GIT_SHA" { default = "" }

variable "PLATFORMS" { default = ["linux/amd64"] }

group "default" {
  targets = ["frontend", "backend"]
}

target "base" {
  context        = "."
  platforms      = ["linux/amd64", "linux/arm64"]
  # output = ["type=registry"]
  output = ["type=docker"]
  attest = [
    "type=provenance,mode=max",
    "type=sbom"
  ]
  # cache-from = ["type=registry,ref=${REGISTRY}/app:buildcache:${TAG}"]
  # cache-to = ["type=registry,ref=${REGISTRY}/app:buildcache:${TAG},mode=max"]
  labels = {
    "maintainer" = "devsecops@gmail.com"
    "project"    = "app"
    "org.opencontainers.image.source" = "https://gitlab.com/personnel4344847/devsecops-portfolio.git"
    "org.opencontainers.image.description" = "Forum citoyen ivoirien"
    "org.opencontainers.image.created"  = "${timestamp()}"
    "org.opencontainers.image.revision" = GIT_SHA
  }
}

target "frontend" {
  inherits   = ["base"]
  dockerfile = "frontend/Dockerfile"
  tags       = ["${REGISTRY}/frontend/app:${TAG}"]
}

target "backend" {
  inherits   = ["base"]
  dockerfile = "backend/Dockerfile"
  tags       = ["${REGISTRY}/backend/app:${TAG}"]
}