variable "aws_region" {
  description = "AWS region for the demo environment."
  type        = string
  default     = "eu-west-2"
}

variable "project_name" {
  description = "Name prefix used for AWS resources."
  type        = string
  default     = "okapi-demo"
}

variable "domain_name" {
  description = "Base DNS domain controlled by this environment."
  type        = string
  default     = "okapiapp.io"
}

variable "route53_zone_id" {
  description = "Public Route53 hosted zone ID for domain_name."
  type        = string
}

variable "okapi_hostname" {
  description = "Hostname for the Okapi UI/API."
  type        = string
  default     = "main.okapiapp.io"
}

variable "otel_hostname" {
  description = "Hostname for the OpenTelemetry demo frontend."
  type        = string
  default     = "otel.okapiapp.io"
}

variable "vpc_cidr" {
  description = "CIDR block for the demo VPC."
  type        = string
  default     = "10.42.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for the public subnet containing the fixed demo instances."
  type        = string
  default     = "10.42.1.0/24"
}

variable "okapi_instance_type" {
  description = "EC2 instance type for the Okapi stack."
  type        = string
  default     = "r7i.xlarge"
}

variable "otel_instance_type" {
  description = "EC2 instance type for the OpenTelemetry demo stack."
  type        = string
  default     = "m7i.xlarge"
}

variable "root_volume_size_gb" {
  description = "Root EBS volume size for each instance."
  type        = number
  default     = 60
}

variable "okapi_data_volume_size_gb" {
  description = "Persistent Okapi data volume size."
  type        = number
  default     = 250
}

variable "ssh_allowed_cidrs" {
  description = "Optional CIDRs allowed to SSH to demo instances. Prefer SSM and leave this empty."
  type        = list(string)
  default     = []
}

variable "okapi_image_repo" {
  description = "Container registry/repository prefix for Okapi images."
  type        = string
  default     = "ghcr.io/okapi-core"
}

variable "okapi_image_tag" {
  description = "Okapi image tag deployed by default."
  type        = string
  default     = "latest"
}

variable "postgres_password" {
  description = "Password for the Postgres admin/user-data role used by the demo."
  type        = string
  sensitive   = true
  default     = "okapi_oscar_password"
}

variable "okapi_web_db_password" {
  description = "Password for the okapi_web application database user."
  type        = string
  sensitive   = true
  default     = "okapi_web_password"
}

variable "okapi_web_migration_password" {
  description = "Password for the okapi_web migration database user."
  type        = string
  sensitive   = true
  default     = "okapi_web_migration_password"
}

variable "oscar_db_password" {
  description = "Password for the okapi_oscar application database user."
  type        = string
  sensitive   = true
  default     = "okapi_oscar_password"
}

variable "clickhouse_password" {
  description = "ClickHouse default user password."
  type        = string
  sensitive   = true
  default     = "okapi_testing_password"
}

variable "vault_root_token" {
  description = "Vault dev root token for the demo."
  type        = string
  sensitive   = true
  default     = "0d94159a1b7e9c8f563e4e9e383185dc402ef70e"
}

variable "openai_api_key" {
  description = "Optional OpenAI API key stored for Oscar. Empty means the value is not provisioned."
  type        = string
  sensitive   = true
  default     = ""
}
