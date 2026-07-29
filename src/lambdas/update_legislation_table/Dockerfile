FROM public.ecr.aws/lambda/python:3.13@sha256:a2599a8364d1b56a6b39fcf83116fb33a69c5a0dfabdcbff618c9fe50bc00eab

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONIOENCODING=UTF-8

# Install poetry
RUN pip install poetry

# Copy root pyproject.toml and poetry.lock for dependency resolution
COPY pyproject.toml poetry.lock ${LAMBDA_TASK_ROOT}/

# Install dependencies with legislation-lambda group
RUN cd ${LAMBDA_TASK_ROOT} && poetry config virtualenvs.create false && poetry install --with legislation-lambda --no-root

# Copy shared utilities and database modules (needed by all lambdas)
COPY src/utils ${LAMBDA_TASK_ROOT}/utils
COPY src/database ${LAMBDA_TASK_ROOT}/database

# Copy this lambda's code
COPY src/lambdas/update_legislation_table ${LAMBDA_TASK_ROOT}/lambdas/update_legislation_table

CMD ["lambdas.update_legislation_table.index.handler"]
