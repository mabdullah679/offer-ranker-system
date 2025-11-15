resource "google_cloud_run_v2_service" "offer_api" {
  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = var.image
      ports {
        container_port = 8080
      }
      env {
        name  = "ENV"
        value = var.environment
      }
      env {
        name  = "PORT"
        value = "8080"
      }
    }

    max_instance_request_concurrency = var.concurrency
    service_account                  = var.service_account_email

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
  }

  traffic {
    percent         = 100
    type            = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    revision        = ""
  }
}

resource "google_cloud_run_v2_service_iam_member" "invoker" {
  location = google_cloud_run_v2_service.offer_api.location
  project  = google_cloud_run_v2_service.offer_api.project
  name     = google_cloud_run_v2_service.offer_api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
