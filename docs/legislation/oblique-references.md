# Oblique Legislative References Annotator

## Overview

It is common in judgments for the judge to use the full short title of a piece of legislation (such as the `Theft Act 1968`) the first time it is referred to and then to refer to the same legislation obliquely (such as `the Act` of the `1968 Act`) in subsequent references elsewhere in the judgment. This challenge this presents is that it makes it difficult to determine which Act is being cited (so that, for example, the oblique reference can be linked to the corresponding instrument on `legislation.gov.uk`). The Oblique Legislative References Annotator (OLRA) is designed to address this challenge.

The OLRA is the fourth annotator in the JEP and kicks into action in the second [phase of enrichment](/docs/README.md#13-enrichment-phases) (the [Case Law Annotator](/docs/caselaw/case-law-annotator.md); the [Legisalation Annotator](/docs/legislation/legislation-annotator.md); and the [Abbreviations Annotator](/docs/abbreviation-annotator.md)). 

## XML and attributes

```xml
<ref href="http://www.legislation.gov.uk/id/ukpga/1972/68" uk:canonical="1972 c. 68" uk:type="legislation">this Act</ref>
```

## Implementation details

1. The OLRA uses the previously phase two enriched judgment as input and identifies where there are legislation `</ref>` tags in the judgment body.
2. The annotator then searches for oblique reference patterns, such as `T(t)he/T(t)his/T(t)hat Act` and `T(t)he/T(t)his/T(t)hat [dddd] Act` references in the judgment text.
3. Where the matched oblique reference does not contain a year, the OLRA uses the location of the oblique reference and the legislation reference to determine which citation to legislation the oblique reference is closest to, and then links to that legislation.
4. Where the matched oblique reference contains a year, the OLRA searches  for the matched legislation reference (identified in step 1 above) that corresponds to that year and then links to that legislation.
1. OLRA then builds builds a replacement string that wraps the detected oblique reference into a <ref> element with the link and canonical form of the linked legislation as attributes. 

The pipeline returns a dictionary containing the detected oblique reference, its position and the replacement string.
