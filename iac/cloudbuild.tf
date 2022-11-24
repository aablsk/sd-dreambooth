resource "google_service_account" "cloudbuild" {
  project    = var.project_id
  account_id = "cloudbuild"
}

# CI trigger configuration for finetuning image
resource "google_cloudbuild_trigger" "finetune-image" {
  project  = var.project_id
  name     = "finetune-image-builder"
  location = var.region

  github {
    owner = var.repo_owner
    name  = var.repo_name

    push {
      branch = "^main$"
    }
  }
  included_files = ["fine_tune/training_job/**"]
  filename       = "fine_tune/training_job/cloudbuild.yaml"
  substitutions = {
    _REPO_NAME = local.app_name
  }
  service_account = google_service_account.cloudbuild.id
}

# CI trigger configuration for rendering pipeline
resource "google_cloudbuild_trigger" "render-pipeline" {
  project  = var.project_id
  name     = "render-pipeline-definition"
  location = var.region

  github {
    owner = var.repo_owner
    name  = var.repo_name

    push {
      branch = "^main$"
    }
  }
  included_files = ["fine_tune/pipeline/**"]
  filename       = "fine_tune/pipeline/cloudbuild.yaml"
  substitutions = {
    _PIPELINE_BUCKET = "gs://${google_storage_bucket.pipeline_definition.name}"
  }
  service_account = google_service_account.cloudbuild.id
}

# CI trigger configuration
resource "google_cloudbuild_trigger" "server_image" {
  project  = var.project_id
  name     = "server-image-builder"
  location = var.region

  github {
    owner = var.repo_owner
    name  = var.repo_name

    push {
      branch = "^main$"
    }
  }
  included_files = ["server/**"]
  filename       = "server/cloudbuild.yaml"
  substitutions = {
    _REPO_NAME = local.app_name
  }
  service_account = google_service_account.cloudbuild.id
}

# give CloudBuild SA access to read pipeline definition
resource "google_storage_bucket_iam_member" "pipeline_definition_cloudbuild" {
  bucket = google_storage_bucket.pipeline_definition.name

  member = "serviceAccount:${google_service_account.cloudbuild.email}"
  role   = "roles/storage.admin"
}