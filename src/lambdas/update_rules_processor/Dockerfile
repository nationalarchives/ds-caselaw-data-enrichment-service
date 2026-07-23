FROM public.ecr.aws/lambda/python:3.13@sha256:743866014de75339bd3d1e34ec69d9d93fa0942f584f401e560668daa8ba592e

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
