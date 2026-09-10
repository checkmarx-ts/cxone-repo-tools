# Analysis

Analysis is performed on Checkmarx One projects connected to an SCM through Checkmarx One Code Repository import.
The user should be informed that projects that are for a manual scan are not part of the analysis.

These field names are to be considered synonyms:
- `scm_id`
- `SCM ID`
- `scmid`

These field names are to be considered synonyms:
- `repoid`
- `repo_id`
- `REPO ID`
- `Repo ID`

## Data Prerequisites

* The rendering of the analysis cases requires the output of `export-projects`.
* If the data provided does not contain all the required fields for analysis, it is not the output of `export-projects`.
* If the user has not provided the output required for the analysis requested, ask the user to provide it.

## Analysis 1: Pie Chart of Project Counts by SCM

Display a pie chart showing the count of projects connected to an SCM.

The pie chart must have the following properties:
* Each slice contains the count and percentage of projects assigned to the same `scm_id`.
* Each slice has a callout for the `scm_instance_name` corresponding to the slice's `scm_id`.

## Analysis 2: Multiple Pie Charts Showing Organization Membership

For each `SCM ID`, a pie chart is generated showing the distribution of projects
with the same value of `project_scm_org`.  Each SCM will have one or more organizations
containing code repositories that correspond to a Checkmarx One project.

Each pie chart must have the following properties:
* Each Pie Chart is titled with the `scm_instance_name`.
* Each pie slice contains the count and percentage of projects assigned to the same `project_scm_org`.
* Each slice has a callout for the `project_scm_org` corresponding to the `scm_instance_name`
  representing the pie chart.

If there are more than 4 pie charts to render, render a table for all chart data instead of any pie charts.

## Analysis 3: Project Configurations

Render a bar chart with the counts of projects where the values for the following fields
are `true`:

* `project_webhook_enabled`
* `project_pr_decoration_enabled`
* `project_sca_autopr_enabled`

When any of the preceeding fields are `false` for more than 10% of all projects provided
in the input data, the user should be warned of a possible misconfiguration for that
field exceeding the threshold.

## Analysis 4: Bar Chart of Enabled Scanners

The `project_scanners` field is a comma-separated list of scanner types enabled for the project. A
bar chart should be rendered showing the number of projects that reference each scanner.

## Analysis 5: Warnings

Warn the user of the counts of projects that have a configuration that may indicate
undiscovered risk:

* Projects that have `project_sca_autopr_enabled` set to `true` but do not have the `sca` engine
  listed in `project_scanners`.

* Projects that have `project_scanners` as an empty field but have `project_webhook_enabled` set to `true`.

* Projects that have `project_webhook_enabled` set to `true` but have `project_protected_branches` as an empty field.
