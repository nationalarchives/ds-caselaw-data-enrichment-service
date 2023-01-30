# The Case Law Annotator

## Overview
The Case Law Annotator is the first *Annotator* function in the pipeline and is followed by the [Legislation Annotator](../legislation/legislation-annotator.md)). The purpose of the Case Law Annotator is to detect and markup citations to UK case law cited in the judgment being processed. The Case Law Annotator uses a rules-based engine, the *Rules Manifest*, which is built on top of the [spaCy EntityRuler](https://spacy.io/api/entityruler). The [*Rules Manifest*]() is stored as a table in Postgres where each row in the table represents a rule. 

The Case Law Annotator provides the following core functionality:

1. Detects references to well-formed (canonical) citations and malformed citations
2. Casts malformed case citations to their canonical form
3. Marks up the detected references in the LegalDocML

## XML and attributes

The primary purpose of the Case Law Annotator is to apply LegalDocML markup to references to case law present in the judgment. This serves many downstream use-cases, such as generating lists of citing and cited cases for a given judgment or generating a citation graph. 

The following snippet provides an example of enriched references to case law (a neutral citation and a reference to a case reported in The Weekly Law Reports):

```xml
<ref href="https://caselaw.nationalarchives.gov.uk/ewca/civ/2021/1308" uk:canonical="[2021] EWCA Civ 1308" uk:isneutral="true" uk:type="case" uk:year="2021">[2021] EWCA Civ 1308</ref>, <ref href="#" uk:canonical="[2022] 1 WLR 1585" uk:isneutral="false" uk:type="case" uk:year="2022">[2022] 1 WLR 1585</ref>
```
References to case law are enclosed in `</ref>` tags with the following five attributes:

* `href`: the TNA URI for the judgment that corresponds to the detected citation. Note that this attribute is only assigned a value where the value of `uk:isneutral` is `true`
* `uk:canonical`: the canonical form of the detected citation
* `uk:isneutral`: whether the detected citation is a neutral citation 
* `uk:type`: the type of `ref` element. For case law citations this is always set to `case`
* `uk:year`: the year extracted from the detected citation, if present. Note: the value of `year` reflects the year in the detected citation, which is not necessarily the same as the year of judgment

## Implementation details

The input to the Case Law Annotator is the raw text of the judgment body of the incoming judgment XML file to be enriched. The output is a list of replacements and associated metadata that is sent to the first phase enrichment [replacer](/docs/the-replacers.md).

The Case Law Annotator uses a deterministic rules-based approach to identify case law citations and apply any necessary correction strategies to malformed citations (these are explained extensively in the documentation that follows).

The heart of the Case Law Annotator is the *Rules Manifest*, a set of citation detection rule patterns and associated data stored in Postgres. Whenever the Rules Manifest is updated and re-ingested into Postgres, the spaCy rule patterns are extracted to a JSONL file, `citation_patterns.jsonl`, which is stored in S3 (`production-tna-s3-tna-sg-rules-bucket`). 

When a new judgment arrives for enrichment, the following process occurs:

1. The incoming judgment XML is parsed and the raw text of the judgment body is extracted.
2. The Case Law Annotator constructs a spaCy `nlp` pipeline in memory. `citation_patterns.jsonl` is read from S3 and is then used to build an `EntityRuler` component which is added to the end of the spaCy model pipeline. It is this component that performs the citation detection. Detected citations are analogous to detected entities in a standard spaCy model. 
3. The raw text of the judgment body is passed to the `nlp` pipeline to create a spaCy `Doc` object. The `EntityRuler` is applied to the judgment. This returns a list of tuples, the elements of which include the detected citation text and the `id` of the rule responsible for the match. 
4. The rule `id` is used to query the Rules Manifest in Postgres for the associated metadata about the matched citation, such as whether the matched citation is a neutral citation, the citation type and whether the matched citation adheres to the canonical form. 
5. In the event that the matched citaion does not adhere the canonical form specified in the Rules Manifest, a [correction strategy](/caselaw_extraction/correction_strategies.py) is applied generate the canonical form. The canonical form is written back to the resultant enriched XML as a value on the `uk:canonical` attribute on the `</ref>` tag wrapped around the matched citation.
6. Metadata for each citation match, including the text of the citation match itself and the associated canonical form, is passed to the [replacer](/docs/the-replacers.md) responsible for first phase enrichment.  


## Detection of Canonical and Malformed Citations
The accuracy with which case law citations are used in judgments is highly variable. Some citations are perfect and follow the *canonical form*. For example, the correct, or canonical, way to cite a case reported in *The Weekly Law Reports* is like so: `[year] vol WLR page`or `[2022] 1 WLR 123`. The square brackets are present and are the correct way round. The volume number has been included. There are no fullstops interspersed through the series abbreviation. The citation is just right. 

Sometimes citations are less than perfect: they do not follow the *canonical form* and are *malformed*. For example, whilst there is only one way to correctly cite a case reported in *The Weekly Law Reports* there are many wrong ways. One example of this might be to incorrectly specify the series abbreviation, such as `[2022] 1 Weekly LR 123` instead of `[2022] 1 Weekly LR 123`. Sometimes more minor typographic mistakes are introduced, such as muddled opening and closing square brackets: `]2022] 1 WLR 123`. 

The Case Law Annotator has been designed to detect both canonical and malformed variations of the case law citations that are most often found in judgments given in the courts of England and Wales. It does so by using rules (contained in the *Rules Manifest*) to specify which citation patterns to match against and whether those patterns match the canonical form of a citation or not. For example, there is a rule that matches the canonical form of a citation to a case reported in *The Weekly Law Reports*. That rule's `id` is `wlr`. 

This is what the *Rules Manifest* entry for the canonical form of The Weekly Law Report looks like (we examine these rules in more depth [here](/docs/caselaw/adding-new-citation-rules.md)):

```csv
id,family,description,uri_template,canonical_form,canonical_example,match_example,citation_type,is_canonical,is_neutral,jurisdiction,pattern
wlr,WLR,The Weekly Law Reports (ICLR),,[dddd] d1 WLR d2,[2022] 1 WLR 123,[2022] 1 WLR 123,PubYearNumAbbrNum,TRUE,FALSE,EW,"{""id"": ""wlr"", ""description"": ""The Weekly Law Reports (ICLR)"", ""label"": ""CITATION"", ""pattern"": [{""ORTH"": ""[""}, {""SHAPE"": ""dddd""}, {""ORTH"": ""]""}, {""LIKE_NUM"": true}, {""ORTH"": ""WLR""},{""LIKE_NUM"": true}]}"
```

It is common to see citations to cases reported in *The Weekly Law Reports* sprinkled with fullstops in the abbreviation section so that they look like this: `[2022] 1 W.L.R. 123`. Such a reference is regarded by the Case Law Annotator as *malformed*. The *Rules Manifest* has a rule to detect this malformed variant; the `id` of that rule is `wlr_a`. 

```csv
id,family,description,uri_template,canonical_form,canonical_example,match_example,citation_type,is_canonical,is_neutral,jurisdiction,pattern
wlr_a,WLR,The Weekly Law Reports (ICLR),,[dddd] d1 WLR d2,[2022] 1 WLR 123,[2022] 1 W.L.R. 123,PubYearNumAbbrNum,FALSE,FALSE,EW,"{""id"": ""wlr_a"", ""description"": ""The Weekly Law Reports (ICLR)"", ""label"": ""CITATION"", ""pattern"": [{""ORTH"": ""[""}, {""SHAPE"": ""dddd""}, {""ORTH"": ""]""}, {""LIKE_NUM"": true}, {""ORTH"": ""W.L.R.""},{""LIKE_NUM"": true}]}"
```
### A look at some of the attributes of a rule

The structure of the rules is outlined below. However, it is worth highlighting certain features of the rules above before continuing. 

#### `family`
The first feature is the `family`, which is set to `WLR` in the case of the two examples rules set out above. There is a `family` of rules that cater for references to cases reported in *The Weekly Law Reports* and many other series of law reports.  

A `family` must have at least one rule that matches the canonical form. That is to say, a `family` must have at least one rule for which the `isCanonical` attribute  is `TRUE`. 

For most series of law reports and neutral citation there will only be one canonical form, but this is not universal. For example, the current series of *The Law Reports* published by the Incorporated Council of Law Reporting for England and Wales are an example when it is necessary to create multiple rules where `isCanonical` is set to `TRUE`. In the case of *The Law Reports*, there are years where the printed series runs across multiple volumes, which makes the inclusion of a volumne number necessary: e.g. `[2022] 1 AC 123`. In contrast, some years will only run to one volume, in which case the correct style is to omit a volumne number: e.g. `[2022] AC 123`. 

#### `id`
Each rule requires its own unique `id`. This identifier is used at inference time to access various information about the citation and the rule that detected it. Notice that the `id` in the first snippet above, which matches the canonical form, is simply `wlr`. The `id` for the second snippet, which matches a malformed variant, is `wlr_a`.  A convention of the *Rules Manifest* is that the `id` for rules that match malformed variants should use the `id` for the canonical rule with an `_a`, `_b`, `_c` etc appended to the end. This ensures that all rule IDs are unique whilst providing a coherent way of grouping rules together.

#### `isCanonical`
Each rule must specify whether the pattern matches the canonical form or a malformed variant of the target citation by setting `is_canonical` to `TRUE` or `FALSE`. This flag tells the *Case Law Annotator* whether or not it needs to apply a [correction](/caselaw_extraction/correction_strategies.py) strategy to cast the malformed reference to the canonical form. 

#### `canonicalForm`
Every rule, regardless of whether it matches a canonical citation or a malformed variant, contains the `canonicalForm` of the matched reference. The `canonical` form acts as a template of sorts that the Case Law Annotator uses to cast malformed citations to the canonical form. 

For example, the `canonical_form` for the `family` of rules dealing with references to *The Weekly Law Reports*, `WLR`, is as follows:
`[dddd] d1 WLR d2` 

The `canonicalForm` should be the same across the entire `family` of citations, save in the limited circumstances a family contains more than one canonical pattern.

#### `pattern`
The `pattern` attribute stores the actual spaCy [matcher](https://spacy.io/api/matcher) pattern responsible for detecting the citation. The pattern to match the canonical form of citations in *The Weekly Law Reports* is as follows:

```json
"{""id"": ""wlr"", ""description"": ""The Weekly Law Reports (ICLR)"", ""label"": ""CITATION"", ""pattern"": [{""ORTH"": ""[""}, {""SHAPE"": ""dddd""}, {""ORTH"": ""]""}, {""LIKE_NUM"": true}, {""ORTH"": ""WLR""},{""LIKE_NUM"": true}]}"
```
The patterns work at the token level in a manner similar to a very verbose regular expression. Whenever the *Rules Manifest* [is updated](/docs/caselaw/adding-new-citation-rules.md) the patterns are written to a newline JSON file, `citation_patterns.json`, which is then consumed by the NLP pipeline at inference time.  

The pattern above breaks down in the following way:
* The `id` attribute mirrors the `id` attribute of the rule (in this case `wlr`)
* The `description` attributes mirrors the `description` attribute of the rule.
* The `label` attribute captures the type of entity detected by the pattern, in this case a `CITATION`. 
* The `pattern` itself then specifies the token attributes this rule detects:
	* `{""ORTH"": ""[""}`: opening square bracket,
	* `{""SHAPE"": ""dddd""}`: four-digit number, 
	* `{""ORTH"": ""]""}`: closing square bracket
	* `{""LIKE_NUM"": true}`: a token that represents a number
	* `{""ORTH"": ""WLR""}`: WLR
	* `{""LIKE_NUM"": true}]}`: a token that represents a number


## The Rules Manifest, Canonical and Malformed Citations

The concept of **canonical** and **malformed** citations is central to the design of the Case Law Annotator and the system of rules that underpins it, the *Rules Manifest*. 

### Canonical citations
Canonical citations are citations that exactly follow the correct form of the given citation. A canonical citation will not:
* Introduce unnecessary matter into the citation, such as punctuation marks;
* Introduce erroneous matter, such as an incorrect series abbreviation (e.g. `Weekly LR` instead of `WLR`)
* Omit necessary matter, such as the volume number, if a volume number is required (e.g. `[2022] WLR 456` instead of `[2022] 1 WLR 456`

The Rules Manifest imports the concept of canonical citations into a rule attribute called `canonicalForm`. The `canonicalForm` for a rule serves as a template for a well-formed citation. The Case Law Annotator uses this template to generate a "corrected" citation from a detected malformed version. 

The `canonicalForm` is simply a well-formed articulation of the relevant citation with placeholder strings for the numeric components of the citation, such as the year (`dddd`), the volume number (`d1`) and the page number, which is `d2` for citations that have a volume number and `d+` for citations that do not include a volumne number. 

:warning: There should be one and only one canonical rule for a given citation family. 

### Malformed citations
Malformed citations are the opposite of canonical citations: they are citations that contain some error or unnecessary material. Where possible, the Case Law Annotator applies a [correction strategy](/caselaw_extraction/correction_strategies.py) to resolve the malformed citation to the corresponding canonical form. 

Crucially, the Case Law Annotator does not alter the original citation used by the judge. The philosophy of the JEP is to respect and preserve the original content of the judgment whilst generating well-formed and accurate data. Accordingly, where the Case Law Annotator detects a malformed citation, the canonical form of that citation is stored in the `canonicalForm` attribute of the `</ref>` tag surrounding the citaiton in question. 

### Rule Attributes

| Attribute | Required or Optional | Detail |
|-----------|----------------------|--------|
|id|Required|Each rule requires a unique `id`.<br><br> By convention, the `id` for the canonical form of a given rule follows the abbreviation used by the case law citation the rule matches against. For example, the `id` for the rule that matches _The Weekly Law Reports_ is `wlr`. <br><br> |
|family|Required|A short descriptive label that describes a collection of rules that relate to a single report series or citation type. For example, the family for The Weekly Law Reports is `WLR`.|
|description|Required|A longer description of the report series of citation type detected by the relevant rule. The same `description` should be used across a `family`. We recommend using the full formal name of the relevant series of reports (e.g. *The Weekly Law Reports*) or, in the case of neutral citations, the full name of the relevant court (e.g. *Court of Appeal (Civil Division*)).|
|uriTemplate|Optional|The template for the TNA URI used to populate the value of the `href` attribute on the `</ref>` element. The base URI is https://caselaw.nationalarchives.gov.uk/, which will generally be followed by the court and placeholder for year and document number (e.g. https://caselaw.nationalarchives.gov.uk/ewfc/year/d1). The URItemplate should only be provided for citations where `isNeutral` is `True` <br><br> For neutral citations with multiple numeric identifiers, such as the General Regulatory Chamber of the First Tier Tribunal, two numeric placeholders (`d1` and `d2`) are used in the uriTemplate, https://caselaw.nationalarchives.gov.uk/ukftt/grc/year/d1_d2. 
|canonicalForm|Required|The template for the detected citation's canonical form, e.g. `[dddd] d1 WLR d2`. <br><br> The `canonicalForm` is used in combination with the `citationType` to resolve malformed citations to their canonical form, see [correction_strategies.py](/caselaw_extraction/correction_strategies.py).|
|canonicalExample|Required|An example of a well-formed citation matched by the relevant family of rules. The main purpose of the `canonicalExample` is to provide an example of a well-formed citation for a given rule.|
|matchExample|Required|The `matchExample` is an example of a citation intended to be detected by the corresponding rule. The main purpose of the `matchExample` is to test that a given rule does in fact match the intended citation style. The `matchExample` is used in automated tests that run whenever a [modified version of the Rules Manifest is uploaded to S3](/docs/caselaw/adding-new-citation-rules.md).|
|citationType|Required|Every canonical form of citation belongs to one of ten `citationType`s. The types are outlined in the table below. The `citationType` is used to determine the relevant correction strategy for a given malformed citation.|
|isNeutral|Required|Whether the detected citation is a neutral citation.|
|jurisdiction|Required|`jurisdiction` records the geographic jurisdiction of the relevant reports series/neutral citation. The current version of the JEP assumes one of three values, `EW`; `UK`; and `EU`|
|pattern|Required|The `pattern` attribute stores the actual spaCy [matcher](https://spacy.io/api/matcher) pattern responsible for detecting the relevant citation.|

### Citation Types

This table provides a breakdown of the ten citation types (see `citationType` above) that are used to select the appropriate correction strategy. 

| Citation Type | Example|
|-----------|----------------------|
|`NCitYearAbbrNum`|[2022] EWCA Civ 123|
|`NCitYearAbbrNumDiv`|[2022] EWHC 123 (Admin)|
|`PubYearAbbrNum`|[2022] QB 123|
|`NCitYearAbbrNumUnderNumDiv`|[2022] UKFTT 2020_0341 (GRC)|
|`NCitYearAbrrNumStrokeNum`|[2022] UKET 123456/2022|
|`PubYearNumAbbrNum`|[2022] 1 WLR 123|
|`PubAbbrNumAbbrNum`|LR 1 QB 123|
|`PubNumAbbrNum`|1 PD 123|
|`EUCCase`|Case C-123/12|
|`EUTCase`|Case T-123/12|