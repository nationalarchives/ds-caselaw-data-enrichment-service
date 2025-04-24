FROM public.ecr.aws/lambda/python:3.12@sha256:f68c08c8de35922db08a27d0f0014860ffe5b4cdac290062780f0d6f6af6ea3c

# Copy only the requirements file first and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy the rest of the code
COPY . ${LAMBDA_TASK_ROOT}
COPY utils/ ${LAMBDA_TASK_ROOT}/utils/
COPY replacer/ ${LAMBDA_TASK_ROOT}/replacer/
COPY oblique_references/ ${LAMBDA_TASK_ROOT}/oblique_references/

CMD [ "index.handler" ]
