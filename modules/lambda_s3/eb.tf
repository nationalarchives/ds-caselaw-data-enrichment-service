#module "eb_db_backup" {
#  source  = "terraform-aws-modules/eventbridge/aws"
#  version = "~> 0.1"
#
#  create_bus = false
#
#  rules = {
#    backup = {
#      description         = "Trigger lambda to perform db snapshot"
#      enabled             = false
#      schedule_expression = "cron(0 12 * * ? *)"
#    }
#  }
#
#  targets = {
#    backup = {
#      name  = "db-backup-lambda"
#      #arn   = module.db_backup_lambda.lambda_function_arn
#      arn   = module.lambda-fetch-xml.lambda_function_arn
#      input = jsonencode({ "db-name" : "tna-metadata-db-${local.environment}-1" })
#    }
#  }
#}
