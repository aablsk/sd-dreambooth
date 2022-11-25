# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

resource "google_service_account" "vertexai_prediction" {
  project    = var.project_id
  account_id = "vertexai-prediction"
}

resource "google_storage_bucket" "render_results" {
  project                     = var.project_id
  name                        = "render-results_${var.project_id}"
  uniform_bucket_level_access = true
  location                    = var.region
  force_destroy               = true # TODO: remove this so buckets don't get deleted on terraform destroy
}

# give SA access to write images to bucket
resource "google_storage_bucket_iam_member" "prediction_results" {
  bucket = google_storage_bucket.render_results.name

  member = "serviceAccount:${google_service_account.vertexai_prediction.email}"
  role   = "roles/storage.admin"
}

resource "google_service_account_iam_member" "vertexai_training_impersonate_prediction" {
  service_account_id = google_service_account.vertexai_prediction.id
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.vertexai_training.email}"
}
