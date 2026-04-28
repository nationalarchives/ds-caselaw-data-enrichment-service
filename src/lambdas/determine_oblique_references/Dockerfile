FROM public.ecr.aws/lambda/python:3.14@sha256:9337593a0777142e10c688b0d8daa3d6dbcaf4c94d7936f77aa09b7c19c61b1e

# Copy only the requirements file first and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy the rest of the code
COPY . ${LAMBDA_TASK_ROOT}
COPY utils/ ${LAMBDA_TASK_ROOT}/utils/
COPY replacer/ ${LAMBDA_TASK_ROOT}/replacer/
COPY oblique_references/ ${LAMBDA_TASK_ROOT}/oblique_references/

CMD [ "index.handler" ]
