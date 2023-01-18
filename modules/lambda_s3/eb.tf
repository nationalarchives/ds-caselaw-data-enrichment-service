resource "aws_cloudwatch_event_rule" "db_backup" {
  name                = "db-backup"
  description         = "Trigger lambda to perform db snapshot"
  is_enabled          = false # update last
  schedule_expression = "cron(0 12 * * ? *)"
}

#resource "aws_cloudwatch_event_target" "db_backup_lambda" {
#  arn   = module.db_backup_lambda.lambda_function_arn
#  rule  = aws_cloudwatch_event_rule.db_backup.name
#  input = jsonencode({ "db-name" : "tna-metadata-db-${local.environment}-1" })
#}
