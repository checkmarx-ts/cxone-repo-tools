# Helpful Data

The CSV exports provided by the tool can be referenced to assist in producing CLI examples.

## `export-scms` data

The `export-scms` option will export the SCM definition with the important fields:

* `scm_id`: The `SCM ID` used as a `source` or `target` SCM for operations requiring an `SCM ID`.
* `scm_instance_name`: A human-readable reference to the SCM connection identified by the `SCM ID`.

Explanation of the execution should include the human-readable name of the SCM connection.

## `export-projects` data

The `export-projects` option will export the project definitions for Code Repository projects
(no manual projects will be included) with the important fields:

* All fields supplied by `export-scms` including the mentioned important fields.

* `project_id`: The identifier of the Checkmarx One project that may be provided as an option to some
  CLI execution scenarios.
* `project_name`: The human-readable reference to the project, preferable to the `project_id` for display
  purposes.
* `project_scm_org`: The name of the organization in the SCM where the code repository can be located.
* `project_repo_url`: The SCM URL for the project code, mainly used for reference purposes if
  the user needs to find the code associated with the project.

### Additional fields in `export-projects` data

* `project_webhook_enabled`: A boolean value indicating webhook events will be processed for the project.
* `project_pr_decoration_enabled`: A boolean value indicating that the pull-request webhook events will
  post a scan summary in the pull-request comments.
* `project_sca_autopr_enabled`: A boolean value indicating that SCA dependency scans will automatically
  open a pull-request to update dependencies when an SCA scan finds reason to update dependencies.
* `project_scanners`: A comma-separated list of strings indicating the scan engines set to be used
  for a scan by default.
* `project_protected_branches`: A comma-separated list of strings representing branches that are typically
  important enough to have limited access to commit changes.  These are typically for branches where
  released code can be found.  Scans are orchestrated via webhook events involving these branches.
