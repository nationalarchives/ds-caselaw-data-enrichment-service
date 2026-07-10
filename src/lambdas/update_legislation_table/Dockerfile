FROM public.ecr.aws/lambda/python:3.13@sha256:42c04c55e2d14aa57906ee6962d3aef902ee5c264adab29b6f453041474ae862

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
