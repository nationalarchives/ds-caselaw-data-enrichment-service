== v6.0.0 ==
Fix case where `replace_references_by_paragraph` was treating XML as HTML (symptom: forced lower case tags

== v5.0.0 ==
Create `create_tag` and `create_tag_string` to make more compliant XML, to try to resolve escaping issues.
Escape some strings coming from the replacement lists on output

== v4.0.0 ==
Fix a bug which was mangling judgment text in particular scenarios when inserting references.

== v3.0.0 ==
Change the version back to semver to not violate our schema.

== v2 ==
Update Terraform to filter only trigger_enrichment messages.
Enrichment lambdas do not attempt to filter based on body JSON.

== v1 ==
Ensure "No Year" does not appear in <ref> tags to avoid validation errors.

== v0.1.0 ==
Before December 2023, versions were not tracked and the version string was "0.1.0"
