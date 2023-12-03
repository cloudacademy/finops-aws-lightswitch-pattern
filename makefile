export LAMBDA_NAME=cloudacademy-calc-pi
export LAMBDA_REGION=us-west-2
export IAM_ROLE_ARN=TOKEN_IAM_ROLE_ARN
export S3_BUCKET_NAME=TOKEN_S3_BUCKET_NAME

SHELL = bash

.DEFAULT_GOAL := all

libs: requirements.txt
	@[ -d $@ ] || mkdir $@
		pip3.10 install -r $< \
		--platform manylinux2014_x86_64 \
		--target=$@ \
		--implementation cp \
		--only-binary=:all: --upgrade

release.zip: libs lambda_function.py
	zip -rq $@ *.py
	cd $< && zip -rq ../$@ *

.PHONY: deploy
deploy: release.zip
	aws lambda create-function \
		--function-name "${LAMBDA_NAME}" \
		--runtime python3.10 \
		--timeout 60 \
		--zip-file fileb://$< \
		--handler lambda_function.lambda_handler \
		--role "${IAM_ROLE_ARN}" \
		--environment '{"Variables":{"S3_BUCKET_NAME":"${S3_BUCKET_NAME}"}}' \
		--tracing-config 'Mode=Active' \
		--region "${LAMBDA_REGION}" \
		| jq -r ".State"
	@echo "lambda function created..."
	aws lambda wait function-active \
		--function-name "${LAMBDA_NAME}" \
		--region="${LAMBDA_REGION}"
	@echo "lambda function is active..."
	aws lambda create-function-url-config \
		--function-name "${LAMBDA_NAME}" \
		--auth-type "NONE" \
		| jq -r ".FunctionUrl"
	aws lambda add-permission \
		--function-name "${LAMBDA_NAME}" \
		--action lambda:InvokeFunctionUrl \
		--principal "*" \
		--statement-id "${LAMBDA_NAME}" \
		--function-url-auth-type "NONE"
	aws lambda wait function-updated \
		--function-name "${LAMBDA_NAME}" \
		--region="${LAMBDA_REGION}"
	@echo "lambda function is ready..."

.PHONY: update
update: release.zip
	aws lambda update-function-code \
		--function-name "${LAMBDA_NAME}" \
		--zip-file fileb://function.zip \
		--zip-file fileb://$< \
		--region="${LAMBDA_REGION}" \
		| jq -r ".LastUpdateStatusReason"
	aws lambda wait function-updated \
		--function-name "${LAMBDA_NAME}" \
		--region="${LAMBDA_REGION}"
	@echo "lambda function updated..."

.PHONY: delete
delete:
	-aws lambda delete-function-url-config \
		--function-name "${LAMBDA_NAME}"
	-aws lambda delete-function \
		--function-name "${LAMBDA_NAME}"
	@echo "lambda function is deleted..."

.PHONY: invoke
invoke:
	aws lambda invoke \
		--function-name "${LAMBDA_NAME}" \
		--region="${LAMBDA_REGION}" \
		--cli-binary-format raw-in-base64-out \
		--payload '{"queryStringParameters": {"num": "1000"}}' \
		--log-type Tail \
		out \
		| jq ".LogResult" -r | base64 -d

.PHONY: clean
clean:
	rm release.zip

.PHONY: all
all: libs release.zip deploy invoke