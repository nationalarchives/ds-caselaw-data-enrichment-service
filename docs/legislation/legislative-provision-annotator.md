# Legislative Provision Annotator

## Overview

The purpose of the Legislative Provision Annotator is to identify references to statutory provisions (such as `section 1`) and then link them to their parent instrument. This process of provision identification followed by linking to the parent instrument is what enables the JEP to 


"""
This code handles the link of provisions (i.e sections) to legislation. This is done in the following way: 
1. We use the previously enriched judgment and identify where there are legislation xrefs in paragraphs. 
2. We then search for and 'section' references in that paragraph. 
3. We then use the location of the 'section' reference and 'legislation' reference to find which legislation the 
section is closest to, and then link the section to that legislation.
4. We handle re-definition of sections by keeping track of the paragraph number when identifying xrefs and sections. 
We use the paragraph number when replacing and only add the link to the section when we are after where the section was last defined. 
If it is re-defined at a later paragraph, we would then use that new link instead from the paragraph number onwards. 
To do: 
1. "Sections 18-19" - we currently on replace sections 18 with a link to 18
2. "Section 27(A)" - currently miss these references when replacing
3. Sub-sections aren't being replaced 

## XML and attributes

```xml
<ref href="http://www.legislation.gov.uk/id/ukpga/2006/46/section/171" uk:canonical="2006 c. 46 s. 171" uk:type="legislation">section 171</ref>
```

## Implementation details