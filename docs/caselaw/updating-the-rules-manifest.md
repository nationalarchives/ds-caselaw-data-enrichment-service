# Updating the Rules Manifest

The [Case Law Annotator](/docs/caselaw/case-law-annotator.md) is rules-based engine that detects and enriches citations to case law. The rules that underpin this functionality are managed in, and derived from, the *Rules Manifest* -- a single table dataset where each row contains a spaCy entity rule that matches a citation pattern and an assortment of related data, such as whether the rule matches the relevant citation's canonical form and whether the citation is a neutral citation. You can read more about the [*Rules Manifest*](/docs/caselaw/case-law-annotator.md#the-rules-manifest-canonical-and-malformed-citations) and its attributes [here](/docs/caselaw/case-law-annotator.md)

The purpose of this note is to set out the steps you need to take to update the *Rules Manifest*. 

## Step 1: Download the current version of the Rules Manifest

The first step is to download the current version of the Rules Manifest from the `production-tna-s3-tna-sg-rules-bucket` S3 bucket. We recommend using the AWS console to perform this step. The file naming convention for the manifest is `yyyy-mm-dd_Citation_Manifest.csv` and the file will be located at the top-level of the `production-tna-s3-tna-sg-rules-bucket` folder structure. 

## Step 2: Make the changes to the rules file

Our strong recommendation is to work in a code editor when making changes to the rules file rather than in Excel or some other spreadsheet GUI. Applications like Excel commonly introduce unwanted character changes, particularly where double-quotes are concerned (and these are used extensively throughout the rules file)!

The *Rules Manifest* already contains a large number of rules that match canoncial and malformed variants of case law citations. As such, it is more likely than not that a rule already exists that will serve as a clse template for the new rule you wish to create. We recommend spending the time finding an example that closely matches the rule under construction. This can then be copied and pasted on a new line and edited. 

### Set the new rule's attributes
Assuming you have followed our recommendation to use an existing rule as a template, the next step is to update **all** of the attributes. Care should be taken to ensure every column is updated, but particular care should be taken with respect to the following attributes:

* `id`: this must be unique and match the id attribute in the spaCy rule specified in the `pattern` column. For ease, the convention is to set the ``id` to follow the series/citation abbreviation. If the rule matches a malformed variant, the convention is to use the `id` for the canonical variant, suffixed with `_a`, `_b` etc 
* `isCanonical`: this attribute tells the JEP whether or not the citation matched by the relevant rule is a canonical or malformed variant of the matched citation. When this value is set to `True` the [correction strategies](/rules/correction_strategies.py) are bypassed. 
* `matchExample`: the `matchExample` attribute holds a literal example of the citation targeted by the relevant rule. It serves two purposes. First, it provides a convenient example of what we're expecting the relevant rule to match. Second, it is used in a unit test to check that the corresponding rule does in fact match the expected citation.
* `citationType`: the citation type defines the structure of the canonical form of the target citation. This is used by the select the relevant correction strategy.

The various [rules attributes](/docs/caselaw/case-law-annotator.md#rule-attributes) and [citation types](/docs/caselaw/case-law-annotator.md#citation-types)[ [here](/docs/caselaw/case-law-annotator.md#rule-attributes) and [here](/docs/caselaw/case-law-annotator.md#citation-types), respectively.

### Craft the rule pattern

The rule pattern is responsible for the detecting the actual match to the target citation. The patterns are spaCy [EntityRuler](https://spacy.io/usage/rule-based-matching#entityruler) patterns and look like so:

```json
"{""id"": ""wlr"", ""description"": ""The Weekly Law Reports (ICLR)"", ""label"": ""CITATION"", ""pattern"": [{""ORTH"": ""[""}, {""SHAPE"": ""dddd""}, {""ORTH"": ""]""}, {""LIKE_NUM"": true}, {""ORTH"": ""WLR""},{""LIKE_NUM"": true}]}"
```

Each pattern consists of an `id`, which should exactly match the `id` assigned for the rule; a `description`, which by convention matches the `description` in the rule; a `label`, which allows us to categorise the type of match (in this case, a `CITATION`); followed by the pattern sequence itself:

```json
[{""ORTH"": ""[""}, {""SHAPE"": ""dddd""}, {""ORTH"": ""]""}, {""LIKE_NUM"": true}, {""ORTH"": ""WLR""},{""LIKE_NUM"": true}]
```

The pattern sequence works at the token level, and spaCy's tokenizer provides a rich array of [token attributes](https://spacy.io/api/token#attributes) that you can use to control the pattern's match behaviour. 

Once you're finished crafting the rule, save the file as a CSV under a new name. We recommend sticking with the `yyyy-mm-dd_Citation_Manifest.csv` convention. 

## Step 3: Moved the old manifest rules files and pattern files to archive

Before uploading the new rules manifest file to S3 we recommend archiving the old rules file in the `Manifest_versions` folder and the the old `citation_patterns.jsonl` file in the `Citation_patterns_versions` folder. 

## Step 4: Upload the new rules manifest file to S3

Now upload the updated rules file to the `production-tna-s3-tna-sg-rules-bucket` S3 bucket. The file should be placed at the top level of the bucket's folder structure. Again, we recommend using the AWS console, but this can also be achieved from the command line. 

Successful upload of the updated rules file will trigger the [update_rules_processor](/lambda/update_rules_processor/index.py) lambda, which in turn performs the following functions:

1. The rules file is tested and if tests pass, the rules table in Postgres is updated. This table is used at enrichment-time to provide metadata for the matched citation, such as whether the citation is canonical and, in the case of malformed citations, the appropriate correction strategy.
2. The pattern field in the rules file is extracted to a newline JSON file called `citation_patterns.jsonl`. This JSONL file is loaded into the `nlp` object for when the [Case Law Annotator](/docs/caselaw/case-law-annotator.md) runs.
