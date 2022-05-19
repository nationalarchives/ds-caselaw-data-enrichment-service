# The Case Law Annotator

## Overview
The purpose of the Case Law Annotator is to detect and markup citations to UK case law cited in the judgment being processed. The Case Law Annotator uses a rules-based engine, the *Rules Manifest*, built on the [spaCy EntityRuler](https://spacy.io/api/entityruler) to achieve this. 

The *Rules Manifest* provides the following core functionality:

1. Detects references to both well-formed (canonical) citations and malformed citations
2. In the case of detected malformed citations, casts the malformed citation to the canonical form
3. Marks up the detected references in the LegalDocML.

The *Rules Manifest* is stored in *X* table of the Postgres database (***Need location***) where each row represents a rule. 

## Detection of Canonical and Malformed Citations
The accuracy with which case law citations are used in judgments is variable. Some citations are perfect: they follow the *canonical form*. For example, the correct, or canonical, way to cite a case reported in *The Weekly Law Reports* is like so: `[year] vol WLR page`or `[2022] 1 WLR 123`. The square brackets are present and the right way round. The volume number has been included. There are no fullstops interspersed through the series abbreviation. 

Sometimes citations are less than perfect: they do not follow the *canonical form* and are *malformed*. For example, whilst there is only one way to correctly cite a case reported in *The Weekly Law Reports* there are many wrong ways. One incorrect way might be to incorrectly specify the series abbreviation, such as `[2022] 1 Weekly LR 123`. 

The Case Law Annotator has been designed to detect both canonical and malformed variations of the case law citations most often found in judgments given in English and Welsh, and UK courts. It does so by using rules (contained in the *Rules Manifest*) to specify which citation patterns to match against and whether those patterns match the canonical form of a citation or not. For example, there is a rule that matches the canonical form of a citation to a case reported in *The Weekly Law Reports*. That rule's `id` is `wlr`. 

```csv
id,family,description,uri_template,canonical_form,canonical_example,match_example,citation_type,is_canonical,is_neutral,jurisdiction,pattern
wlr,WLR,The Weekly Law Reports (ICLR),,[dddd] d1 WLR d2,[2022] 1 WLR 123,[2022] 1 WLR 123,PubYearNumAbbrNum,TRUE,FALSE,EW,"{""id"": ""wlr"", ""description"": ""The Weekly Law Reports (ICLR)"", ""label"": ""CITATION"", ""pattern"": [{""ORTH"": ""[""}, {""SHAPE"": ""dddd""}, {""ORTH"": ""]""}, {""LIKE_NUM"": true}, {""ORTH"": ""WLR""},{""LIKE_NUM"": true}]}"
```
It is quite common to see citations to cases reported in *The Weekly Law Reports* sprinkled with fullstops in the abbreviation section so that they look like this: `[2022] 1 W.L.R. 123`. Such a reference is regarded by the Case Law Annotator as *malformed*. The *Rules Manifest* has a rule to detect this malformed variant. That rule's `id` is `wlr_a`. 

```csv
id,family,description,uri_template,canonical_form,canonical_example,match_example,citation_type,is_canonical,is_neutral,jurisdiction,pattern
wlr_a,WLR,The Weekly Law Reports (ICLR),,[dddd] d1 WLR d2,[2022] 1 WLR 123,[2022] 1 W.L.R. 123,PubYearNumAbbrNum,FALSE,FALSE,EW,"{""id"": ""wlr_a"", ""description"": ""The Weekly Law Reports (ICLR)"", ""label"": ""CITATION"", ""pattern"": [{""ORTH"": ""[""}, {""SHAPE"": ""dddd""}, {""ORTH"": ""]""}, {""LIKE_NUM"": true}, {""ORTH"": ""W.L.R.""},{""LIKE_NUM"": true}]}"
```
### All look at some of the attributes of a rule

The structure of the rules is comprehensively outlined below. However, it is worth highlighting certain features of the rules above before continuing. 

#### `family`
The first feature is the `family`, which is `WLR` in the case of the two rules set out above. There is a `family` of rules that cater for references to cases reported in *The Weekly Law Reports* and many other series of law reports.  

A `family` must have one and only one rule that matches the canonical form. That is to say, a `family` must have one and only rule for which the `is_canonical` attribute  is `TRUE`. 

#### `id`
Each rule requires its own unique `id`. This identifier is used at inference time to access various information about the citation and the rule that detected it. Notice that the `id` in the first snippet, which matches the canonical form, is simply `wlr`. The `id` for the second snippet is `wlr_a`.  A convention of the *Rules Manifest* is that the `id` for rules that match malformed variants should use the `id` for the canonical rule  with an `_a`, `_b`, `_c` etc appended to the end.

#### `is_canonical`
Each rule must specify whether the pattern matches the canonical form or a malformed variant of the target citation by setting `is_canonical` to `TRUE` or `FALSE`. This flag tells the Case Law Annotator whether or not it needs to run a *Correction Strategy* to case the malformed reference to the canonical form. 

#### `canonical_form`
Every rule, regardless of whether it matches a canonical citation or a malformed variant, contains the `canonical_form` of the matched reference. The `canonical` form acts as a sort of template that the Case Law Annotator uses to cast malformed citations to their rightful canonical form. The `canonical_form` will be the same across the entire `family` of citations. 

For example, the `canonical_form` for the `family` of rules dealing with references to *The Weekly Law Reports*, `WLR`, is as follows:
`[dddd] d1 WLR d2` 

#### `pattern`
The `pattern` attribute stores the actual spaCy [matcher](https://spacy.io/api/matcher) pattern responsible for detecting the citation. The pattern to match the canonical form of citations in *The Weekly Law Reports* is as follows:

```json
"{""id"": ""wlr"", ""description"": ""The Weekly Law Reports (ICLR)"", ""label"": ""CITATION"", ""pattern"": [{""ORTH"": ""[""}, {""SHAPE"": ""dddd""}, {""ORTH"": ""]""}, {""LIKE_NUM"": true}, {""ORTH"": ""WLR""},{""LIKE_NUM"": true}]}"
```
The patterns work at the token level in a manner similar to a very verbose regular expression. Whenever the *Rules Manifest* [is updated](updating-the-rules.md) the patterns are written to a newline JSON file, `filename.json`, which is then consumed by the NLP pipeline at inference time.  

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

For more information on the structure of the patterns, see the [guide on writing rule patterns](how-to-write-rule-patterns.md).


## Rules Manifest

### Canonical and Malformed Citations

The concept of **canonical** and **malformed** citations is central to the design of the Case Law Annotator and the rules-base that it is powered by. 

#### Canonical citations
Canonical citations are citations that exactly follow the correct form of the given citation. A canonical citation will not:
* Introduce unnecessary matter into the citation, such as punctuation marks, 
* Introduce erroneous matter, such as an incorrect series abbreviation (e.g. `Weekly LR` instead of `WLR`)
* Omit necessary matter, such as the volume number, if a volume number is required (e.g. `[2022] WLR 456` instead of `[2022] 1 WLR 456`

:warning: There should be one and only one canonical rule for a given citation family. 
#### Malformed citations
Malformed citations are the opposite of canonical citations. They are citations that contain some error or unnecessary material. 






  

### Rule Attributes

  

| Attribute | Required or Optional | Detail |
|-----------|----------------------|--------|
|id|Required|Each rule requires a unique `id`. <br> <br> By convention, the `id` for the canonical form of a given rule follows the abbreviation used by the case law citation the rule matches against. For example, the `id` for the rule that matches _The Weekly Law Reports_ is `wlr`. <br> <br> |
|family|Required|sdssfsd |
|description|Required|ssdsds|
|uri_template|Optional|adsdsd|
|canonical_form|Required|adsdsds|
|canonical_example|Required|adsfdsfd|
|match_example|Required|sfsfdfdfd|
|citation_type|Required|sffdfdf|
|is_neutral|Required|ddfdfdfd|
|jurisdiction|Required|sfdsfdf|
|pattern|Required|sdsffdfd|

### Creating a match pattern
 