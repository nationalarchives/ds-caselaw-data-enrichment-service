# ============================================================
# ECR REPOSITORIES  (one per deployed lambda)
# ============================================================

resource "aws_ecr_repository" "enrichment" {
  name = "${local.name}-ecr-repository-enrichment-${local.environment}"
  image_scanning_configuration { scan_on_push = true }
  tags = local.tags
}
resource "aws_ecr_lifecycle_policy" "enrichment_retention" {
  repository = aws_ecr_repository.enrichment.name
  policy     = file("${path.module}/retention_policy.json")
}

resource "aws_ecr_repository" "db-backup" {
  name = "${local.name}-ecr-repository-db-backup-${local.environment}"
  image_scanning_configuration { scan_on_push = true }
  tags = local.tags
}
resource "aws_ecr_lifecycle_policy" "db_backup_retention" {
  repository = aws_ecr_repository.db-backup.name
  policy     = file("${path.module}/retention_policy.json")
}

resource "aws_ecr_repository" "legislation-update" {
  name = "${local.name}-ecr-repository-legislation-update-${local.environment}"
  image_scanning_configuration { scan_on_push = true }
  tags = local.tags
}
resource "aws_ecr_lifecycle_policy" "lu_retention" {
  repository = aws_ecr_repository.legislation-update.name
  policy     = file("${path.module}/retention_policy.json")
}

resource "aws_ecr_repository" "rules-update" {
  name = "${local.name}-ecr-repository-rules-update-${local.environment}"
  image_scanning_configuration { scan_on_push = true }
  tags = local.tags
}
resource "aws_ecr_lifecycle_policy" "ru_retention" {
  repository = aws_ecr_repository.rules-update.name
  policy     = file("${path.module}/retention_policy.json")
}

# ============================================================
# API CREDENTIALS  (Secrets Manager)
# ============================================================

resource "aws_secretsmanager_secret" "api_credentials" {
  description             = "Combined secret for API username and password"
  name                    = "${local.name}-api-credentials-${local.environment}"
  recovery_window_in_days = 0
  tags                    = local.tags
}

resource "aws_secretsmanager_secret_version" "api_credentials" {
  secret_id = aws_secretsmanager_secret.api_credentials.id
  secret_string = jsonencode({
    username = var.api_username
    password = var.api_password
  })
}

# ============================================================
# SPARQL CREDENTIALS  (for update_legislation_table)
# ============================================================

resource "aws_secretsmanager_secret" "sparql_credentials" {
  description             = "Combined secret for SPARQL username and password"
  name                    = "${local.name}-sparql-credentials-${local.environment}"
  recovery_window_in_days = 0
  tags                    = local.tags
}

resource "aws_secretsmanager_secret_version" "sparql_credentials" {
  secret_id = aws_secretsmanager_secret.sparql_credentials.id
  secret_string = jsonencode({
    username = var.sparql_username
    password = var.sparql_password
  })
}

# ============================================================
# ENRICHMENT LAMBDA  (consolidated pipeline)
# ============================================================

module "lambda-enrichment" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "8.8.0"

  function_name  = "${local.name}-${local.environment}-enrichment"
  package_type   = "Image"
  create_package = false
  handler        = "index.handler"
  image_uri      = "${aws_ecr_repository.enrichment.repository_url}:${var.container_image_tag}"

  create_current_version_allowed_triggers = false

  allowed_triggers = {
    vciteCallback = {
      service    = "s3"
      principal  = "s3.amazonaws.com"
      source_arn = module.vcite_enriched_bucket.s3_bucket_arn
    }
  }

  timeout     = 900
  memory_size = 10240

  attach_policy_statements = true
  policy_statements = {
    s3_read_rules = {
      effect    = "Allow"
      actions   = ["s3:HeadObject", "s3:GetObject", "s3:GetObjectVersion"]
      resources = ["${module.rules_bucket.s3_bucket_arn}/*"]
    }
    s3_put_vcite = {
      effect    = "Allow"
      actions   = ["s3:PutObject", "s3:PutObjectAcl"]
      resources = ["${module.vcite_enriched_bucket.s3_bucket_arn}/*"]
    }
    s3_read_vcite = {
      effect    = "Allow"
      actions   = ["s3:HeadObject", "s3:GetObject", "s3:GetObjectVersion"]
      resources = ["${module.vcite_enriched_bucket.s3_bucket_arn}/*"]
    }
    kms = {
      effect  = "Allow"
      actions = ["kms:Encrypt", "kms:DescribeKey", "kms:GenerateDataKey", "kms:Decrypt", "kms:ReEncryptTo"]
      resources = [
        module.rules_bucket.kms_key_arn,
        module.vcite_enriched_bucket.kms_key_arn,
      ]
    }
    ssm_get_parameter = {
      effect    = "Allow"
      actions   = ["ssm:GetParameters", "ssm:GetParameter", "ssm:GetParametersByPath"]
      resources = [aws_ssm_parameter.vCite.arn]
    }
    secrets_get = {
      effect  = "Allow"
      actions = ["secretsmanager:GetResourcePolicy", "secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret", "secretsmanager:ListSecretVersionIds"]
      resources = [
        aws_secretsmanager_secret.api_credentials.arn,
        var.postgress_master_password_secret_id,
      ]
    }
    sqs_consume = {
      effect    = "Allow"
      actions   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
      resources = [aws_sqs_queue.enrichment_queue.arn]
    }
    log_lambda = {
      effect    = "Allow"
      actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
      resources = ["*"]
    }
  }

  attach_policies    = true
  number_of_policies = 2
  policies = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
  ]

  assume_role_policy_statements = {
    account_root = {
      effect  = "Allow"
      actions = ["sts:AssumeRole"]
      principals = {
        account_principal = {
          type        = "Service"
          identifiers = ["lambda.amazonaws.com"]
        }
      }
    }
  }

  vpc_security_group_ids = [var.default_security_group_id]
  vpc_subnet_ids         = var.aws_subnets_private_ids

  environment_variables = {
    API_SECRET_NAME         = aws_secretsmanager_secret.api_credentials.name
    API_ENDPOINT            = local.api_endpoint
    DATABASE_NAME           = "rules"
    DATABASE_USERNAME       = "root"
    DATABASE_PORT           = "5432"
    DATABASE_HOSTNAME       = var.postgress_hostname
    DB_PASSWORD_SECRET_NAME = var.postgress_master_password_secret_id
    TABLE_NAME              = "rules"
    USERNAME                = "root"
    PORT                    = "5432"
    HOSTNAME                = var.postgress_hostname
    RULES_FILE_BUCKET       = module.rules_bucket.s3_bucket_id
    RULES_FILE_KEY          = "citation_patterns.jsonl"
    VCITE_BUCKET            = "vcite-tna-files"
    VCITE_ENRICHED_BUCKET   = module.vcite_enriched_bucket.s3_bucket_id
    VCITE_ENABLED           = var.vcite_enabled
  }

  cloudwatch_logs_retention_in_days = 365
  tags                              = local.tags
}

resource "aws_lambda_event_source_mapping" "sqs_enrichment_trigger" {
  event_source_arn = aws_sqs_queue.enrichment_queue.arn
  enabled          = true
  function_name    = module.lambda-enrichment.lambda_function_arn
  batch_size       = 1
}

# ============================================================
# DB BACKUP LAMBDA
# ============================================================

module "db_backup_lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "8.8.0"

  function_name = "${local.name}-${local.environment}-db-backup"
  description   = "Takes a snapshot each day"

  create_package                          = false
  create_current_version_allowed_triggers = false
  maximum_retry_attempts                  = 0

  image_uri     = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${local.region}.amazonaws.com/tna-s3-tna-ecr-repository-db-backup-${local.environment}:latest"
  package_type  = "Image"
  architectures = ["x86_64"]
  timeout       = 900

  attach_policies    = true
  number_of_policies = 2
  policies = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
  ]

  attach_policy_statements = true
  policy_statements = {
    rds = {
      effect    = "Allow"
      actions   = ["rds:Create*", "rds:StartExportTask", "rds:Describe*"]
      resources = ["*"]
    }
    kms_get_key = {
      effect    = "Allow"
      actions   = ["kms:Encrypt", "kms:DescribeKey", "kms:GenerateDataKey", "kms:Decrypt", "kms:ReEncryptTo"]
      resources = ["*"]
    }
    iam = {
      effect    = "Allow"
      actions   = ["iam:PassRole"]
      resources = [module.db_backup_lambda.lambda_role_arn]
    }
  }

  environment_variables = { environment = local.environment }

  allowed_triggers = {
    db_backup = {
      principal  = "events.amazonaws.com"
      source_arn = aws_cloudwatch_event_rule.db_backup.arn
    }
  }

  vpc_security_group_ids = [var.default_security_group_id]
  vpc_subnet_ids         = var.aws_subnets_private_ids

  depends_on = [aws_ecr_repository.db-backup]
}

# ============================================================
# UPDATE LEGISLATION TABLE LAMBDA
# ============================================================

module "lambda-update-legislation-table" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "8.8.0"

  function_name  = "${local.name}-${local.environment}-update-legislation-table"
  package_type   = "Image"
  create_package = false
  runtime        = "python3.13"
  image_uri      = "${aws_ecr_repository.legislation-update.repository_url}:${var.container_image_tag}"
  handler        = "index.handler"
  source_path    = "${var.lambda_source_path}update_legislation_table"

  create_current_version_allowed_triggers = false

  timeout     = 60
  memory_size = 512

  attach_policies    = true
  number_of_policies = 2
  policies = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
  ]

  attach_policy_statements = true
  policy_statements = {
    secrets_get = {
      effect  = "Allow"
      actions = ["secretsmanager:GetResourcePolicy", "secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret", "secretsmanager:ListSecretVersionIds"]
      resources = [
        var.postgress_master_password_secret_id,
        aws_secretsmanager_secret.sparql_credentials.arn,
      ]
    }
  }

  assume_role_policy_statements = {
    account_root = {
      effect  = "Allow"
      actions = ["sts:AssumeRole"]
      principals = {
        account_principal = { type = "Service", identifiers = ["lambda.amazonaws.com"] }
      }
    }
  }

  vpc_security_group_ids = [var.default_security_group_id]
  vpc_subnet_ids         = var.aws_subnets_private_ids

  environment_variables = {
    DATABASE_NAME           = "rules"
    DATABASE_USERNAME       = "root"
    DATABASE_HOSTNAME       = var.postgress_hostname
    DATABASE_PORT           = "5432"
    DB_PASSWORD_SECRET_NAME = var.postgress_master_password_secret_id
    SPARQL_SECRET_NAME      = aws_secretsmanager_secret.sparql_credentials.name
    USERNAME                = "root"
    PORT                    = "5432"
    HOSTNAME                = var.postgress_hostname
  }

  cloudwatch_logs_retention_in_days = 365
  tags                              = local.tags
}

resource "aws_cloudwatch_event_rule" "update_legislation_table" {
  name                = "${local.name}-${local.environment}-update-legislation-table"
  description         = "Weekly trigger for update-legislation-table lambda"
  state               = "ENABLED"
  schedule_expression = "cron(0 2 ? * SUN *)"
}

resource "aws_cloudwatch_event_target" "update_legislation_table_lambda" {
  arn  = module.lambda-update-legislation-table.lambda_function_arn
  rule = aws_cloudwatch_event_rule.update_legislation_table.name
}

resource "aws_lambda_permission" "update_legislation_table_allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-update-legislation-table.lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.update_legislation_table.arn
}

# ============================================================
# UPDATE RULES PROCESSOR LAMBDA
# ============================================================

module "lambda-update-rules-processor" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "8.8.0"

  function_name  = "${local.name}-${local.environment}-update-rules-processor"
  package_type   = "Image"
  create_package = false
  runtime        = "python3.13"
  image_uri      = "${aws_ecr_repository.rules-update.repository_url}:${var.container_image_tag}"
  handler        = "index.handler"
  source_path    = "${var.lambda_source_path}update_rules_processor"

  create_current_version_allowed_triggers = false

  timeout     = 60
  memory_size = 512

  attach_policies    = true
  number_of_policies = 2
  policies = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
  ]

  attach_policy_statements = true
  policy_statements = {
    s3_read = {
      effect    = "Allow"
      actions   = ["s3:HeadObject", "s3:GetObject", "s3:GetObjectVersion"]
      resources = ["${module.rules_bucket.s3_bucket_arn}/*"]
    }
    s3_put = {
      effect    = "Allow"
      actions   = ["s3:PutObject", "s3:PutObjectAcl"]
      resources = ["${module.rules_bucket.s3_bucket_arn}/*"]
    }
    kms_get_key = {
      effect    = "Allow"
      actions   = ["kms:Encrypt", "kms:DescribeKey", "kms:GenerateDataKey", "kms:Decrypt", "kms:ReEncryptTo"]
      resources = [module.rules_bucket.kms_key_arn]
    }
    secrets_get = {
      effect    = "Allow"
      actions   = ["secretsmanager:GetResourcePolicy", "secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret", "secretsmanager:ListSecretVersionIds"]
      resources = [var.postgress_master_password_secret_id]
    }
    log_lambda = {
      effect    = "Allow"
      actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
      resources = ["*"]
    }
  }

  allowed_triggers = {
    S3BucketUpload = {
      service    = "s3"
      principal  = "s3.amazonaws.com"
      source_arn = module.rules_bucket.s3_bucket_arn
    }
  }

  assume_role_policy_statements = {
    account_root = {
      effect  = "Allow"
      actions = ["sts:AssumeRole"]
      principals = {
        account_principal = { type = "Service", identifiers = ["lambda.amazonaws.com"] }
      }
    }
  }

  vpc_security_group_ids = [var.default_security_group_id]
  vpc_subnet_ids         = var.aws_subnets_private_ids

  environment_variables = {
    DATABASE_NAME           = "rules"
    DATABASE_USERNAME       = "root"
    DATABASE_HOSTNAME       = var.postgress_hostname
    DATABASE_PORT           = "5432"
    DB_PASSWORD_SECRET_NAME = var.postgress_master_password_secret_id
    TABLE_NAME              = "rules"
    USERNAME                = "root"
    PORT                    = "5432"
    HOSTNAME                = var.postgress_hostname
  }

  cloudwatch_logs_retention_in_days = 365
  tags                              = local.tags
}

# ============================================================
# CLOUDWATCH ALARMS
# ============================================================

locals {
  lambda_function_names = [
    "${local.name}-${local.environment}-enrichment",
    "${local.name}-${local.environment}-db-backup",
    "${local.name}-${local.environment}-update-rules-processor",
    "${local.name}-${local.environment}-update-legislation-table",
  ]
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors_alarm" {
  count               = length(local.lambda_function_names)
  alarm_description   = "${local.lambda_function_names[count.index]} Error"
  alarm_name          = "${local.lambda_function_names[count.index]} Error"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  unit                = "Count"
  datapoints_to_alarm = "1"
  namespace           = "AWS/Lambda"
  period              = "180"
  statistic           = "Sum"
  threshold           = "0"
  dimensions = {
    FunctionName = local.lambda_function_names[count.index]
  }
  alarm_actions = [aws_sns_topic.enrichment_error_alerts.arn]
}

# ============================================================
# MISC
# ============================================================

resource "aws_ssm_parameter" "vCite" {
  name  = "vCite"
  type  = "String"
  value = "off"
}
