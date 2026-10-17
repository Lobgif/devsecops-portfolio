variable "TAG" {
  default = "v1.0.0"
}

group "default" {
  targets = ["frontend", "backend"]
}

target "base" {
  context        = "."
  platforms      = ["linux/amd64", "linux/arm64"]
  output = ["type=docker"]
  labels = {
    "maintainer" = "devsecops@gmail.com"
    "project"    = "app"
    "org.opencontainers.image.source" = "https://gitlab.com/personnel4344847/devsecops-portfolio.git"
    "org.opencontainers.image.description" = "Forum citoyen ivoirien"
  }
}

target "frontend" {
  inherits   = ["base"]
  dockerfile = "frontend/Dockerfile"
  tags       = ["frontend/app:${TAG}"]
}

target "backend" {
  inherits   = ["base"]
  dockerfile = "backend/Dockerfile"
  tags       = ["backend/app:${TAG}"]
}