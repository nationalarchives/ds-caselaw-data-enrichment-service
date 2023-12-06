== v3.0.0 ==
Change the version back to semver to not violate our schema.

== v2 ==
Update Terraform to filter only trigger_enrichment messages.
Enrichment lambdas do not attempt to filter based on body JSON.

== v1 ==
Ensure "No Year" does not appear in <ref> tags to avoid validation errors.

== v0.1.0 ==
Before December 2023, versions were not tracked and the version string was "0.1.0"
