resource "google_service_account" "cloudbuild" {
  project    = var.project_id
  account_id = "cloudbuild"
}

# CI trigger configuration
resource "google_cloudbuild_trigger" "finetune-image" {
  name = "finetune-image-builder"
  location = var.region

  github {
      owner = var.repo_owner
      name = var.repo_name

      push {
        branch = "^main$"
      }
  }
  included_files = ["fine_tune/training_job/**"]
  filename = "fine_tune/training_job/cloudbuild.yaml"
  substitutions = {
      _REPO_NAME= local.app_name
  }
  service_account = google_service_account.cloudbuild.id
}


# CI trigger configuration
resource "google_cloudbuild_trigger" "render-pipeline" {
  name = "render-pipeline-definition"
  location = var.region

  github {
      owner = var.repo_owner
      name = var.repo_name

      push {
        branch = "^main$"
      }
  }
  included_files = ["fine_tune/pipeline/**"]
  filename = "fine_tune/pipeline/cloudbuild.yaml"
  substitutions = {
      _PIPELINE_BUCKET= "gs://${google_storage_bucket.pipeline_definition.name}"
  }
  service_account = google_service_account.cloudbuild.id
}
