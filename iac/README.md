# What is in this
Infrastructure configuration

# Preqrequisites
1. Ensure you have sufficient rights on the project (e.g. owner)
1. Create repository connection in Cloud Build to your Github repository (make sure to select the region that you are going to set in `terraform.tfvars` in CloudBuild when doing this)

# How to use
1. Ensure the prerequisites
1. Create `terraform.tfvars` file and enter your configuration of variables as describe in `variables.tf`
1. `gcloud auth application-default login` to make sure terraform can act on your behalf.
1. `terraform apply`
1. Confirm with `Yes`
1. Profit!
