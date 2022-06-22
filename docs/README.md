# Judgment Enrichment Pipeline Documentation

## Introduction

This resource documents the design and operation of the Judgment Enrichment Pipeline (JEP) built for The National Archives by MDRxTECH and vLex Justis to support the publishing process that sits behind [caselaw.nationalarchives.gov.uk](caselaw.nationalarchives.gov.uk).

The primary purpose of the JEP is to "enrich" the jugdments published on [caselaw.nationalarchives.gov.uk](caselaw.nationalarchives.gov.uk) by marking up important pieces of legal information, such as references to earlier cases and legislation, that are cited in the judgments. In certain scenarios described elsewhere in this documentation, the JEP will "repair" or *resolve* entities that are malformed whilst respecting the original text of the judgment in question.   

Architecturally, the JEP is composed of a series of serverless *Annotators* that sequentially add layers of enrichment to an incoming judgment. An overview of the *Annotators* can be found below with more detailed guidance on each set out in dedicated documentation. 

## The general anatomy of the JEP

### The *Annotators*

The JEP is a modular system comprising a series of AWS Lambda functions that are each responsible for a discrete element of the processing pipeline. The current version of the JEP has four *Annotators*. They are:

1. [Case Law Annotator](caselaw/case-law-annotator.md) -- detects references to UK case law citations, such as `[2022] 1 WLR 123` 
2. [Legislation Annotator](legislation-annotator.md) -- detects references to UK primary legislation, such as `Theft Act 1968`
3. [Abbreviation Annotator](abbreviation-annotator.md) -- detects abbreviations and resolves them to their longform. For example, the longform of `HRA 1998` is `Human Rights Act 1998`.
4. [Legislative Provision Annotator](legislative-provision-annotator.md)
5. [Oblique Legislative References Annotator](oblique-references.md)

### The pipeline in overview

** Add diagram of JEP**

## Operating the pipeline

There are two ways to operate the pipeline:

1. Triggering the pipeline via file upload to S3
2. API integration with the MarkLogic database

## 1. Triggering the pipeline via file upload to S3

### Upload the judgment XML to the origin bucket in S3

The JEP can be operated manually by uploading judgments directly to the JEP's trigger S3 bucket: `s3://production-tna-s3-tna-sg-xml-original-bucket/`. We recommend using the AWS CLI to achieve this, like so:

`aws s3 cp path/to/judgment.xml s3://production-tna-s3-tna-sg-xml-original-bucket/`

### Collect the enriched XML file from the terminal bucket in S3

The enrichment process typically takes five-six minutes per judgment. Enriched judgment XML is deposited in the JEP's terminal bucket: `s3://production-tna-s3-tna-sg-xml-enriched-bucket`. Again, we recommend using the AWS CLI to retrieve the enriched XML, like so:

`aws s3 cp s3://production-tna-s3-tna-sg-xml-enriched-bucket/judgment.xml path/to/local/dir`

## 2. API integration with the MarkLogic database

Not yet implemented

## Tests
