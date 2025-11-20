output "cloud_run_url" {
  description = "Public URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.offer_api.uri
}

output "service_url" {
  description = "Alias for Cloud Run URL (used by workflows)"
  value       = google_cloud_run_v2_service.offer_api.uri
}

output "cloud_run_service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.offer_api.name
}

output "region" {
  description = "Deployment region"
  value       = var.region
}

output "project_id" {
  description = "GCP project ID"
  value       = var.project_id
}

output "artifact_registry_image" {
  description = "Container image pushed to Artifact Registry"
  value       = var.image
}
