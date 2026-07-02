FROM public.ecr.aws/lambda/python:3.13@sha256:e38b89f323239f0c6156dad47f178b1c0873a6595180546874597c6707dd7520

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONIOENCODING=UTF-8

# Install poetry
RUN pip install poetry

# Copy root pyproject.toml and poetry.lock for dependency resolution
COPY pyproject.toml poetry.lock ${LAMBDA_TASK_ROOT}/

# Install dependencies with enrichment-lambda group
RUN cd ${LAMBDA_TASK_ROOT} && poetry config virtualenvs.create false && poetry install --with enrichment-lambda --no-root

# Copy shared utilities and database modules (needed by all lambdas)
COPY src/utils ${LAMBDA_TASK_ROOT}/utils
COPY src/database ${LAMBDA_TASK_ROOT}/database

# Copy enrichment modules (specific to this lambda)
COPY src/enrichment ${LAMBDA_TASK_ROOT}/enrichment

# Copy this lambda's code
COPY src/lambdas/enrichment_lambda ${LAMBDA_TASK_ROOT}/lambdas/enrichment_lambda

CMD ["lambdas.enrichment_lambda.index.handler"]
