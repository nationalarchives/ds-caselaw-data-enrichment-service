# Legislative Provision Annotator

## Overview

The purpose of the Legislative Provision Annotator is to identify references to statutory provisions (such as `section 1`) and then link them to their parent instrument (such as the `Theft Act 1968`). The Legislative Provision Annotator is the final annotator in the enrichment sequence and runs in the final phase of enrichment. This process of provision identification followed by linking to the parent instrument is what enables the JEP to enrich a reference to a statutory provision with a link to its location in the parent instrument, even when the reference to the parent instrument itself is "distant" from the provision reference.

## XML and attributes

```xml
<ref href="http://www.legislation.gov.uk/id/ukpga/2006/46/section/171" uk:canonical="2006 c. 46 s. 171" uk:type="legislation">section 171</ref>
```

## Implementation details

The implementation for Legislative Provision Annotator can be found [here](/legislation_provisions_extraction/). Provision linking is handled in the following way:

1. The Legislative Provision Annotator (LPA) uses the previously enriched judgment (which has already passed through the [Legislation Annotator](/docs/legislation/legislation-annotator.md)) to identify where there are references to legislation in the paragraphs judgment.
1. Once paragraphs containing references to legislation have been identified, the LAP search for 'section' references in those paragraphs.
1. The LAP thens use the location of the 'section' references and 'legislation' reference to find which legislation the section is closest to, and then links the section to that legislation.
1. We handle re-definition of sections by keeping track of the paragraph number when identifying xrefs and sections.
   We use the paragraph number when replacing and only add the link to the section when our current locations in the judgment is later than where the section was last defined. If it is re-defined at a later paragraph, we would then use that new link instead from the paragraph number onwards.

## Currently out of scope

To do:

1. "Sections 18-19" - we currently on replace sections 18 with a link to 18
1. "Section 27(A)" - currently miss these references when replacing
1. Sub-sections aren't being replaced
