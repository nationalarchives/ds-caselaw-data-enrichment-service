# The Abbreviation Annotator

## Overview

The Abbreviation Annotator is the third Annotator function in the JEP pipeline. It is preceded by the [Legislation Annotator](/docs/legislation/legislation-annotator.md) and followed the [Oblique Legislative References Annotator](/docs/legislation/oblique-references.md). The Abbreviation Annotator is deployed as a container function Lambda function. [!!!! name of lambda!]

The purpose of the Abbreviation Annotator is to detect the use of abbreviations and resolve the abbreviated shortform, such as `ECtHR`, to its corresponding longform, `European Court of Human Rights`. Abbreviation shortform are used extensively in judgments as a device to reduce wordcount and aid readability and are generally declared within double quotes inside parentheses following the first mention of the corresponding longform, like so:

> ... section 4 of the Human Rights Act 1998 ("HRA 1998") provides...

In the example above, the shortform is `HRA` and the longform is `Human Rights Act 1998`. 

## XML and attributes

The markup on abbreviations is straightforward. The Abbreviation Annotator wraps the shortform abbreviation, e.g. `FSA`, within `</abbr>` tags. The longform definition, e.g. `Food Standards Agency`, is captured as the value of the `title` attribute, like so:

```xml
<abbr title="Food Standards Agency">FSA</abbr>
```

## Implementation Details

The input to the Abbreviation Annotator is the raw text of the judgment body of the incoming judgment XML file to be enriched. The output is a list of replacements that is sent to the first phase enrichment [replacer](/docs/the-replacers.md).

The logic for the Abbreviation Annotator is contained in the [abbreviation extraction module](/abbreviation_extraction/). The JEP's implementation is an adaption of [Blackstone's abbreviation detector](https://github.com/ICLRandD/Blackstone/blob/master/blackstone/pipeline/abbreviations.py) which itself was an adaption of [ScispaCy's abbreviation detector](https://github.com/allenai/scispacy/blob/main/scispacy/abbreviation.py). The JEP's implementation has been updated for spaCy version 3.0+. 

The implementation is based on the abbreviation detection algorithm in ["A simple algorithm for identifying abbreviation definitions in biomedical text.", (Schwartz & Hearst, 2003)](https://pubmed.ncbi.nlm.nih.gov/12603049/). The algorithm works by enumerating the characters in the short form of the abbreviation (e.g. `ECtHR`), checking that they can be matched against characters in a candidate text for the long form in order (e.g. `European Court of Human Rights`), as well as requiring that the first letter of the abbreviated form matches the first letter of a word. 

The Schwartz & Hearst (2003) approach is remarkably effective at resolving abbreviations used in scientific texts. Some modifications to the algorithm's logic were necessary to render the approach suitable for legal texts. These modifications include:

* The short form abbreviation must be defined within quotes inside parentheses. `("PACE")` will be detected, `(PACE)` will not be detected. This significantly reduces the risks of false positives, such as where parentheticals are used in the titles of legislation.
* The short form must be at least three characters long

The Abbreviation Annotator is added as a pipeline component to the spaCy `nlp` model and abbreviations are made available by the resulting `Doc` object. To prevent memory errors when dealing with longer judgments, the Abbreviation Annotator divides the raw text of the judgment body into an arbitrary number of chunks that are sequentially fed to the model to reduce memory overhead at inference time. 

