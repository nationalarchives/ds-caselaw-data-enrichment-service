module "lambda-extract-judgement-contents" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.21.1"

  function_name = "${local.name}-${local.environment}-extract-judgement-contents"
  package_type  = var.use_container_image == true ? "Image" : "Zip"

  # Deploy as code
  handler     = "index.handler"
  runtime     = "python3.12"
  source_path = "${var.lambda_source_path}extract_judgement_contents"

  create_current_version_allowed_triggers = false # !var.use_container_image

  timeout     = 60
  memory_size = 256

  attach_policy_statements = true
  policy_statements = {
    s3_read = {
      effect = "Allow",
      actions = [
        "s3:HeadObject",
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      resources = ["${module.xml_original_bucket.s3_bucket_arn}/*"]
    },
    s3_put = {
      effect    = "Allow",
      actions   = ["s3:PutObject", "s3:PutObjectAcl"],
      resources = ["${module.text_content_bucket.s3_bucket_arn}/*"]
    },
    kms_get_key = {
      effect = "Allow",
      actions = [
        "kms:Encrypt",
        "kms:DescribeKey",
        "kms:GenerateDataKey",
        "kms:Decrypt",
        "kms:ReEncryptTo"
      ],
      resources = [module.text_content_bucket.kms_key_arn, module.xml_original_bucket.kms_key_arn]
    },
    log_lambda = {
      effect = "Allow",
      actions = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      resources = ["*"]
    }
  }

  allowed_triggers = {
    S3BucketUpload = {
      service    = "s3"
      principal  = "s3.amazonaws.com"
      source_arn = "${module.xml_original_bucket.s3_bucket_arn}"
    }
  }

  environment_variables = {
    DEST_BUCKET_NAME = "${module.text_content_bucket.s3_bucket_id}"
  }

  cloudwatch_logs_retention_in_days = 365

  tags = local.tags
}

resource "aws_s3_bucket_notification" "xml_original_bucket_notification" {
  bucket = module.xml_original_bucket.s3_bucket_id

  lambda_function {
    lambda_function_arn = module.lambda-extract-judgement-contents.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".xml"
  }
}

resource "aws_ecr_repository" "main" {
  name = "${local.name}-ecr-repository-${local.environment}"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.tags
}

resource "aws_ecr_lifecycle_policy" "main_retention" {
  repository = aws_ecr_repository.main.name
  policy     = file("${path.module}/retention_policy.json")
}

resource "aws_ecr_repository" "legislation" {
  name = "${local.name}-ecr-repository-legislation-${local.environment}"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.tags
}

resource "aws_ecr_lifecycle_policy" "leglislation_retention" {
  repository = aws_ecr_repository.legislation.name
  policy     = file("${path.module}/retention_policy.json")
}

resource "aws_ecr_repository" "abbreviations" {

  name = "${local.name}-ecr-repository-abbreviations-${local.environment}"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.tags
}

resource "aws_ecr_lifecycle_policy" "abbreviations_retention" {
  repository = aws_ecr_repository.abbreviations.name
  policy     = file("${path.module}/retention_policy.json")
}

resource "aws_ecr_repository" "legislation-provision" {
  name = "${local.name}-ecr-repository-legislation-provision-${local.environment}"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.tags
}

resource "aws_ecr_lifecycle_policy" "lp_retention" {
  repository = aws_ecr_repository.legislation-provision.name
  policy     = file("${path.module}/retention_policy.json")
}

resource "aws_ecr_repository" "oblique-references" {
  name = "${local.name}-ecr-repository-oblique-references-${local.environment}"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.tags
}

resource "aws_ecr_lifecycle_policy" "or_retention" {
  repository = aws_ecr_repository.oblique-references.name
  policy     = file("${path.module}/retention_policy.json")
}

resource "aws_ecr_repository" "legislation-update" {
  name = "${local.name}-ecr-repository-legislation-update-${local.environment}"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.tags
}

resource "aws_ecr_lifecycle_policy" "lu_retention" {
  repository = aws_ecr_repository.legislation-update.name
  policy     = file("${path.module}/retention_policy.json")
}

resource "aws_ecr_repository" "rules-update" {
  name = "${local.name}-ecr-repository-rules-update-${local.environment}"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.tags
}

resource "aws_ecr_lifecycle_policy" "ru_retention" {
  repository = aws_ecr_repository.rules-update.name
  policy     = file("${path.module}/retention_policy.json")
}

resource "random_pet" "this" {
  length = 2
}

module "lambda-determine-replacements-caselaw" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.21.1"

  function_name = "${local.name}-${local.environment}-determine-replacements-caselaw"

  package_type   = "Image"
  create_package = false

  handler = "index.handler"

  image_uri = "${aws_ecr_repository.main.repository_url}:${var.container_image_tag}"

  create_current_version_allowed_triggers = false # !var.use_container_image

  timeout     = 900
  memory_size = 10240

  attach_policy_statements = true
  policy_statements = {
    s3_read = {
      effect = "Allow",
      actions = [
        "s3:HeadObject",
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      resources = ["${module.text_content_bucket.s3_bucket_arn}/*", "${module.rules_bucket.s3_bucket_arn}/*"]
    },
    s3_put = {
      effect    = "Allow",
      actions   = ["s3:PutObject", "s3:PutObjectAcl"],
      resources = ["${module.replacements_bucket.s3_bucket_arn}/*"]
    },
    kms_get_key = {
      effect = "Allow",
      actions = [
        "kms:Encrypt",
        "kms:DescribeKey",
        "kms:GenerateDataKey",
        "kms:Decrypt",
        "kms:ReEncryptTo"
      ],
      resources = [module.text_content_bucket.kms_key_arn, module.replacements_bucket.kms_key_arn, module.rules_bucket.kms_key_arn]
    },
    secrets_get = {
      effect = "Allow",
      actions = [
        "secretsmanager:GetResourcePolicy",
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecretVersionIds"
      ],
      resources = ["${var.postgress_master_password_secret_id}"]
    },
    sqs_put_message = {
      effect = "Allow",
      actions = [
        "sqs:SendMessage",
        "sqs:GetQueueAttributes"
      ],
      "Effect" : "Allow",
      resources = [aws_sqs_queue.replacement-caselaw-queue.arn]
    },
    log_lambda = {
      effect = "Allow",
      actions = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      resources = ["*"]
    }
  }

  allowed_triggers = {
    S3BucketUpload = {
      service    = "s3"
      principal  = "s3.amazonaws.com"
      source_arn = "${module.text_content_bucket.s3_bucket_arn}"
    }
  }

  attach_policies    = true
  number_of_policies = 2
  policies = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  ]

  assume_role_policy_statements = {
    account_root = {
      effect  = "Allow",
      actions = ["sts:AssumeRole"],
      principals = {
        account_principal = {
          type        = "Service",
          identifiers = ["lambda.amazonaws.com"]
        }
      }
    }
  }

  vpc_security_group_ids = [var.default_security_group_id]
  vpc_subnet_ids         = var.aws_subnets_private_ids

  environment_variables = {
    DATABASE_NAME          = "rules"
    DATABASE_USERNAME      = "root"
    DATABASE_PORT          = "5432"
    SECRET_PASSWORD_LOOKUP = "${var.postgress_master_password_secret_id}"
    REGION_NAME            = "${local.region}"
    DATABASE_HOSTNAME      = "${var.postgress_hostname}"

    # needed until we fix https://trello.com/c/lLABy4j9/791-certain-enrichment-lambda-functions-not-updating-on-merge-even-though-terraform-updating-env-variables-causing-errors
    TABLE_NAME = "rules"
    USERNAME   = "root"
    PORT       = "5432"
    HOSTNAME   = "${var.postgress_hostname}"


    DEST_QUEUE_NAME     = aws_sqs_queue.replacement-caselaw-queue.url
    RULES_FILE_BUCKET   = "${module.rules_bucket.s3_bucket_id}"
    RULES_FILE_KEY      = "citation_patterns.jsonl"
    REPLACEMENTS_BUCKET = "${module.replacements_bucket.s3_bucket_id}"
    ENRICHMENT_BUCKET   = "${module.tracking_bucket.s3_bucket_id}"
  }

  cloudwatch_logs_retention_in_days = 365

  tags = local.tags
}

module "lambda-determine-replacements-legislation" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.21.1"

  function_name = "${local.name}-${local.environment}-determine-replacements-legislation"

  package_type   = "Image"
  create_package = false

  handler   = "index.handler"
  image_uri = "${aws_ecr_repository.legislation.repository_url}:${var.container_image_tag}"

  create_current_version_allowed_triggers = false # !var.use_container_image

  timeout     = 900
  memory_size = 5120

  attach_policy_statements = true
  policy_statements = {
    s3_read = {
      effect = "Allow",
      actions = [
        "s3:HeadObject",
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      resources = ["${module.text_content_bucket.s3_bucket_arn}/*", "${module.replacements_bucket.s3_bucket_arn}/*",
      "${module.tracking_bucket.s3_bucket_arn}/*"]
    },
    s3_put = {
      effect    = "Allow",
      actions   = ["s3:PutObject", "s3:PutObjectAcl"],
      resources = ["${module.replacements_bucket.s3_bucket_arn}/*", "${module.tracking_bucket.s3_bucket_arn}/*"]
    },
    kms_get_key = {
      effect = "Allow",
      actions = [
        "kms:Encrypt",
        "kms:DescribeKey",
        "kms:GenerateDataKey",
        "kms:Decrypt",
        "kms:ReEncryptTo"
      ],
      resources = [module.text_content_bucket.kms_key_arn, module.replacements_bucket.kms_key_arn, module.tracking_bucket.kms_key_arn]
    },
    sqs_get_message = {
      effect = "Allow",
      actions = [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      "Effect" : "Allow",
      resources = [aws_sqs_queue.replacement-caselaw-queue.arn]
    },
    sqs_put_message = {
      effect = "Allow",
      actions = [
        "sqs:SendMessage",
        "sqs:GetQueueAttributes"
      ],
      "Effect" : "Allow",
      resources = [aws_sqs_queue.replacement-legislation-queue.arn]
    },
    secrets_get = {
      effect = "Allow",
      actions = [
        "secretsmanager:GetResourcePolicy",
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecretVersionIds"
      ],
      resources = ["${var.postgress_master_password_secret_id}"]
    },
    log_lambda = {
      effect = "Allow",
      actions = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      resources = ["*"]
    }
  }

  attach_policies    = true
  number_of_policies = 2
  policies = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  ]

  assume_role_policy_statements = {
    account_root = {
      effect  = "Allow",
      actions = ["sts:AssumeRole"],
      principals = {
        account_principal = {
          type        = "Service",
          identifiers = ["lambda.amazonaws.com"]
        }
      }
    }
  }

  vpc_security_group_ids = [var.default_security_group_id]
  vpc_subnet_ids         = var.aws_subnets_private_ids

  environment_variables = {
    DATABASE_NAME          = "rules"
    DATABASE_USERNAME      = "root"
    DATABASE_PORT          = "5432"
    DATABASE_HOSTNAME      = "${var.postgress_hostname}"
    SECRET_PASSWORD_LOOKUP = "${var.postgress_master_password_secret_id}"
    REGION_NAME            = "${local.region}"

    # needed until we fix https://trello.com/c/lLABy4j9/791-certain-enrichment-lambda-functions-not-updating-on-merge-even-though-terraform-updating-env-variables-causing-errors
    TABLE_NAME = "rules"
    USERNAME   = "root"
    PORT       = "5432"
    HOSTNAME   = "${var.postgress_hostname}"

    DEST_QUEUE_NAME = aws_sqs_queue.replacement-legislation-queue.url

    REPLACEMENTS_BUCKET = "${module.replacements_bucket.s3_bucket_id}"
    SOURCE_BUCKET       = "${module.text_content_bucket.s3_bucket_arn}"
    ENRICHMENT_BUCKET   = "${module.tracking_bucket.s3_bucket_id}"
  }

  cloudwatch_logs_retention_in_days = 365

  tags = local.tags
}


module "lambda-determine-replacements-abbreviations" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.21.1"

  function_name = "${local.name}-${local.environment}-determine-replacements-abbreviations"

  package_type   = "Image"
  create_package = false

  handler = "index.handler"

  image_uri = "${aws_ecr_repository.abbreviations.repository_url}:${var.container_image_tag}"

  create_current_version_allowed_triggers = false # !var.use_container_image

  timeout     = 900
  memory_size = 10240 # maxing out

  attach_policy_statements = true
  policy_statements = {
    s3_read = {
      effect = "Allow",
      actions = [
        "s3:HeadObject",
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      resources = ["${module.text_content_bucket.s3_bucket_arn}/*", "${module.replacements_bucket.s3_bucket_arn}/*"]
    },
    s3_put = {
      effect    = "Allow",
      actions   = ["s3:PutObject", "s3:PutObjectAcl"],
      resources = ["${module.replacements_bucket.s3_bucket_arn}/*"]
    },
    kms_get_key = {
      effect = "Allow",
      actions = [
        "kms:Encrypt",
        "kms:DescribeKey",
        "kms:GenerateDataKey",
        "kms:Decrypt",
        "kms:ReEncryptTo"
      ],
      resources = [module.text_content_bucket.kms_key_arn, module.replacements_bucket.kms_key_arn]
    },
    sqs_get_message = {
      effect = "Allow",
      actions = [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      "Effect" : "Allow",
      resources = [aws_sqs_queue.replacement-legislation-queue.arn]
    },

    sqs_put_message = {
      effect = "Allow",
      actions = [
        "sqs:SendMessage",
        "sqs:GetQueueAttributes"
      ],
      "Effect" : "Allow",
      resources = [aws_sqs_queue.replacement-abbreviations-queue.arn]
    },
    log_lambda = {
      effect = "Allow",
      actions = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      resources = ["*"]
    }
  }

  attach_policies    = true
  number_of_policies = 2
  policies = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  ]

  assume_role_policy_statements = {
    account_root = {
      effect  = "Allow",
      actions = ["sts:AssumeRole"],
      principals = {
        account_principal = {
          type        = "Service",
          identifiers = ["lambda.amazonaws.com"]
        }
      }
    }
  }

  vpc_security_group_ids = [var.default_security_group_id]
  vpc_subnet_ids         = var.aws_subnets_private_ids

  environment_variables = {

    DEST_QUEUE_NAME     = aws_sqs_queue.replacement-abbreviations-queue.url
    REPLACEMENTS_BUCKET = "${module.replacements_bucket.s3_bucket_id}"
    SOURCE_BUCKET       = "${module.text_content_bucket.s3_bucket_arn}"
  }

  cloudwatch_logs_retention_in_days = 365

  tags = local.tags
}

module "lambda-determine-legislation-provisions" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.21.1"

  function_name  = "${local.name}-${local.environment}-determine-legislation-provisions"
  package_type   = "Image"
  create_package = false

  handler = "index.handler"

  image_uri = "${aws_ecr_repository.legislation-provision.repository_url}:${var.container_image_tag}"

  create_current_version_allowed_triggers = false # !var.use_container_image

  timeout     = 900
  memory_size = 5120

  attach_policy_statements = true
  policy_statements = {
    s3_read = {
      effect = "Allow",
      actions = [
        "s3:HeadObject",
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      resources = ["${module.xml_second_phase_enriched_bucket.s3_bucket_arn}/*"]
    },
    s3_put = {
      effect    = "Allow",
      actions   = ["s3:PutObject", "s3:PutObjectAcl"],
      resources = ["${module.xml_third_phase_enriched_bucket.s3_bucket_arn}/*"]
    },
    kms_get_key = {
      effect = "Allow",
      actions = [
        "kms:Encrypt",
        "kms:DescribeKey",
        "kms:GenerateDataKey",
        "kms:Decrypt",
        "kms:ReEncryptTo"
      ],
      resources = [module.xml_second_phase_enriched_bucket.kms_key_arn, module.xml_third_phase_enriched_bucket.kms_key_arn]
    },
    log_lambda = {
      effect = "Allow",
      actions = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      resources = ["*"]
    }
  }

  attach_policies    = true
  number_of_policies = 2
  policies = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  ]

  assume_role_policy_statements = {
    account_root = {
      effect  = "Allow",
      actions = ["sts:AssumeRole"],
      principals = {
        account_principal = {
          type        = "Service",
          identifiers = ["lambda.amazonaws.com"]
        }
      }
    }
  }

  allowed_triggers = {
    S3BucketUpload = {
      service    = "s3"
      principal  = "s3.amazonaws.com"
      source_arn = "${module.xml_second_phase_enriched_bucket.s3_bucket_arn}"
    }
  }

  vpc_security_group_ids = [var.default_security_group_id]
  vpc_subnet_ids         = var.aws_subnets_private_ids

  environment_variables = {
    DEST_BUCKET = "${module.xml_third_phase_enriched_bucket.s3_bucket_id}"
  }

  cloudwatch_logs_retention_in_days = 365

  tags = local.tags
}

module "lambda-determine-oblique-references" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.21.1"

  function_name  = "${local.name}-${local.environment}-determine-oblique-references"
  package_type   = "Image"
  create_package = false

  handler   = "index.handler"
  image_uri = "${aws_ecr_repository.oblique-references.repository_url}:${var.container_image_tag}"

  create_current_version_allowed_triggers = false # !var.use_container_image

  timeout     = 900
  memory_size = 5120

  attach_policy_statements = true
  policy_statements = {
    s3_read = {
      effect = "Allow",
      actions = [
        "s3:HeadObject",
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      resources = ["${module.xml_enriched_bucket.s3_bucket_arn}/*"]
    },
    s3_put = {
      effect    = "Allow",
      actions   = ["s3:PutObject", "s3:PutObjectAcl"],
      resources = ["${module.xml_second_phase_enriched_bucket.s3_bucket_arn}/*"]
    },
    kms_get_key = {
      effect = "Allow",
      actions = [
        "kms:Encrypt",
        "kms:DescribeKey",
        "kms:GenerateDataKey",
        "kms:Decrypt",
        "kms:ReEncryptTo"
      ],
      resources = [module.xml_enriched_bucket.kms_key_arn, module.xml_second_phase_enriched_bucket.kms_key_arn]
    },
    log_lambda = {
      effect = "Allow",
      actions = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      resources = ["*"]
    }
  }

  attach_policies    = true
  number_of_policies = 2
  policies = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  ]

  assume_role_policy_statements = {
    account_root = {
      effect  = "Allow",
      actions = ["sts:AssumeRole"],
      principals = {
        account_principal = {
          type        = "Service",
          identifiers = ["lambda.amazonaws.com"]
        }
      }
    }
  }

  allowed_triggers = {
    S3BucketUpload = {
      service    = "s3"
      principal  = "s3.amazonaws.com"
      source_arn = "${module.xml_enriched_bucket.s3_bucket_arn}"
    }
  }

  vpc_security_group_ids = [var.default_security_group_id]
  vpc_subnet_ids         = var.aws_subnets_private_ids

  environment_variables = {
    DEST_BUCKET = "${module.xml_second_phase_enriched_bucket.s3_bucket_id}"
  }

  cloudwatch_logs_retention_in_days = 365

  tags = local.tags
}

module "lambda-make-replacements" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.21.1"

  function_name = "${local.name}-${local.environment}-make-replacements"
  package_type  = var.use_container_image == true ? "Image" : "Zip"

  handler = "index.handler"
  runtime = "python3.12"

  source_path = "${var.lambda_source_path}make_replacements"

  create_current_version_allowed_triggers = false # !var.use_container_image

  timeout     = 30
  memory_size = var.memory_size

  attach_policy_statements = true
  policy_statements = {
    s3_read = {
      effect = "Allow",
      actions = [
        "s3:HeadObject",
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      resources = ["${module.xml_original_bucket.s3_bucket_arn}/*", "${module.replacements_bucket.s3_bucket_arn}/*"]
    },
    s3_put = {
      effect    = "Allow",
      actions   = ["s3:PutObject", "s3:PutObjectAcl"],
      resources = ["${module.xml_enriched_bucket.s3_bucket_arn}/*"]
    },
    kms_get_key = {
      effect = "Allow",
      actions = [
        "kms:Encrypt",
        "kms:DescribeKey",
        "kms:GenerateDataKey",
        "kms:Decrypt",
        "kms:ReEncryptTo"
      ],
      resources = [module.xml_original_bucket.kms_key_arn, module.xml_enriched_bucket.kms_key_arn, module.replacements_bucket.kms_key_arn]
    },
    sqs_get = {
      effect = "Allow",
      actions = [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      resources = ["${aws_sqs_queue.replacements-queue.arn}", "${aws_sqs_queue.replacement-caselaw-queue.arn}", "${aws_sqs_queue.replacement-legislation-queue.arn}", "${aws_sqs_queue.replacement-abbreviations-queue.arn}"]
    },
    log_lambda = {
      effect = "Allow",
      actions = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      resources = ["*"]
    }
  }


  assume_role_policy_statements = {
    account_root = {
      effect  = "Allow",
      actions = ["sts:AssumeRole"],
      principals = {
        account_principal = {
          type        = "Service",
          identifiers = ["lambda.amazonaws.com"]
        }
      }
    }
  }

  environment_variables = {
    DEST_BUCKET_NAME    = "${module.xml_enriched_bucket.s3_bucket_id}"
    REPLACEMENTS_BUCKET = "${module.replacements_bucket.s3_bucket_id}"
    SOURCE_BUCKET_NAME  = "${module.xml_original_bucket.s3_bucket_id}"
  }

  cloudwatch_logs_retention_in_days = 365

  tags = local.tags

}

resource "aws_s3_bucket_notification" "text_content_bucket_notification" {
  bucket = module.text_content_bucket.s3_bucket_id

  lambda_function {
    lambda_function_arn = module.lambda-determine-replacements-caselaw.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
  }
}


resource "aws_s3_bucket_notification" "xml_enriched_bucket_notification" {
  bucket = module.xml_enriched_bucket.s3_bucket_id

  lambda_function {
    lambda_function_arn = module.lambda-determine-oblique-references.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".xml"
  }
}

resource "aws_s3_bucket_notification" "xml_second_phase_enriched_bucket_notification" {
  bucket = module.xml_second_phase_enriched_bucket.s3_bucket_id

  lambda_function {
    lambda_function_arn = module.lambda-determine-legislation-provisions.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".xml"
  }
}


resource "aws_s3_bucket_notification" "xml_third_phase_enriched_bucket_notification" {
  bucket = module.xml_third_phase_enriched_bucket.s3_bucket_id

  lambda_function {
    lambda_function_arn = module.lambda-validate-replacements.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".xml"
  }
}

resource "aws_s3_bucket_notification" "rules_bucket_notification" {
  bucket = module.rules_bucket.s3_bucket_id

  lambda_function {
    lambda_function_arn = module.lambda-update-rules-processor.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".csv"
  }
}

resource "aws_secretsmanager_secret" "sparql_username" {
  description             = "Secret for storing the sparql username"
  name                    = "${local.name}-sparql-username-${local.environment}"
  recovery_window_in_days = 0

  tags = local.tags
}

resource "aws_secretsmanager_secret" "sparql_password" {
  description             = "Secret for storing the sparql username"
  name                    = "${local.name}-sparql-password-${local.environment}"
  recovery_window_in_days = 0

  tags = local.tags
}

data "aws_secretsmanager_secret" "sparql_username" {
  name = "${local.name}-sparql-username-${local.environment}"
}

data "aws_secretsmanager_secret_version" "sparql_username_credentials" {
  secret_id = data.aws_secretsmanager_secret.sparql_username.id
}

data "aws_secretsmanager_secret" "sparql_password" {
  name = "${local.name}-sparql-password-${local.environment}"
}

data "aws_secretsmanager_secret_version" "sparql_password_credentials" {
  secret_id = data.aws_secretsmanager_secret.sparql_password.id
}

module "lambda-update-legislation-table" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.21.1"

  # Lambda function declaration
  function_name = "${local.name}-${local.environment}-update-legislation-table"
  package_type  = var.use_container_image == true ? "Image" : "Zip"

  runtime = "python3.12" # Setting runtime is required when building package in Docker and Lambda Layer resource.

  # Deploy as code
  handler = "index.handler"

  source_path = "${var.lambda_source_path}update_legislation_table"

  create_current_version_allowed_triggers = false # !var.use_container_image

  timeout     = 60
  memory_size = 512

  attach_policies    = true
  number_of_policies = 2
  policies = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  ]

  attach_policy_statements = true
  policy_statements = {
    secrets_get = {
      effect = "Allow",
      actions = [
        "secretsmanager:GetResourcePolicy",
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecretVersionIds"
      ],
      resources = [
        var.postgress_master_password_secret_id,
        aws_secretsmanager_secret.sparql_username.arn,
        aws_secretsmanager_secret.sparql_password.arn
      ]
    }
  }

  assume_role_policy_statements = {
    account_root = {
      effect  = "Allow",
      actions = ["sts:AssumeRole"],
      principals = {
        account_principal = {
          type        = "Service",
          identifiers = ["lambda.amazonaws.com"]
        }
      }
    }
  }

  vpc_security_group_ids = [var.default_security_group_id]

  vpc_subnet_ids = var.aws_subnets_private_ids

  environment_variables = {
    DATABASE_NAME          = "rules"
    DATABASE_USERNAME      = "root"
    DATABASE_HOSTNAME      = var.postgress_hostname
    DATABASE_PORT          = "5432"
    SECRET_PASSWORD_LOOKUP = "${var.postgress_master_password_secret_id}"
    REGION_NAME            = local.region
    SPARQL_USERNAME        = data.aws_secretsmanager_secret_version.sparql_username_credentials.secret_string
    SPARQL_PASSWORD        = data.aws_secretsmanager_secret_version.sparql_password_credentials.secret_string

    # needed until we fix https://trello.com/c/lLABy4j9/791-certain-enrichment-lambda-functions-not-updating-on-merge-even-though-terraform-updating-env-variables-causing-errors
    TABLE_NAME = "rules"
    USERNAME   = "root"
    PORT       = "5432"
    HOSTNAME   = "${var.postgress_hostname}"
  }

  cloudwatch_logs_retention_in_days = 365

  tags = local.tags

}

module "lambda-update-rules-processor" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.21.1"

  # Lambda function declaration
  function_name = "${local.name}-${local.environment}-update-rules-processor"

  package_type   = "Image"
  create_package = false

  runtime = "python3.12" # Setting runtime is required when building package in Docker and Lambda Layer resource.

  image_uri = "${aws_ecr_repository.rules-update.repository_url}:${var.container_image_tag}"

  # Deploy as code
  handler = "index.handler"

  source_path = "${var.lambda_source_path}update_rules_processor"

  create_current_version_allowed_triggers = false # !var.use_container_image

  timeout     = 60
  memory_size = 512

  attach_policies    = true
  number_of_policies = 2
  policies = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  ]

  attach_policy_statements = true
  policy_statements = {
    s3_read = {
      effect = "Allow",
      actions = [
        "s3:HeadObject",
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      resources = ["${module.rules_bucket.s3_bucket_arn}/*"]
    },
    s3_put = {
      effect    = "Allow",
      actions   = ["s3:PutObject", "s3:PutObjectAcl"],
      resources = ["${module.rules_bucket.s3_bucket_arn}/*"]
    },
    kms_get_key = {
      effect = "Allow",
      actions = [
        "kms:Encrypt",
        "kms:DescribeKey",
        "kms:GenerateDataKey",
        "kms:Decrypt",
        "kms:ReEncryptTo"
      ],
      resources = [module.rules_bucket.kms_key_arn]
    },
    secrets_get = {
      effect = "Allow",
      actions = [
        "secretsmanager:GetResourcePolicy",
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecretVersionIds"
      ],
      resources = ["${var.postgress_master_password_secret_id}"]
    },
    log_lambda = {
      effect = "Allow",
      actions = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      resources = ["*"]
    }
  }

  allowed_triggers = {
    S3BucketUpload = {
      service    = "s3"
      principal  = "s3.amazonaws.com"
      source_arn = "${module.rules_bucket.s3_bucket_arn}"
    }
  }

  assume_role_policy_statements = {
    account_root = {
      effect  = "Allow",
      actions = ["sts:AssumeRole"],
      principals = {
        account_principal = {
          type        = "Service",
          identifiers = ["lambda.amazonaws.com"]
        }
      }
    }
  }

  vpc_security_group_ids = [var.default_security_group_id]

  vpc_subnet_ids = var.aws_subnets_private_ids

  environment_variables = {
    DATABASE_NAME          = "rules"
    DATABASE_USERNAME      = "root"
    DATABASE_HOSTNAME      = "${var.postgress_hostname}"
    DATABASE_PORT          = "5432"
    SECRET_PASSWORD_LOOKUP = "${var.postgress_master_password_secret_id}"
    REGION_NAME            = "${local.region}"

    # needed until we fix https://trello.com/c/lLABy4j9/791-certain-enrichment-lambda-functions-not-updating-on-merge-even-though-terraform-updating-env-variables-causing-errors
    TABLE_NAME = "rules"
    USERNAME   = "root"
    PORT       = "5432"
    HOSTNAME   = "${var.postgress_hostname}"
  }

  cloudwatch_logs_retention_in_days = 365

  tags = local.tags

}

module "lambda-validate-replacements" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.21.1"

  function_name = "${local.name}-${local.environment}-xml-validate"
  package_type  = var.use_container_image == true ? "Image" : "Zip"

  # Deploy as code
  handler = "index.handler"

  runtime     = "python3.12"
  source_path = "${var.lambda_source_path}xml_validate"

  create_current_version_allowed_triggers = false # !var.use_container_image

  timeout     = 30
  memory_size = var.memory_size

  attach_policy_statements = true
  policy_statements = {
    s3_read = {
      effect = "Allow",
      actions = [
        "s3:HeadObject",
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      resources = ["${module.xml_third_phase_enriched_bucket.s3_bucket_arn}/*", "${module.rules_bucket.s3_bucket_arn}/*",
      "${module.vcite_enriched_bucket.s3_bucket_arn}/*"]
    },
    kms_get_key = {
      effect = "Allow",
      actions = [
        "kms:Encrypt",
        "kms:DescribeKey",
        "kms:GenerateDataKey",
        "kms:Decrypt",
        "kms:ReEncryptTo"
      ],
      resources = [module.xml_third_phase_enriched_bucket.kms_key_arn, module.rules_bucket.kms_key_arn]
    },
    sqs_put_message = {
      effect = "Allow",
      actions = [
        "sqs:SendMessage",
        "sqs:GetQueueAttributes"
      ],
      "Effect" : "Allow",
      resources = [aws_sqs_queue.xml-validated-queue.arn]
    },
    sns_put = {
      effect = "Allow",
      actions = [
        "SNS:Publish",
        "SNS:ListSubscriptionsByTopic",
        "SNS:GetTopicAttributes"
      ],
      resources = ["${aws_sns_topic.validation_updates.arn}", "${aws_sns_topic.validation_updates_error.arn}"]
    },
    log_lambda = {
      effect = "Allow",
      actions = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      resources = ["*"]
    },
    ssm_get_parameter = {
      effec = "Allow",
      actions = [
        "ssm:GetParameters",
        "ssm:GetParameter",
        "ssm:GetParametersByPath"
      ],
      resources = ["${aws_ssm_parameter.vCite.arn}"]
    }
  }

  allowed_triggers = {
    ThirdPhaseUpload = {
      service    = "s3"
      principal  = "s3.amazonaws.com"
      source_arn = "${module.xml_third_phase_enriched_bucket.s3_bucket_arn}"
    },
    vCiteUpload = {
      service    = "s3"
      principal  = "s3.amazonaws.com"
      source_arn = "${module.vcite_enriched_bucket.s3_bucket_arn}"
    }
  }

  assume_role_policy_statements = {
    account_root = {
      effect  = "Allow",
      actions = ["sts:AssumeRole"],
      principals = {
        account_principal = {
          type        = "Service",
          identifiers = ["lambda.amazonaws.com"]
        }
      }
    }
  }

  environment_variables = {
    DEST_TOPIC_NAME       = "${aws_sns_topic.validation_updates.arn}"
    DEST_ERROR_TOPIC_NAME = "${aws_sns_topic.validation_updates_error.arn}"
    DEST_BUCKET_NAME      = "${module.xml_third_phase_enriched_bucket.s3_bucket_id}"
    VCITE_BUCKET          = "vcite-tna-files"
    VCITE_ENRICHED_BUCKET = "${module.vcite_enriched_bucket.s3_bucket_id}"
    SCHEMA_BUCKET_NAME    = "${module.rules_bucket.s3_bucket_id}"
    SCHEMA_BUCKET_KEY     = "caselaw.xsd"
    VALIDATE_USING_SCHEMA = "0"
    DEST_QUEUE            = aws_sqs_queue.xml-validated-queue.url
  }

  cloudwatch_logs_retention_in_days = 365

  tags = local.tags

}

resource "aws_s3_bucket_notification" "third_phase_enriched_bucket_notification" {
  bucket = module.xml_third_phase_enriched_bucket.s3_bucket_id

  lambda_function {
    lambda_function_arn = module.lambda-validate-replacements.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
  }
}

resource "aws_s3_bucket_notification" "vcite_enriched_bucket_notification" {
  bucket = module.vcite_enriched_bucket.s3_bucket_id

  lambda_function {
    lambda_function_arn = module.lambda-validate-replacements.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
  }
}

resource "aws_cloudwatch_event_rule" "update_legislation_table_lambda_event_rule" {
  name                = "update-legislation-table-lambda-event-rule"
  description         = "retry scheduled every 1 week"
  schedule_expression = "rate(7 days)"
}

resource "aws_cloudwatch_event_target" "update_legislation_table_lambda_target" {
  arn   = module.lambda-update-legislation-table.lambda_function_arn
  rule  = aws_cloudwatch_event_rule.update_legislation_table_lambda_event_rule.name
  input = "{\"trigger_date\": 7}"
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_rw_fallout_retry_step_deletion_lambda" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-update-legislation-table.lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.update_legislation_table_lambda_event_rule.arn
}


resource "aws_ecr_repository" "fetch-xml" {
  name = "${local.name}-ecr-repository-fetch-xml-${local.environment}"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.tags
}

resource "aws_ecr_repository" "db-backup" {
  name = "${local.name}-ecr-repository-db-backup-${local.environment}"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.tags
}

resource "aws_ecr_lifecycle_policy" "db_backup" {
  repository = aws_ecr_repository.db-backup.name
  policy     = file("${path.module}/retention_policy.json")
}

resource "aws_ecr_lifecycle_policy" "fx_retention" {
  repository = aws_ecr_repository.fetch-xml.name
  policy     = file("${path.module}/retention_policy.json")
}

resource "aws_secretsmanager_secret" "API_username" {
  description             = "Secret for storing the API username"
  name                    = "${local.name}-API-username-${local.environment}"
  recovery_window_in_days = 0

  tags = local.tags
}

resource "aws_secretsmanager_secret" "API_password" {
  description             = "Secret for storing the API password"
  name                    = "${local.name}-API-password-${local.environment}"
  recovery_window_in_days = 0

  tags = local.tags
}

data "aws_secretsmanager_secret" "API_username" {
  name = "${local.name}-API-username-${local.environment}"
}

data "aws_secretsmanager_secret_version" "API_username_credentials" {
  secret_id  = data.aws_secretsmanager_secret.API_username.id
  depends_on = [aws_secretsmanager_secret.API_username]
}

data "aws_secretsmanager_secret" "API_password" {
  name = "${local.name}-API-password-${local.environment}"
}

data "aws_secretsmanager_secret_version" "API_password_credentials" {
  secret_id  = data.aws_secretsmanager_secret.API_password.id
  depends_on = [aws_secretsmanager_secret.API_password]
}

module "lambda-fetch-xml" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "< 8.0.0"

  # Lambda function declaration
  function_name = "${local.name}-${local.environment}-fetch-xml"

  package_type   = "Image"
  create_package = false

  runtime = "python3.12" # Setting runtime is required when building package in Docker and Lambda Layer resource.

  image_uri = "${aws_ecr_repository.fetch-xml.repository_url}:${var.container_image_tag}"

  # Deploy as code
  handler = "index.handler"

  source_path = "${var.lambda_source_path}fetch_xml"

  create_current_version_allowed_triggers = false # !var.use_container_image

  timeout     = 60
  memory_size = 512

  attach_policies    = true
  number_of_policies = 2
  policies = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  ]

  attach_policy_statements = true
  policy_statements = {
    s3_read = {
      effect = "Allow",
      actions = [
        "s3:HeadObject",
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:List*",
      ],
      resources = ["*"]
    },
    s3_put = {
      effect    = "Allow",
      actions   = ["s3:PutObject", "s3:PutObjectAcl"],
      resources = ["${module.xml_original_bucket.s3_bucket_arn}/*"]
    },
    kms_get_key = {
      effect = "Allow",
      actions = [
        "kms:Encrypt",
        "kms:DescribeKey",
        "kms:GenerateDataKey",
        "kms:Decrypt",
        "kms:ReEncryptTo"
      ],
      resources = ["*"]
    },
    log_lambda = {
      effect = "Allow",
      actions = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      resources = ["*"]
    },
    sqs_get = {
      effect = "Allow",
      actions = [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      resources = ["${aws_sqs_queue.fetch_xml_queue.arn}"]
    },
    secrets_get = {
      effect = "Allow",
      actions = [
        "secretsmanager:GetResourcePolicy",
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecretVersionIds"
      ],
      resources = [
        aws_secretsmanager_secret.API_username.arn,
        aws_secretsmanager_secret.API_password.arn
      ]
    }
  }

  assume_role_policy_statements = {
    account_root = {
      effect  = "Allow",
      actions = ["sts:AssumeRole"],
      principals = {
        account_principal = {
          type        = "Service",
          identifiers = ["lambda.amazonaws.com"]
        }
      }
    }
  }

  vpc_security_group_ids = [var.default_security_group_id]

  vpc_subnet_ids = var.aws_subnets_private_ids

  environment_variables = {
    DEST_BUCKET_NAME = module.xml_original_bucket.s3_bucket_id
    API_USERNAME     = data.aws_secretsmanager_secret_version.API_username_credentials.secret_string
    API_PASSWORD     = data.aws_secretsmanager_secret_version.API_password_credentials.secret_string
    ENVIRONMENT      = "${local.environment}"
  }

  cloudwatch_logs_retention_in_days = 365

  tags = local.tags

}

resource "aws_ecr_repository" "push_enriched_xml" {
  name = "${local.name}-ecr-repository-push-enriched-xml-${local.environment}"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.tags
}

resource "aws_ecr_lifecycle_policy" "pe_retention" {
  repository = aws_ecr_repository.push_enriched_xml.name
  policy     = file("${path.module}/retention_policy.json")
}

module "lambda-push-enriched-xml" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.21.1"

  # Lambda function declaration
  function_name = "${local.name}-${local.environment}-push-enriched-xml"

  package_type   = "Image"
  create_package = false

  runtime = "python3.12" # Setting runtime is required when building package in Docker and Lambda Layer resource.

  image_uri = "${aws_ecr_repository.push_enriched_xml.repository_url}:${var.container_image_tag}"

  # Deploy as code
  handler = "index.handler"

  source_path = "${var.lambda_source_path}push_enriched_xml"

  create_current_version_allowed_triggers = false # !var.use_container_image

  timeout     = 60
  memory_size = 512

  attach_policies    = true
  number_of_policies = 2
  policies = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  ]

  attach_policy_statements = true
  policy_statements = {
    s3_read = {
      effect = "Allow",
      actions = [
        "s3:HeadObject",
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:List*",
      ],
      resources = ["*"]
    },
    kms_get_key = {
      effect = "Allow",
      actions = [
        "kms:Encrypt",
        "kms:DescribeKey",
        "kms:GenerateDataKey",
        "kms:Decrypt",
        "kms:ReEncryptTo"
      ],
      resources = ["*"]
    },
    log_lambda = {
      effect = "Allow",
      actions = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      resources = ["*"]
    },
    sqs_get = {
      effect = "Allow",
      actions = [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      resources = ["${aws_sqs_queue.xml-validated-queue.arn}"]
    },
    secrets_get = {
      effect = "Allow",
      actions = [
        "secretsmanager:GetResourcePolicy",
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecretVersionIds"
      ],
      resources = [
        aws_secretsmanager_secret.API_username.arn,
        aws_secretsmanager_secret.API_password.arn
      ]
    }
  }

  assume_role_policy_statements = {
    account_root = {
      effect  = "Allow",
      actions = ["sts:AssumeRole"],
      principals = {
        account_principal = {
          type        = "Service",
          identifiers = ["lambda.amazonaws.com"]
        }
      }
    }
  }

  allowed_triggers = {
    S3BucketUpload = {
      service    = "s3"
      principal  = "s3.amazonaws.com"
      source_arn = "${module.xml_third_phase_enriched_bucket.s3_bucket_arn}"
    }
  }

  vpc_security_group_ids = [var.default_security_group_id]
  vpc_subnet_ids         = var.aws_subnets_private_ids

  environment_variables = {
    SOURCE_BUCKET = "${module.xml_third_phase_enriched_bucket.s3_bucket_id}"
    API_USERNAME  = data.aws_secretsmanager_secret_version.API_username_credentials.secret_string
    API_PASSWORD  = data.aws_secretsmanager_secret_version.API_password_credentials.secret_string
    ENVIRONMENT   = "${local.environment}"
  }

  cloudwatch_logs_retention_in_days = 365

  tags = local.tags

}

module "db_backup_lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.21.1"

  function_name = "${local.name}-${local.environment}-db-backup"
  description   = "Takes a snapshot each day"

  create_package                          = false
  create_current_version_allowed_triggers = false

  maximum_retry_attempts = 0

  image_uri     = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${local.region}.amazonaws.com/tna-s3-tna-ecr-repository-db-backup-${local.environment}:latest"
  package_type  = "Image"
  architectures = ["x86_64"]
  timeout       = 900

  attach_policies    = true
  number_of_policies = 2
  policies = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  ]

  attach_policy_statements = true
  policy_statements = {
    rds = {
      effect = "Allow",
      actions = [
        "rds:Create*",
        "rds:StartExportTask",
        "rds:Describe*",
      ],
      resources = [
        "*"
      ]
    },
    kms_get_key = {
      effect = "Allow",
      actions = [
        "kms:Encrypt",
        "kms:DescribeKey",
        "kms:GenerateDataKey",
        "kms:Decrypt",
        "kms:ReEncryptTo"
      ],
      resources = ["*"]
    },
    iam = {
      effect = "Allow",
      actions = [
        "iam:PassRole",
      ]
      resources = [module.db_backup_lambda.lambda_role_arn]
    }
  }

  environment_variables = {
    environment = local.environment
  }

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

resource "aws_ssm_parameter" "vCite" {
  name  = "vCite"
  type  = "String"
  value = "off"
}
