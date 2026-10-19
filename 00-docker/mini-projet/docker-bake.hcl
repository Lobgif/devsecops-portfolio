variable "frontend_version" {
  default = "1.0.0"
}

variable "backend_version" {
  default = "1.0.17"
}

group "default" {
  targets = [
    "backend",
    "frontend"
  ]
}

target "backend" {
  context  = "./backend"
  dockerfile = "Dockerfile"
  tags = ["backend:${backend_version}"]
  platforms = ["linux/amd64", "linux/arm64"]
}

target "frontend" {
  context = "./frontend"
  dockerfile = "Dockerfile"
  tags = ["frontend:${frontend_version}"]
  platforms = ["linux/amd64", "linux/arm64"]
}