FROM public.ecr.aws/lambda/python:3.12@sha256:60d905e5b5329af7f2bd8289c5f989b91a33963e9908b29511b2d119721e67d0

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONIOENCODING=UTF-8

# Install dependencies first for layer caching
COPY src/lambdas/enrichment_lambda/requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy the full src tree so shared packages resolve without a generated copy tree
COPY src/ ${LAMBDA_TASK_ROOT}/

CMD ["lambdas.enrichment_lambda.index.handler"]
