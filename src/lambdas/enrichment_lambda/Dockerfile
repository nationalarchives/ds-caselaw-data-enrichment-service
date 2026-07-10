FROM public.ecr.aws/lambda/python:3.13@sha256:42c04c55e2d14aa57906ee6962d3aef902ee5c264adab29b6f453041474ae862

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
