FROM public.ecr.aws/lambda/python:3.13@sha256:e8fcbe9388ea08bdbb19529a823bbb7e1f87e114412bc36a2fab001847507032

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
