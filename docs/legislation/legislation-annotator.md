# The Legislation Annotator

## Overview
The Legislation Annotator is the second *Annotator* function in the pipeline. It follows the [Case Law Annotator](/docs/caselaw/case-law-annotator.md) and is itself followed by the [Abbreviation Annotator](/docs/abbreviation-annotator.md). 

The purpose of the Legislation Annotator is to detect and markup references to UK primary legislation cited in the judgment being processed and uses a hybrid of deterministic and probabilistic strategies to achieve this.

## XML and attributes

The primary purpose of the Legislation Annotator is to apply LegalDocML markup to references to primary legislation present in the judgment. 

The following snippet provides an example of an enriched reference to an Act of Parliament, in this case the Companies Act 2006.

```xml
<ref href="http://www.legislation.gov.uk/id/ukpga/2006/46/" uk:canonical="2006 c. 46" uk:type="legislation">Companies Act 2006</ref>
```
References to primary legislation are enclosed in `</ref>` tags with the following three attributes:

* `href`: the TNA URI for the detected piece of primary legislation 
* `uk:canonical`: the citation, composed of the year and chapter number assigned to the detected piece of primary legislation
* `uk:type`: the reference type, which unsurprisingly for legislation is always set to `legislation`
  
## Implementation details

The input to the Legislation Annotator is the raw text of the judgment body of the incoming judgment XML file to be enriched. The output is a list of replacements and associated metadata that is sent to the first phase enrichment [replacer](/docs/the-replacers.md).

The Legislation Annotator detects references to UK primary legislation by searching through a lookup table of existing Acts stored in Postgres. The lookup table is updated on an automated basis every seven days by a [utility function](/lambda/update_legislation_table/) that queries the [legislation.gov.uk](https://legislation.gov.uk) SPARQL endpoint for new UK Public General Acts. New Acts are written to the Postgres database so that they are available for matching.

The Legislation Annotator uses a hybrid strategy that combines exact string matching and fuzzy matching. This combination of exact and fuzzy matching enables the Legislation Annotator to trivially detect well-formed references to legislation, whilst the fuzzy matcher extends detection to malformed variants, such as those with minor differences in spelling, that exceed a given threshold of similarity. 

The Legislation Annotator's logic follows three stages. First, the Legislation Annotator narrows down the search space to candidate spans in the judgment text that contain the pattern `Act YYYY`. 

A fuzzy matcher is then applied against the legislation in the lookup table to identify matches exceeding a set threshold of similarity, which is controlled by modifying the `CUTOFF` value in [legislation_matcher_hybrid.py](/legislation_extraction/legislation_matcher_hybrid.py). `CUTOFF` is a value between `0-100`. The lower the `CUTOFF`, the fuzzier the matcher. The JEP uses a third-party library called [spaczz](https://github.com/gandersen101/spaczz) to provide this functionality

The second stage runs the exact matcher against legislation entries in the lookup table that do not conform to the `Act YYYY` pattern, e.g. `RCRA 1926`. 

The final stage completes the detection process by (i) merging the results of the first and second stages; (ii) resolving detected references that might overlap due the nature of the fuzzy matching to a [1-to-1] linking between legislation short titles and the detected reference; and (iii) createing replacement tuples for the detected references which are passed over to the first enrichment [replacer](/docs/the-replacers.md).





