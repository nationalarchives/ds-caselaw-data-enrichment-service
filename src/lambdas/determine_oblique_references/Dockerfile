FROM public.ecr.aws/lambda/python:3.14@sha256:426f35313ef4bd78b9ec159301e619c7708b49b22f47e9525763feb773984984

# Copy only the requirements file first and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy the rest of the code
COPY . ${LAMBDA_TASK_ROOT}
COPY utils/ ${LAMBDA_TASK_ROOT}/utils/
COPY replacer/ ${LAMBDA_TASK_ROOT}/replacer/
COPY oblique_references/ ${LAMBDA_TASK_ROOT}/oblique_references/

CMD [ "index.handler" ]
