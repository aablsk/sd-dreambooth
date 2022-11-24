resource "google_service_account" "vertexai_prediction" {
  project    = var.project_id
  account_id = "vertexai-prediction"
}

resource "google_storage_bucket" "render_results" {
  project                     = var.project_id
  name                        = "render-results_${var.project_id}"
  uniform_bucket_level_access = true
  location                    = var.region
  force_destroy               = true # do not do this in production!
}

# give SA access to write images to bucket
resource "google_storage_bucket_iam_member" "prediction_results" {
  bucket = google_storage_bucket.render_results.name

  member = "serviceAccount:${google_service_account.vertexai_prediction.email}"
  role   = "roles/storage.admin"
}
