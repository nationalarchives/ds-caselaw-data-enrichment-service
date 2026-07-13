FROM public.ecr.aws/lambda/python:3.13@sha256:b996fcbe71c33614349bd31cf2932347c7df4ec82a546be8f05071bca1b152a0

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONIOENCODING=UTF-8

# Install poetry
RUN pip install poetry

# Copy root pyproject.toml and poetry.lock for dependency resolution
COPY pyproject.toml poetry.lock ${LAMBDA_TASK_ROOT}/

# Install dependencies with rules-lambda group
RUN cd ${LAMBDA_TASK_ROOT} && poetry config virtualenvs.create false && poetry install --with rules-lambda --no-root

# Copy shared utilities and database modules (needed by all lambdas)
COPY src/utils ${LAMBDA_TASK_ROOT}/utils
COPY src/database ${LAMBDA_TASK_ROOT}/database

# Copy this lambda's code
COPY src/lambdas/update_rules_processor ${LAMBDA_TASK_ROOT}/lambdas/update_rules_processor

CMD ["lambdas.update_rules_processor.index.lambda_handler"]
