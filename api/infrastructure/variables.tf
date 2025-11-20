variable "project_id" {
  description = "GCP project ID where resources will be created"
  type        = string
}

variable "region" {
  description = "GCP region for Cloud Run"
  type        = string
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
}

variable "image" {
  description = "Container image deployed to Cloud Run (Artifact Registry path)"
  type        = string
}

variable "service_account_email" {
  description = "Service account email Cloud Run should use"
  type        = string
}

# Optional: model bucket (present for workflow compatibility; unused in current resources)
variable "gcs_model_bucket" {
  description = "GCS bucket holding model artifacts (unused by current module)"
  type        = string
  default     = ""
}


variable "max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 3
}

variable "min_instances" {
  description = "Minimum number of Cloud Run instances"
  type        = number
  default     = 0
}

variable "concurrency" {
  description = "Maximum concurrent requests per instance"
  type        = number
  default     = 80
}

variable "environment" {
  description = "Environment label exposed to the container"
  type        = string
  default     = "dev"
}
