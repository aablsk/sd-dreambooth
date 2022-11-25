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

resource "google_service_account" "vertexai_training" {
  project    = var.project_id
  account_id = "vertexai-training"
}

resource "google_service_account_iam_member" "vertexai_training_impersonate_itself" {
  service_account_id = google_service_account.vertexai_training.id
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.vertexai_training.email}"
}


# bucket to store pipeline_artifacts
resource "google_storage_bucket" "pipeline_artifacts" {
  project                     = var.project_id
  name                        = "vertexai_pipeline_staging_${var.project_id}"
  uniform_bucket_level_access = true
  location                    = var.region
  force_destroy               = true # TODO: remove this so buckets don't get deleted on terraform destroy
}

# give SA access to write pipeline artifacts
resource "google_storage_bucket_iam_member" "pipeline_artifacts" {
  bucket = google_storage_bucket.pipeline_artifacts.name

  member = "serviceAccount:${google_service_account.vertexai_training.email}"
  role   = "roles/storage.admin"
}


# bucket to store fine-tuned models
resource "google_storage_bucket" "models" {
  project                     = var.project_id
  name                        = "stable-diffusion-dreambooth-models_${var.project_id}"
  uniform_bucket_level_access = true
  location                    = var.region
  force_destroy               = true # TODO: remove this so buckets don't get deleted on terraform destroy
}

# give SA access to write models
resource "google_storage_bucket_iam_member" "models" {
  bucket = google_storage_bucket.models.name

  member = "serviceAccount:${google_service_account.vertexai_training.email}"
  role   = "roles/storage.admin"
}

# bucket to store vertex ai pipeline definition
resource "google_storage_bucket" "pipeline_definition" {
  project                     = var.project_id
  name                        = "vertexai_pipeline_definition_${var.project_id}"
  uniform_bucket_level_access = true
  location                    = var.region
  force_destroy               = true # TODO: remove this so buckets don't get deleted on terraform destroy
}

# give SA access to read pipeline definition
resource "google_storage_bucket_iam_member" "pipeline_definition" {
  bucket = google_storage_bucket.pipeline_definition.name

  member = "serviceAccount:${google_service_account.vertexai_training.email}"
  role   = "roles/storage.objectViewer"
}

# bucket to store instance images
resource "google_storage_bucket" "instance_images" {
  project                     = var.project_id
  name                        = "instance_images_dog_${var.project_id}"
  uniform_bucket_level_access = true
  location                    = var.region
  force_destroy               = true # TODO: remove this so buckets don't get deleted on terraform destroy
}

# give SA access to read instance images
resource "google_storage_bucket_iam_member" "instance_images" {
  bucket = google_storage_bucket.instance_images.name

  member = "serviceAccount:${google_service_account.vertexai_training.email}"
  role   = "roles/storage.objectViewer"
}
