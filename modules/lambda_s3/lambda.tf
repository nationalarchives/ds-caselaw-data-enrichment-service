

module "lambda-extract-judgement-contents" {
  source  = "terraform-aws-modules/lambda/aws"
  version = ">=2.0.0,<3.0.0"
  # version = "2.35.1"

  # version = ">=4.4.0"

  function_name = "${local.name}-${local.environment}-extract-judgement-contents"
  package_type  = var.use_container_image == true ? "Image" : "Zip"
  # package_type = "Image"

  # Deploy as code
  # handler     = var.lambda_handler
  handler = "index.handler"
  # runtime     = var.runtime
  runtime           = "python3.6" 
  source_path = "${var.lambda_source_path}extract_judgement_contents"

  # Deploy as ECR image
  # image_uri      = var.use_container_image == true ? "${aws_ecr_repository.main[0].repository_url}:${var.container_image_tag}" : null
  # create_package = !var.use_container_image

  create_current_version_allowed_triggers = false # !var.use_container_image

  timeout     = 30
  memory_size = 256
  # memory_size = var.memory_size

  attach_policy_statements = true
  policy_statements = {
    s3_read = {
      effect = "Allow",
      actions = [
        "s3:HeadObject",
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      # resources = ["${data.aws_s3_bucket.source_bucket.arn}/${var.source_bucket_folder}*"]
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
      # resources = [module.dest_bucket.kms_key_arn]
      resources = [module.text_content_bucket.kms_key_arn, module.xml_original_bucket.kms_key_arn]
    },
    # sqs_get_message = {
    #   effect = "Allow",
    #   actions = [
    #     "sqs:ReceiveMessage",
    #     "sqs:DeleteMessage",
    #     "sqs:GetQueueAttributes"
    #   ],
    #   "Effect": "Allow",
    #   resources = [module.xml_original_bucket_sqs_queue.queue.arn]
    # },
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
# }

  allowed_triggers = {
    S3BucketUpload = {
      service    = "s3"
      principal  = "s3.amazonaws.com"
      # source_arn = module.xml_original_bucket.s3_bucket.arn
      source_arn = "${module.xml_original_bucket.s3_bucket_arn}"
    }
  }

  environment_variables = {
    DEST_BUCKET_NAME       = "${module.text_content_bucket.s3_bucket_id}"
    # DATA_BUCKET_KMS_KEY_ID = module.text_content_bucket.kms_key_id
  }

  tags = local.tags
}

resource "aws_s3_bucket_notification" "xml_original_bucket_notification" {
  # bucket = module.xml_original_bucket.bucket_name.id
  # bucket = module.xml_original_bucket.bucket.id
  # bucket = "${module.xml_original_bucket.name}"
  # bucket = "${module.xml_original_bucket.s3_bucket_arn}"
  # bucket =module.xml_original_bucket.s3_bucket.arn
  bucket =module.xml_original_bucket.s3_bucket_id

  lambda_function {
    lambda_function_arn = module.lambda-extract-judgement-contents.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
    # filter_prefix       = var.source_bucket_folder
    # filter_suffix       = var.source_filter_suffix
  }
}
#   depends_on = [
#     module.xml_original_bucket
#   ]
# }

# CloudWatch Log Group for the Lambda function
# resource "aws_cloudwatch_log_group" "lambda_loggroup" {
#     name = "/aws/lambda/${lambda-extract-judgement-contents.function_name}"
#     retention_in_days = 14
# }

# resource "aws_lambda_layer_version" "lambda_layer" {
#   filename   = "python.zip"
#   layer_name = "${local.name}-lambda-layer-${local.environment}"

#   compatible_runtimes = ["python3.6"]
# }

# module "lambda_function" {
#   source = "terraform-aws-modules/lambda/aws"

#   function_name  = "my-lambda1"
#   create_package = false

#   image_uri    = module.docker_image.image_uri
#   package_type = "Image"
# }

# module "docker_image" {
#   source = "terraform-aws-modules/lambda/aws//modules/docker-build"

#   create_ecr_repo = true
#   ecr_repo        = "${local.name}-${local.environment}my-test-ecr-repo"
#   image_tag       = "1.0"
#   source_path     = "${var.lambda_source_path}determine_replacements_caselaw"
#   build_args      = {
#     FOO = "bar"
#   }
# }

resource "aws_ecr_repository" "main" {
  # count = var.use_container_image == true ? 1 : 0

  name                 = "${local.name}-ecr-repository-${local.environment}"
  # image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.tags
}

resource "aws_ecr_repository" "legislation" {
  # count = var.use_container_image == true ? 1 : 0

  name                 = "${local.name}-ecr-repository-legislation-${local.environment}"
  # image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.tags
}

resource "aws_ecr_repository" "abbreviations" {
  # count = var.use_container_image == true ? 1 : 0

  name                 = "${local.name}-ecr-repository-abbreviations-${local.environment}"
  # image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.tags
}


# resource "aws_ecr_lifecycle_policy" "main" {
#   count = var.use_container_image == true ? 1 : 0

#   repository = aws_ecr_repository.main.name

#   policy = jsonencode({
#     rules = [{
#       rulePriority = 1
#       description  = "keep last 3 images"
#       action = {
#         type = "expire"
#       }
#       selection = {
#         tagStatus   = "any"
#         countType   = "imageCountMoreThan"
#         countNumber = 3
#       }
#     }]
#   })
# }

# module "docker_image" {
#   source = "terraform-aws-modules/lambda/aws//modules/docker-build"

#   # create_ecr_repo = false
#   create_ecr_repo = true
#   ecr_repo        = aws_ecr_repository.main.name
#   image_tag       = var.container_image_tag
#   # source_path     = abspath(var.lambda_source_path)
#   source_path     = abspath("${var.lambda_source_path}determine_replacements_caselaw")
#   docker_file_path = "Dockerfile"
# }

resource "random_pet" "this" {
  length = 2
}

# module "lambda_function_from_container_image" {
#   source = "terraform-aws-modules/lambda/aws"

#   function_name = "${random_pet.this.id}-lambda-from-container-image"
#   description   = "My awesome lambda function from container image"

#   create_package = false

#   ##################
#   # Container Image
#   ##################
#   image_uri    = module.docker_image.image_uri
#   package_type = "Image"
# }

# module "docker_image" {
#   source = "terraform-aws-modules/lambda/aws//modules/docker-build"

#   create_ecr_repo = true
#   ecr_repo        = random_pet.this.id
#   image_tag       = "1.0"
#   source_path     = abspath("${var.lambda_source_path}determine_replacements_caselaw")
#   build_args = {
#     FOO = "bar"
#   }
#   ecr_repo_lifecycle_policy = <<EOF
# {
#   "rules": [
#     {
#       "rulePriority": 1,
#       "description": "Keep only the last 2 images",
#       "selection": {
#         "tagStatus": "any",
#         "countType": "imageCountMoreThan",
#         "countNumber": 2
#       },
#       "action": {
#         "type": "expire"
#       }
#     }
#   ]
# }
# EOF
# }

# module "docker_image" {
#   source = "terraform-aws-modules/lambda/aws//modules/docker-build"

#   create_ecr_repo = false
#   ecr_repo        = aws_ecr_repository.main.name
#   image_tag       = var.container_image_tag
#   source_path     = abspath("${var.lambda_source_path}determine_replacements_caselaw")
#   docker_file_path = "Dockerfile"
# }

# provider "docker" {}

# resource "aws_lambda_function" "lambda" {
#   # image_uri     = var.image_uri
#   image_uri     = "${aws_ecr_repository.main.repository_url}:${var.container_image_tag}"
#   function_name = "test_function_name"
#   # role          = var.role_arn
#   role = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
#   # description   = var.description
#   # memory_size   = var.memory_size
#   # timeout       = var.timeout
#   package_type  = "Image"

  # lifecycle {
  #   ignore_changes = [image_uri, layers]
  # }

  # attach_policies    = true
  # number_of_policies = 2
  # policies = [
  #   "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
  #   "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  # ]

  # assume_role_policy_statements = {
  #   account_root = {
  #     effect  = "Allow",
  #     actions = ["sts:AssumeRole"],
  #     principals = {
  #       account_principal = {
  #         type        = "Service",
  #         identifiers = ["lambda.amazonaws.com"]
  #       }
  #     }
  #   }
  # }

  # depends_on = [
  #   null_resource.ecr_image
  # ]

#   tags = local.tags
# }

# resource "null_resource" "ecr_image" {
#   provisioner "local-exec" {
#     command = <<EOF
#         aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${split("/", aws_ecr_repository.main.repository_url)[0]}:${var.container_image_tag}
#         docker pull hello-world
#         docker tag hello-world:latest ${aws_ecr_repository.main.repository_url}:${var.container_image_tag}
#         docker push ${aws_ecr_repository.main.repository_url}:${var.container_image_tag}
#     EOF
#   }
# }

module "lambda-determine-replacements-caselaw" {
  source  = "terraform-aws-modules/lambda/aws"
  version = ">=2.0.0,<3.0.0"

  function_name = "${local.name}-${local.environment}-determine-replacements-caselaw"
  # package_type  = var.use_container_image == true ? "Image" : "Zip"
  package_type  = "Image"
  create_package = false

  # Deploy as code
  # layers = [
  #   aws_lambda_layer_version.lambda_layer.arn
  # ]
  # handler     = var.lambda_handler
  handler = "index.handler"
  # runtime     = var.runtime
  # runtime           = "python3.6" 
  # source_path = "${var.lambda_source_path}determine_replacements_caselaw"
  image_uri     = "${aws_ecr_repository.main.repository_url}:${var.container_image_tag}"

  # Deploy as ECR image
  # image_uri      = var.use_container_image == true ? "${aws_ecr_repository.main[0].repository_url}:${var.container_image_tag}" : null
  # image_uri      = var.use_container_image == true ? module.docker_image.image_uri : null
  # create_package = !var.use_container_image

  # create_layer        = true
  # layer_name          = "${local.name}-${local.environment}-determine_replacements_caselaw_layer"

  # store_on_s3 = true
  # s3_bucket = module.container_bucket.s3_bucket_arn
  # build_in_docker = true

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
      resources = ["${module.text_content_bucket.s3_bucket_arn}/*","${module.rules_bucket.s3_bucket_arn}/*"]
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
    # sqs_get_message = {
    #   effect = "Allow",
    #   actions = [
    #     "sqs:ReceiveMessage",
    #     "sqs:DeleteMessage",
    #     "sqs:GetQueueAttributes"
    #   ],
    #   "Effect": "Allow",
    #   resources = [aws_sqs_queue.text_content_bucket_sqs_queue.queue.arn]
    # },
    secrets_get = {
      effect = "Allow",
      actions = [
        "secretsmanager:GetResourcePolicy",
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecretVersionIds"
      ],  
      # resources = ["${module.data.aws_secretsmanager_secret.postgress_master_password.arn}"] 
      # module.data.aws_secretsmanager_secret.postgress_master_password
      resources = ["${var.postgress_master_password_secret_id}"] 
    },
    sqs_put_message = {
      effect = "Allow",
      actions = [
        "sqs:SendMessage",
        "sqs:GetQueueAttributes"
      ],
      "Effect": "Allow",
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
# }

  allowed_triggers = {
    S3BucketUpload = {
      service    = "s3"
      principal  = "s3.amazonaws.com"
      # source_arn = module.xml_original_bucket.s3_bucket.arn
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

  # environment_variables = {
  #   DEST_QUEUE_NAME       = aws_sqs_queue.replacements_queue.url
  #   # DATA_QUEUE_KMS_KEY_ID = module.xml_enriched_bucket.kms_key_id
  # }

  vpc_security_group_ids = [var.default_security_group_id]
  vpc_subnet_ids = var.aws_subnets_private_ids

  environment_variables = {
    # DB_SECRETS_ARN = "${resource.aws_secretsmanager_secret.postgress_master_password.arn}"
    DATABASE_NAME = "rules"
    # TABLE_NAME = "manifest"
    TABLE_NAME = "rules"
    USERNAME = "root"
    PORT = "5432"
    SECRET_PASSWORD_LOOKUP = "${var.postgress_master_password_secret_id}"
    REGION_NAME = "${local.region}"
    HOSTNAME = "${var.postgress_hostname}"

    DEST_QUEUE_NAME     = aws_sqs_queue.replacement-caselaw-queue.url
    RULES_FILE_BUCKET =  "${module.rules_bucket.s3_bucket_id}"
    RULES_FILE_KEY = "citation_patterns.jsonl"
    REPLACEMENTS_BUCKET = "${module.replacements_bucket.s3_bucket_id}"

  }

  tags = local.tags
}

module "lambda-determine-replacements-legislation" {
  source  = "terraform-aws-modules/lambda/aws"
  version = ">=2.0.0,<3.0.0"

  function_name = "${local.name}-${local.environment}-determine-replacements-legislation"
  # package_type  = var.use_container_image == true ? "Image" : "Zip"
  package_type  = "Image"
  create_package = false

  handler = "index.handler"
  image_uri     = "${aws_ecr_repository.legislation.repository_url}:${var.container_image_tag}"

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
      resources = ["${module.text_content_bucket.s3_bucket_arn}/*","${module.replacements_bucket.s3_bucket_arn}/*"]
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
      "Effect": "Allow",
      resources = [aws_sqs_queue.replacement-caselaw-queue.arn]
    },
    sqs_put_message = {
      effect = "Allow",
      actions = [
        "sqs:SendMessage",
        "sqs:GetQueueAttributes"
      ],
      "Effect": "Allow",
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
      # resources = ["${module.data.aws_secretsmanager_secret.postgress_master_password.arn}"] 
      # module.data.aws_secretsmanager_secret.postgress_master_password
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
  vpc_subnet_ids = var.aws_subnets_private_ids

  environment_variables = {
    DATABASE_NAME = "rules"
    # TABLE_NAME = "manifest"
    TABLE_NAME = "rules"
    USERNAME = "root"
    PORT = "5432"
    SECRET_PASSWORD_LOOKUP = "${var.postgress_master_password_secret_id}"
    REGION_NAME = "${local.region}"
    HOSTNAME = "${var.postgress_hostname}"

    # DEST_QUEUE_NAME     = aws_sqs_queue.replacement-abbreviations-queue.url
    DEST_QUEUE_NAME     = aws_sqs_queue.replacement-legislation-queue.url
    
    REPLACEMENTS_BUCKET = "${module.replacements_bucket.s3_bucket_id}"
    SOURCE_BUCKET = "${module.text_content_bucket.s3_bucket_arn}"
  }

  tags = local.tags
}


module "lambda-determine-replacements-abbreviations" {
  source  = "terraform-aws-modules/lambda/aws"
  version = ">=2.0.0,<3.0.0"

  function_name = "${local.name}-${local.environment}-determine-replacements-abbreviations"
  # package_type  = var.use_container_image == true ? "Image" : "Zip"
  package_type  = "Image"
  create_package = false

  # package_type  = var.use_container_image == true ? "Image" : "Zip"
  # package_type = "Image"

  # Deploy as code
  # handler     = var.lambda_handler
  handler = "index.handler"
  # runtime     = var.runtime
  # runtime           = "python3.9" 
  # source_path = "${var.lambda_source_path}determine_replacements_abbreviations"
  image_uri     = "${aws_ecr_repository.abbreviations.repository_url}:${var.container_image_tag}"

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
      resources = ["${module.text_content_bucket.s3_bucket_arn}/*","${module.replacements_bucket.s3_bucket_arn}/*"]
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
      "Effect": "Allow",
      resources = [aws_sqs_queue.replacement-legislation-queue.arn]
    },

    sqs_put_message = {
      effect = "Allow",
      actions = [
        "sqs:SendMessage",
        "sqs:GetQueueAttributes"
      ],
      "Effect": "Allow",
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
  vpc_subnet_ids = var.aws_subnets_private_ids

  environment_variables = {
 
    DEST_QUEUE_NAME     = aws_sqs_queue.replacement-abbreviations-queue.url
    # DEST_QUEUE_NAME     = aws_sqs_queue.replacement-legislation-queue.url
    # DEST_QUEUE_NAME     = aws_sqs_queue.replacement-abbreviations-queue.arn
    REPLACEMENTS_BUCKET = "${module.replacements_bucket.s3_bucket_id}"
    SOURCE_BUCKET = "${module.text_content_bucket.s3_bucket_arn}"
  }

  tags = local.tags
}


module "lambda-make-replacements" {
  source  = "terraform-aws-modules/lambda/aws"
  version = ">=2.0.0,<3.0.0"

  function_name = "${local.name}-${local.environment}-make-replacements"
  package_type  = var.use_container_image == true ? "Image" : "Zip"

  # Deploy as code
  # handler     = var.lambda_handler
  handler = "index.handler"
  # runtime     = var.runtime
  runtime           = "python3.6" 
  source_path = "${var.lambda_source_path}make_replacements"

  # Deploy as ECR image
  # image_uri      = var.use_container_image == true ? "${aws_ecr_repository.main[0].repository_url}:${var.container_image_tag}" : null
  # create_package = !var.use_container_image

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
      resources = ["${module.xml_original_bucket.s3_bucket_arn}/*","${module.replacements_bucket.s3_bucket_arn}/*"]
      # resources = [module.xml_original_bucket.s3_bucket_id]
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
      resources = ["${aws_sqs_queue.replacements-queue.arn}","${aws_sqs_queue.replacement-caselaw-queue.arn}","${aws_sqs_queue.replacement-legislation-queue.arn}","${aws_sqs_queue.replacement-abbreviations-queue.arn}"]
      # resources = ["${aws_sqs_queue_terraform_queue_arn}"]
      # resources = [module.aws_sqs_queue.terraform_queue.arn]
    },
    # secrets_get = {
    #   effect = "Allow",
    #   actions = [
    #     "secretsmanager:GetResourcePolicy",
    #     "secretsmanager:GetSecretValue",
    #     "secretsmanager:DescribeSecret",
    #     "secretsmanager:ListSecretVersionIds"
    #   ],  
    #   # resources = ["${module.data.aws_secretsmanager_secret.postgress_master_password.arn}"] 
    #   # module.data.aws_secretsmanager_secret.postgress_master_password
    #   resources = ["${var.postgress_master_password_secret_id}"] 
    # },
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

  # event = {
  #   type             = "sqs"
  #   event_source_arn = "arn:aws:kinesis:eu-west-1:647379381847:queue-name"
  # }

  # # optionally configure Parameter Store access with decryption
  # ssm_parameter_names = ["some/config/root/*"]
  # kms_key_arn         = "arn:aws:kms:eu-west-1:647379381847:key/f79f2b-04684-4ad9-f9de8a-79d72f"

  environment_variables = {
    DEST_BUCKET_NAME       = "${module.xml_enriched_bucket.s3_bucket_id}"
    REPLACEMENTS_BUCKET    = "${module.replacements_bucket.s3_bucket_id}"
    # DATA_BUCKET_KMS_KEY_ID = module.xml_enriched_bucket.kms_key_id
    SOURCE_BUCKET_NAME       = "${module.xml_original_bucket.s3_bucket_id}"
    # SOURCE_BUCKET_KMS_KEY_ID = module.xml_original_bucket.kms_key_id
  }

  tags = local.tags

}

resource "aws_s3_bucket_notification" "text_content_bucket_notification" {
  # bucket = module.xml_original_bucket.bucket_name.id
  # bucket = module.xml_original_bucket.bucket.id
  # bucket = "${module.xml_original_bucket.name}"
  # bucket = "${module.xml_original_bucket.s3_bucket_arn}"
  # bucket =module.xml_original_bucket.s3_bucket.arn
  bucket =module.text_content_bucket.s3_bucket_id

  lambda_function {
    lambda_function_arn = module.lambda-determine-replacements-caselaw.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
    # filter_prefix       = var.source_bucket_folder
    # filter_suffix       = var.source_filter_suffix
  }
}


resource "aws_s3_bucket_notification" "xml_enriched_bucket_notification" {
  # bucket = module.xml_original_bucket.bucket_name.id
  # bucket = module.xml_original_bucket.bucket.id
  # bucket = "${module.xml_original_bucket.name}"
  # bucket = "${module.xml_original_bucket.s3_bucket_arn}"
  # bucket =module.xml_original_bucket.s3_bucket.arn
  bucket = module.xml_enriched_bucket.s3_bucket_id

  lambda_function {
    lambda_function_arn = module.lambda-validate-replacements.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
    # filter_prefix       = var.source_bucket_folder
    # filter_suffix       = var.source_filter_suffix
  }
}

# resource "aws_lambda_layer_version" "lambda_layer" {
#   # filename   = var.layer_zip_filename
#   # filename   = "lambda_layer.zip"
#   filename   = "python.zip"
#   layer_name = "${local.name}-lambda-layer-${terraform.workspace}"

#   compatible_runtimes = ["python3.8"]
# }

# data "aws_iam_policy_document" "AWSLambdaTrustPolicy" {
#   statement {
#     actions    = ["sts:AssumeRole"]
#     effect     = "Allow"
#     principals {
#       type        = "Service"
#       identifiers = ["lambda.amazonaws.com"]
#     }
#   }
# }

# resource "aws_iam_role" "terraform_function_role" {
#   name               = "terraform_function_role"
#   assume_role_policy = "${data.aws_iam_policy_document.AWSLambdaTrustPolicy.json}"
# }

# resource "aws_iam_role_policy_attachment" "terraform_lambda_policy" {
#   role       = "${aws_iam_role.terraform_function_role.name}"
#   policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
# }

# resource "aws_iam_role" "lambda_exec_role" {
#   name = "lambda_exec_role"
#   assume_role_policy = <<EOF
# {
#   "Version": "2012-10-17",
#   "Statement": [
#     {
#       "Action": "sts:AssumeRole",
#       "Principal": {
#         "Service": "lambda.amazonaws.com"
#       },
#       "Effect": "Allow",
#       "Sid": ""
#     }
#   ]
# }
# EOF
# }
 
# data "aws_iam_policy" "LambdaVPCAccess" {
#   arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
# }
 
# resource "aws_iam_role_policy_attachment" "sto-lambda-vpc-role-policy-attach" {
#   role       = "${aws_iam_role.lambda_exec_role.name}"
#   policy_arn = "${data.aws_iam_policy.LambdaVPCAccess.arn}"
# }

module "lambda-read-rules" {
  source  = "terraform-aws-modules/lambda/aws"
  version = ">=2.0.0,<3.0.0"

# Lambda function declaration
# resource "aws_lambda_function" "lambda-read-rules" {
  function_name = "${local.name}-${local.environment}-read-rules"
  package_type  = var.use_container_image == true ? "Image" : "Zip"

  # build_in_docker   = true

# source_path = "${var.lambda_source_path}make_replacements"

  # docker_file       = "${var.lambda_source_path}make_replacements/Dockerfile"
  # docker_build_root = "${var.lambda_source_path}make_replacements"
  # docker_image      = "lambci/lambda:build-python3.8"
  # runtime           = "python3.8"    # Setting runtime is required when building package in Docker and Lambda Layer resource.
  runtime           = "python3.6" 

  # layers = [aws_lambda_layer_version.lambda_layer.arn]

  # Deploy as code
  # handler     = var.lambda_handler
  handler = "index.handler"
  # runtime     = var.runtime
  source_path = "${var.lambda_source_path}read_rules"

  create_current_version_allowed_triggers = false # !var.use_container_image

  timeout     = 60
  memory_size = var.memory_size

  # vpc_config {
  #   subnet_ids = ["${split(",", var.subnet_ids)}"]
  #   security_group_ids = ["${var.security_group_ids}"]
  # }

  # role = "${aws_iam_role.terraform_function_role.arn}"
  # role = "${aws_iam_role.lambda_exec_role.arn}"

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
      # resources = ["${module.data.aws_secretsmanager_secret.postgress_master_password.arn}"] 
      # module.data.aws_secretsmanager_secret.postgress_master_password
      resources = ["${var.postgress_master_password_secret_id}"] 
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

  # # so the lambda can access the database
  # vpc_config {
  #   # subnet_ids         = [aws_default_subnet.csx_default_az1.id, aws_default_subnet.csx_default_az2.id, aws_default_subnet.csx_default_az3.id]
  #   # security_group_ids = [aws_default_vpc.csx_default.default_security_group_id]

  #   for_each = toset(module.vpc.public_subnets)
  #   # subnet_ids = "${element(var.subnet_azs, count.index)}"
  #   subnet_ids =each.key
  #   security_group_ids = [module.vpc.default_security_group_id]

  #   # subnet_ids         = ["subnet-0294f174fda94e874", "subnet-0a75c1dc97fe38ac2"]
  #   # security_group_ids = ["sg-0216fc2f7477ed58d"]
  # }

  # for_each = toset(module.vpc.public_subnets)
  # vpc_subnet_ids = each.key
  # vpc_subnet_ids = "${element(tolist(module.vpc.public_subnets.ids))}"
  # vpc_security_group_ids = [module.vpc.default_security_group_id]

  # count = "${length(var.public_subnets)}"
# ￼  id = "${element(public_subnets, count.index)}"

  vpc_security_group_ids = [var.default_security_group_id]
  # vpc_subnet_ids = "${element(var.public_subnets, count.index)}"
  # vpc_subnet_ids = "${var.public_subnets}"
  # for_each = toset(var.aws_subnets_private_ids)
  # id       = each.value
  # vpc_subnet_ids = [each.value]
  vpc_subnet_ids = var.aws_subnets_private_ids

  environment_variables = {
    # DB_SECRETS_ARN = "${resource.aws_secretsmanager_secret.postgress_master_password.arn}"
    DATABASE_NAME = "rules"
    # TABLE_NAME = "manifest"
    TABLE_NAME = "rules"
    USERNAME = "root"
    PORT = "5432"
    SECRET_PASSWORD_LOOKUP = "${var.postgress_master_password_secret_id}"
    REGION_NAME = "${local.region}"
    HOSTNAME = "${var.postgress_hostname}"
  }
  
  tags = local.tags

}

module "lambda-validate-replacements" {
  source  = "terraform-aws-modules/lambda/aws"
  version = ">=2.0.0,<3.0.0"

  function_name = "${local.name}-${local.environment}-xml-validate"
  package_type  = var.use_container_image == true ? "Image" : "Zip"

  # Deploy as code
  handler = "index.handler"
  # runtime     = var.runtime
  runtime           = "python3.6"
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
      resources = ["${module.xml_enriched_bucket.s3_bucket_arn}/*", "${module.rules_bucket.s3_bucket_arn}/*"]
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
      resources = [module.xml_enriched_bucket.kms_key_arn, module.rules_bucket.kms_key_arn]
    },
    sqs_get = {
      effect = "Allow",
      actions = [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      # resources = ["${aws_sqs_queue.replacements_made_queue.arn}"]
      resources = ["${aws_sqs_queue.replacements-queue.arn}"]
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
      # source_arn = module.xml_original_bucket.s3_bucket.arn
      source_arn = "${module.xml_enriched_bucket.s3_bucket_arn}"
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
    # DEST_QUEUE_NAME       = "${aws_sqs_queue.validation-queue.arn}"
    DEST_TOPIC_NAME       = "${aws_sns_topic.validation_updates.arn}"
    DEST_TOPIC_ERROR_NAME       = "${aws_sns_topic.validation_updates_error.arn}"
    DEST_BUCKET_NAME = module.xml_enriched_bucket.s3_bucket_arn
    # use the existing rules bucket for simplicty
    SCHEMA_BUCKET = "${module.rules_bucket.s3_bucket_arn}"
    SCHEMA_BUCKET_KEY = "judgment-1-1.xsd"
    VALIDATE_USING_DTD = "True"
    VALIDATE_USING_SCHEMA = "True"

  }

  tags = local.tags

}















# # Event source from SQS
# resource "aws_lambda_event_source_mapping" "sqs_replacements_event_source_mapping" {
#   event_source_arn = aws_sqs_queue.replacements_queue.arn
#   enabled          = true
# #   function_name    = aws_lambda_function.lambda-make-replacements.arn
#   function_name    = module.lambda-make-replacements.arn
# #   function_name    = "arn:aws:lambda:eu-west-1:849689169827:function:tna-s3-development-ucl-make-replacements"
# #   function_name    = "${module.lambda-make-replacements.arn}"
#   batch_size       = 1
# }

# module "lambda" {
#   source  = "terraform-aws-modules/lambda/aws"
#   # version = ">=2.0.0,<3.0.0"
#   version = ">=2.0.0,<4.4.0"

#   function_name = "${local.name}-${local.environment}"
#   package_type  = var.use_container_image == true ? "Image" : "Zip"

#   # Deploy as code
#   handler     = var.lambda_handler
#   runtime     = var.runtime
#   source_path = var.lambda_source_path

#   # Deploy as ECR image
#   image_uri      = var.use_container_image == true ? "${aws_ecr_repository.main[0].repository_url}:${var.container_image_tag}" : null
#   create_package = !var.use_container_image

#   create_current_version_allowed_triggers = false # !var.use_container_image

#   timeout     = 30
#   memory_size = var.memory_size

#   attach_policy_statements = true
#   policy_statements = {
#     s3_read = {
#       effect = "Allow",
#       actions = [
#         "s3:HeadObject",
#         "s3:GetObject",
#         "s3:GetObjectVersion"
#       ],
#       resources = ["${data.aws_s3_bucket.source_bucket.arn}/${var.source_bucket_folder}*"]
#     },
#     s3_put = {
#       effect    = "Allow",
#       actions   = ["s3:PutObject", "s3:PutObjectAcl"],
#       resources = ["${module.dest_bucket.s3_bucket_arn}/*"]
#     },
#     kms_get_key = {
#       effect = "Allow",
#       actions = [
#         "kms:Encrypt",
#         "kms:DescribeKey",
#         "kms:GenerateDataKey",
#         "kms:Decrypt",
#         "kms:ReEncryptTo"
#       ],
#       resources = [module.dest_bucket.kms_key_arn]
#     }
  # }


#   allowed_triggers = {
#     S3BucketUpload = {
#       service    = "s3"
#       principal  = "s3.amazonaws.com"
#       source_arn = data.aws_s3_bucket.source_bucket.arn
#     }
#   }

#   environment_variables = {
#     DEST_BUCKET_NAME       = module.dest_bucket.s3_bucket_id
#     DATA_BUCKET_KMS_KEY_ID = module.dest_bucket.kms_key_id
#   }

#   tags = local.tags
# }

# resource "aws_s3_bucket_notification" "bucket_notification" {
#   bucket = data.aws_s3_bucket.source_bucket.id

#   lambda_function {
#     lambda_function_arn = module.lambda.lambda_function_arn
#     events              = ["s3:ObjectCreated:*"]
#     filter_prefix       = var.source_bucket_folder
#     filter_suffix       = var.source_filter_suffix
#   }
# }


# resource "aws_lambda_permission" "allow_bucket1" {
#   statement_id  = "AllowExecutionFromS3Bucket1"
#   action        = "lambda:InvokeFunction"
#   function_name = aws_lambda_function.func1.arn
#   principal     = "s3.amazonaws.com"
#   source_arn    = aws_s3_bucket.bucket.arn
# }

# resource "aws_lambda_function" "func1" {
#   filename      = "your-function1.zip"
#   function_name = "example_lambda_name1"
#   role          = aws_iam_role.iam_for_lambda.arn
#   handler       = "exports.example"
#   runtime       = "go1.x"
# }