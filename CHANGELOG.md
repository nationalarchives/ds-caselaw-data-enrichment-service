# Changelog

## v7.0.1 (2025-05-19)

- Fix replace_string_with_tag for when the xml fragment string includes uk namespace attributes

## v7.0.0 (2024-11-28)

- Ensure that documents with matching replacements don't replace inside XML strings
- Fix type linting

## v6.0.2 (2024-10-03)

- Enrich press summaries by fixing patch url to be press-summary, not press/summary

## v6.0.1 (2024-07-16)

- Fix CI by reflecting changed output from legislation SPARQL output

### Refactor

- **FCL-176**: explicitly set timezones to UTC
- **FCL-176**: automated fixes for "C4" rules (includes unsafe)
- **FCL-176**: automated fixes for "COM" rules
- **FCL-176**: replace instances of shadowing Python builtins
- **FCL-176**: use bound parameters to pass rule ID
- **FCL-176**: replace runtime assert with exception
- **FCL-176**: add timeout when patching a judgment
- **FCL-176**: disable S105 and S106 for known-safe lines
- **FCL-176**: Move update_legislation_table tests
- **FCL-176**: Manual f-string fix for multi-line string
- **FCL-176**: Automated fixes for "UP" rules
- **FCL-176**: Automated fixes for "I" rules
- **FCL-176**: Solve cases of control variables not being used
- **FCL-176**: Refactor some Exception handling
- **FCL-176**: Automated fixes for "B" rules
- **FCL-176**: modify return type of get_matched_rule
- **FCL-176**: replace equality operators for True/False/None comparisons

## v6.0.0

Fix case where `replace_references_by_paragraph` was treating XML as HTML (symptom: forced lower case tags

## v5.0.0

Create `create_tag` and `create_tag_string` to make more compliant XML, to try to resolve escaping issues.
Escape some strings coming from the replacement lists on output

## v4.0.0 (2023-12-12)

Fix a bug which was mangling judgment text in particular scenarios when inserting references.

## v3.0.0 (2023-12-06)

Change the version back to semver to not violate our schema.

## v2

Update Terraform to filter only trigger_enrichment messages.
Enrichment lambdas do not attempt to filter based on body JSON.

## v1

Ensure "No Year" does not appear in <ref> tags to avoid validation errors.

## v0.1.0

Before December 2023, versions were not tracked and the version string was "0.1.0"
