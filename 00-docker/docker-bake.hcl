variable "TAG" {
  default = "v1.0.0"
}

group "default" {
  targets = ["frontend", "backend"]
}

target "frontend" {
  context    = "."
  dockerfile = "frontend/Dockerfile"
  tags       = ["frontend/app:${TAG}"]
}

target "backend" {
  context    = "."
  dockerfile = "backend/Dockerfile"
  tags       = ["backend/app:${TAG}"]
}