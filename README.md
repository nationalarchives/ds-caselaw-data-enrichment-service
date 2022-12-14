# ds-caselaw-data-enrichment-service

## CICD Workflow
- When a pull request is opened a series of checks are made, against both staging and production:
  - Python Black (Formats python code correctly)
  - Python iSort (Orders imports correctly)
  - TFLint (Terraform Linter)
  - Terraform Validate
  - Terraform init.
  - Terraform Plan (A plan of the infrastructure changes for that environment)
- If the checks fail due to Python Black. 
A message such as `Oh no! 💥 💔 💥 13 files would be reformatted, 5 files would be left unchanged.` 
  - To fix this, install black locally `pip install black`, then run `black .` and commit the reformatted code.
- If the check fails due to iSort. A message such as `ERROR: Imports are incorrectly sorted.`
  - To fix this, install isort locally `pip install isort`, then run `isort .`
- TFLint will explain any errors it finds. 
- Terraform plan needs to be inspected before merging code to ensure the right thing is being applied. 
Do not assume that a green build is going to build what you want to be built. 
- Upon merge, staging environment docker images will be built and pushed to ECR, staging environment Terraform code will be applied.
On success of the staging environment, production environment docker images will be built and pushed to ECR, production environment Terraform code will be applied.
