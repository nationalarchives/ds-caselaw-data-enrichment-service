zips:
	@mkdir -p dist
	@mkdir -p package
	@STATIC_DEPS=true python3 -m pip install -t package -r src/lambdas/fetch_xml/requirements.txt
	@rm dist/fetch_xml.zip & 2>&1
	@cd package && zip -r ../dist/fetch_xml.zip * && cd ..
	@cd src/lambdas && zip -g ../../dist/fetch_xml.zip fetch_xml/index.py && cd ../..
	@cd src && zip -g ../dist/fetch_xml.zip utils/* && cd ..
	@echo 'Built dist/fetch_xml.zip'

ifeq (setup,$(firstword $(MAKECMDGOALS)))
  # use the rest as arguments for "setup"
  RUN_ARG := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(RUN_ARG):;@:)
endif

setup:
	make zips
	sh scripts/setup-localstack.sh $(RUN_ARG)

# update:
# 	make zips
# 	@sh scripts/update-lambda.sh

# send-message:
# 	@awslocal sns publish --topic-arn arn:aws:sns:us-east-1:000000000000:judgments --message file://aws_examples/sns/parsed-judgment.json

# delete-document:
# 	@curl --anyauth --user admin:admin -X DELETE -i http://localhost:8000/v1/documents\?database\=Judgments\&uri\=/ewca/civ/2022/111.xml
