# Judgment Enrichment Pipeline Documentation

## 1. Introduction

This resource documents the design and operation of the Judgment Enrichment Pipeline (JEP) built for The National Archives by MDRxTECH and vLex Justis to support the publishing process that sits behind the [Find Case Law](https://caselaw.nationalarchives.gov.uk) platform.

The primary purpose of the JEP is to "enrich" the judgments published on [Find Case Law](https://caselaw.nationalarchives.gov.uk) by marking up important pieces of legal information - such as references to earlier cases and legislation - cited in the body of the judgment. In certain scenarios described elsewhere in this documentation, the JEP will "repair" or *resolve* entities that are malformed whilst respecting the original text of the judgment in question.

## 1.1 The general anatomy of the JEP

At its core, the JEP is a series of serverless functions, which we call *Annotators*, that sequentially add layers of markup to judgments submitted for enrichment. Each Annotator is responsible for performing a specific type of enrichment. For example, the [Case Law Annotator](caselaw/case-law-annotator.md) detects references to case law citations (such as `[2021] 1 WLR 1`) and the [Legislation Annotator](legislation/legislation-annotator.md) is responsible for marking up mentions of UK primary legislation. An overview of the *Annotators* can be found below with more detailed notes on each set out in dedicated documentation in this folder.

The *Annotators* are supported by a cast of utility functions that are responsible for ETL, XML validation, rules and data management and file manipulation. The most important of these utility functions are the [*Replacers*](#14-replacers), which generate the enriched XML that is sent back for publication on [Find Case Law](https://caselaw.nationalarchives.gov.uk).

A significant amount of core markup annotation is provided directly by the JEP, but it is also supported an integration with the [vLex](https://vlex.com/) vCite engine. vCite extends the JEP's functionality in a range of ways, including the addition of a comprehensive suite of case law citation matchers. See [here](/docs/vcite.md) for more detail on the vCite integration and how it is controlled.

![Phases of Enrichment](/docs/img/tna_enrichment_phases.png)

An example enriched snippet of LegalDocML feature case law citation markup looks like this:

```xml
<ref href="https://caselaw.nationalarchives.gov.uk/ewca/civ/2021/1308" uk:canonical="[2021] EWCA Civ 1308" uk:isneutral="true" uk:type="case" uk:year="2021" uk:origin="TNA">[2021] EWCA Civ 1308</ref>, <ref href="#" uk:canonical="[2022] 1 WLR 1585" uk:isneutral="false" uk:type="case" uk:year="2022" uk:origin="TNA">[2022] 1 WLR 1585</ref>
```

### 1.2 The *Annotators*

The JEP is a modular system comprising a series of AWS Lambda functions -- the *Annotators* -- that are each responsible for performing a discrete step in the enrichment pipeline. The five Annotator functions are:

1. [Case Law Annotator](caselaw/case-law-annotator.md) -- detects references to UK case law citations, such as `[2022] 1 WLR 123`
1. [Legislation Annotator](legislation/legislation-annotator.md) -- detects references to UK primary legislation, such as `Theft Act 1968`
1. [Abbreviation Annotator](abbreviation-annotator.md) -- detects abbreviations and resolves them to their longform. For example, the longform of `HRA 1998` is `Human Rights Act 1998`
1. [Oblique Legislative References Annotator](legislation/oblique-references.md) -- detects indirect references to primary legislaton, such as `the Act` or `the 1998 Act` and determines which cited primary enactment the indirect reference corresponds to
1. [Legislative Provision Annotator](legislation/legislative-provision-annotator.md) -- identifies references to legislation provisions, such as `section 6`, and identifies the corresponding primary enactment, for example `section 6 of the Human Rights Act`

### 1.3 Enrichment phases

There are four phases of enrichment. Each phase of enrichment generates enriched LegalDocML that is progressively enriched by each successive phase of enrichment.

_First Phase Enrichment_
The first phase of enrichment consists of the [Case Law Annotator](/docs/caselaw/case-law-annotator.md); the [Legislation Annotator](/docs/legislation/legislation-annotator.md); and the [Abbreviations Annotator](/docs/abbreviation-annotator.md)

_Second Phase Enrichment_
The second phase of enrichment consists of the [Oblique Legislative References Annotator](/docs/legislation/oblique-references.md)

_Third Phase Enrichment_
The third phase of enrichment consists of the [Legislative Provision Annotator](/docs/legislation/legislative-provision-annotator.md)

_Fourth Phase Enrichment_
The fourth and final phase of enrichment consists of the [vCite integration](/docs/vcite.md)

### 1.4 Replacers

The [Replacers](/replacer/) are responsible for registering the various entities detected by the [Annotators](#12-the-annotators), including their entity types and position in the judgment body. The registered replacements are then applied to the judgment body through a series of string manipulations by the [`make_replacements`](/lambda/make_replacements/) lambda.

There are two sets of replacer logic. The [first set](/replacer/replacer.py) provides the logic for first phase enrichment replacements. The [second set of replacer logic](/replacer/second_stage_replacer.py) handles replacement in the second and third phases of enrichment.

### 1.5 Re-enrichment

It is possible for the same judgment to be submitted for enrichment on multiple occasions, which creates the risk that existing enrichment present in the judgment will break as additional enrichment is added to the judgment. To address this, the JEP "sanitises" the judgment body prior to making replacements. The sanitisation process is simply performed by stripping existing `</ref>` tags from the judgment. This logic is handled in the [make_replacements](/lambda/make_replacements/index.py) lambda.

**IMPORTANT:** the sanitisation step does not currently distinguish between enrichment supplied by the JEP itself, by vCite or from some other source! Particular care should be taken to avoid inadvertently removing vCite enrichment by re-enriching a judgment that includes vCite enrichment when the [vCite integration](vcite.md) is switched off.

## 2 Adding new citation rules to the Case Law Annotator

The Case Law Annotator uses a rules-based engine, the *Rules Manifest*, which is built on top of the [spaCy EntityRuler](https://spacy.io/api/entityruler) to detect case law citations (e.g. \`\[2022\] 1 WLR 123). The *Rules Manifest* is stored as a table in Postgres where each row in the table represents a rule.

The creation of rules is currently managed by modifying and uploading a CSV version of the *Rules Manifest*, which is stored in `production-tna-s3-tna-sg-rules-bucket` with a filename conforming to the pattern `yyyy_mm_dd_Citation_Manifest.csv`.

See [here](/docs/caselaw/updating-the-rules-manifest.md) for guidance on how to create and modify rules in the *Rules Manifest*.

## 3 Enriching judgments: How to run the pipeline

There are two ways to operate the pipeline:

1. Triggering the pipeline via file upload to S3
1. API integration with the MarkLogic database

### 3.1 Triggering the pipeline via file upload to S3

#### 3.1.1 Upload the judgment XML to the origin bucket in S3

The JEP can be operated manually by uploading judgments directly to the JEP's trigger S3 bucket: `s3://production-tna-s3-tna-sg-xml-original-bucket/`. We recommend using the AWS CLI to achieve this, like so:

`aws s3 cp path/to/judgment.xml s3://production-tna-s3-tna-sg-xml-original-bucket/`

#### 3.1.2 Collect the enriched XML file from the terminal bucket in S3

The enrichment process typically takes five-six minutes per judgment. Enriched judgment XML is deposited in the JEP's terminal bucket: `s3://production-tna-s3-tna-sg-xml-third-phase-enriched-bucket`. Again, we recommend using the AWS CLI to retrieve the enriched XML, like so:

`aws s3 cp s3://production-tna-s3-tna-sg-xml-third-phase-enriched-bucket/judgment.xml path/to/local/dir`

## 3.2 API integration with the MarkLogic database

The standard mechanism for triggering the enrichment pipeline is via the TNA editor interface.

## 4 Tests

There is a comprehensive suite of tests that can be run locally. Clone the repository, `cd` into the `tests` directory and run:

```sh
python runner.py
```

## 5 Architecture

![Architecture](/docs/img/architecture.png)
The VCite integration is shown more distinctly in the diagram below:
![VCite-integration](/docs/img/tna-vcite-integration.png/)

## 6 Workflow

CI/CD works in the following way:

- Engineer branches from `main` branch, commits code and raises a pull request.
  - The Python code within the repo is checked against formatting tools called `black` and `isort`.
  - The Terraform code is checked against a linting tool called `TFLint`.
  - Terraform is validated and planned against staging and production as independent checks.
- Upon merge, non dockerised lambdas are built, terraform is planned, applied and then docker images are built and pushed to ECR. This occurs for staging, if staging succeeds then the same happens for production.

* When a pull request is opened a series of checks are made, against both staging and production:
  - Python Black (Formats python code correctly)
  - Python iSort (Orders imports correctly)
  - TFLint (Terraform Linter)
  - Terraform Validate
  - Terraform init.
  - Terraform Plan (A plan of the infrastructure changes for that environment)
* If the checks fail due to Python Black.
  A message such as `Oh no! 💥 💔 💥 13 files would be reformatted, 5 files would be left unchanged.`
  - To fix this, install black locally `pip install black`, then run `black .` and commit the reformatted code.
* If the check fails due to iSort. A message such as `ERROR: Imports are incorrectly sorted.`
  - To fix this, install isort locally `pip install isort`, then run `isort .`
* TFLint will explain any errors it finds.
* Terraform plan needs to be inspected before merging code to ensure the right thing is being applied.
  Do not assume that a green build is going to build what you want to be built.
* Upon merge, staging environment docker images will be built and pushed to ECR, staging environment Terraform code will be applied.
  On success of the staging environment, production environment docker images will be built and pushed to ECR, production environment Terraform code will be applied.

## 7 DB Backups

As we use AWS Aurora, there is no multi-AZ functionality. Instead, “Aurora automatically replicates storage six ways across three availability zones”.

Each night there is an automated snapshot by Amazon of RDS.
We also run a manual snapshot of the cluster at midday (UTC) each day. This is cron-based from Amazon Eventbridge that triggers a [lambda](/lambda/db_backup/index.py). DB backups are shown in the RDS console under manual snapshots.

## 8 Infrastructure

Here are some brief notes on extending the infrastructure.

- The file `main.tf` at the root of the repo will invoke each of the modules, more of the same services can be created by adding to those modules. If more modules are created then `main.tf` will need to be extended to invoke them.
- Adding an S3 bucket is done by invoking the `secure_bucket` module, located at `modules/secure_bucket/`, you can see how the existing buckets are created by viewing `modules/lambda_s3/bucket.tf`, new buckets should be created by adding to this file.
  If a bucket policy is added, then an extra statement will automatically be added that denies insecure transport.
- Docker images are stored in ECR. Each repo needs to exist before a docker image can be pushed to ECR. These are created in `modules/lambda_s3/lambda.tf`.

## 9 Turning Enrichment Off

There are a number of places where enrichment can be turned off:

- Marklogic Username/Password

  - Go to the production Marklogic interface, "Admin" (top), "Security" (left), "Users" (left), "enrichment-engine" (mid).
  - Make sure you know where the password is stored so you can put access back afterwards!
  - Changing the password will mean no Enrichment processes can interact with Marklogic -- no getting documents, no uploading them
  - Messages will still be sent from the Editor interface, and will build up.
  - Purge the queues in AWS before turning Enrichment back on, unless you're confident there is nothing bad in there.
  - Seemed to work well last time, but there were a lot of warnings

- AWS Lambda that fetches XML

  - Not actually tested in anger!
  - Log into `da-caselaw-enrichment`. Make sure to switch to `eu-west-2`/`London`.
  - In Lambda, Functions, select `tna-s3-tna-production-fetch-xml`
  - Top left, press Throttle.
  - This will prevent any ingestion of the incoming messages which will build up
  - Anything currently in process will finish and will continue to run to completion
  - You can change the concurrency settings to unthrottle it
