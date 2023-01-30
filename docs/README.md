# Judgment Enrichment Pipeline Documentation

## 1. Introduction

This resource documents the design and operation of the Judgment Enrichment Pipeline (JEP) built for The National Archives by MDRxTECH and vLex Justis to support the publishing process that sits behind [caselaw.nationalarchives.gov.uk](https://caselaw.nationalarchives.gov.uk).

The primary purpose of the JEP is to "enrich" the judgments published on [caselaw.nationalarchives.gov.uk](https://caselaw.nationalarchives.gov.uk)) by marking up important pieces of legal information - such as references to earlier cases and legislation - cited in the body of the judgment. In certain scenarios described elsewhere in this documentation, the JEP will "repair" or *resolve* entities that are malformed whilst respecting the original text of the judgment in question.   

## 1.1 The general anatomy of the JEP

At its core, the JEP is a series of serverless functions, which we call *Annotators*, that sequentially add layers of markup to judgments submitted for enrichment. Each Annotator is responsible for performing a specific type of enrichment. For example, the [Case Law Annotator](caselaw/case-law-annotator.md) detects references to case law citations (such as [2021] 1 WLR 1) and the [Legislation Annotator](legislation/legislation-annotator.md) is responsible for marking up mentions of UK primary legislation. An overview of the *Annotators* can be found below with more detailed notes on each set out in dedicated documentation in this folder. 

The *Annotators* are supported by a cast of utility functions that are responsible for ETL, XML validation, rules-management and file manipulation. The most important of these utility functions are the [*Replacers*](the-replacers.md), which generate the enriched XML that is sent back for publication on [caselaw.nationalarchives.gov.uk](caselaw.nationalarchives.gov.uk).

A step-by-step commentary on the pipeline can be found [here](pipeline-walkthrough.md).

### 1.2 The *Annotators*

The JEP is a modular system comprising a series of AWS Lambda functions -- the *Annotators* -- that are each responsible for performing a discrete step in the enrichment pipeline. The five Annotator functions are:

1. [Case Law Annotator](caselaw/case-law-annotator.md) -- detects references to UK case law citations, such as `[2022] 1 WLR 123` 
2. [Legislation Annotator](legislation/legislation-annotator.md) -- detects references to UK primary legislation, such as `Theft Act 1968`
3. [Abbreviation Annotator](abbreviation-annotator.md) -- detects abbreviations and resolves them to their longform. For example, the longform of `HRA 1998` is `Human Rights Act 1998`
4. [Oblique Legislative References Annotator](legislation/oblique-references.md) -- detects indirect references to primary legislaton, such as `the Act` or `the 1998 Act` and determines which cited primary enactment the indirect reference corresponds to
5. [Legislative Provision Annotator](legislation/legislative-provision-annotator.md) -- identifies references to legislation provisions, such as `section 6`, and identifies the corresponding primary enactment, for example `section 6 of the Human Rights Act`

## 2 Enriching judgments: How to run the pipeline

There are two ways to operate the pipeline:

1. Triggering the pipeline via file upload to S3
2. API integration with the MarkLogic database

### 2.1 Triggering the pipeline via file upload to S3

#### 2.1.1 Upload the judgment XML to the origin bucket in S3

The JEP can be operated manually by uploading judgments directly to the JEP's trigger S3 bucket: `s3://production-tna-s3-tna-sg-xml-original-bucket/`. We recommend using the AWS CLI to achieve this, like so:

`aws s3 cp path/to/judgment.xml s3://production-tna-s3-tna-sg-xml-original-bucket/`

#### 2.1.2 Collect the enriched XML file from the terminal bucket in S3

The enrichment process typically takes five-six minutes per judgment. Enriched judgment XML is deposited in the JEP's terminal bucket: `s3://production-tna-s3-tna-sg-xml-third-phase-enriched-bucket`. Again, we recommend using the AWS CLI to retrieve the enriched XML, like so:

`aws s3 cp s3://production-tna-s3-tna-sg-xml-third-phase-enriched-bucket/judgment.xml path/to/local/dir`

## 2.2 API integration with the MarkLogic database

The standard mechanism for triggering the enrichment pipeline is via the TNA editor interface.

## 3 Tests

There is a comprehensive suite of tests that can be run locally. Clone the repository, `cd` into the `tests` directory and run:

```
$ python runner.py
```

## 4 Architecture
![Architecture](/docs/img/architecture.png)
The VCite integration is shown more distinctly in the diagram below:
![VCite-integration](/docs/img/tna-vcite-integration.png/)

## 5 Workflow

CI/CD works in the following way:
* Engineer branches from `main` branch, commits code and raises a pull request.
  * The python code within the repo is checked against formatting tools called `black` and `isort`. 
  * The Terraform code is checked against a linting tool called `TFLint`. 
  * Terraform is validated and planned against staging and production as independent checks.
* Upon merge, non dockerised lambdas are built, terraform is planned, applied and then docker images are built and pushed to ECR. This occurs for staging, if staging succeeds then the same happens for production.

## 6 DB Backups
As we use AWS Aurora, there is no multi-AZ functionality. Instead, “Aurora automatically replicates storage six ways across three availability zones”.
Each night there is an automated snapshot by Amazon of RDS.
We also run a manual snapshot of the cluster at midday (UTC) each day. This is cron based from Amazon Eventbridge that triggers a lambda. DB backups are shown in the RDS console under manual snapshots. 

## 7 Infrastructure
Here are some brief notes on extending the infrastructure. 
* The file `main.tf` at the root of the repo will invoke each of the modules, more of the same services can be created by adding to those modules. If more modules are created then `main.tf` will need to be extended to invoke them.
* Adding an S3 bucket is done by invoking the `secure_bucket` module, located at `modules/secure_bucket/`, you can see how the existing buckets are created by viewing `modules/lambda_s3/bucket.tf`, new buckets should be created by adding to this file.
If a bucket policy is added, then an extra statement will automatically be added that denies insecure transport.
* Docker images are stored in ECR. Each repo needs to exist before a docker image can be pushed to ECR. These are created in `modules/lambda_s3/lambda.tf`. 
