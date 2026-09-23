# Usage Clarification

* The project id of manual projects can be obtained from the Checkmarx One UI.
* Batch size of projects to convert is set at a maximum of 15 projects.  The
  user does not have the ability to control the batch size.
* The `--ignore-url-mismatch` option is used to ignore the mismatch error when converting
  SCMs and the URL matching check fails.  This option is used to ignore differences
  in SCM base-urls such as found in the following examples:
  * `https://scm.mycompany.com` vs. `https://someuser@scm.mycompany.com` indicates the conversion
    is for authentication to the same SCM but the base URL is not exactly the same.
  * `https://some_other_user@scm.mycompany.com` vs. `https://someuser@scm.mycompany.com`


## Conversion Recovery

* Recovery is automatic on each execution with the `convert-scms` option and when one or more recovery
  files are found in the current working directory.
  * The `--recovery-only` option means that the program ends after recovery is completed.
  * The `--skip-recovery` option means that the program will not attempt to perform recovery but will
    not remove the recovery files.
* A completed recovery only indicates an attempt to complete conversions of the projects found
  in the recovery file.
    * Zero or more projects found in the recovery file may be successfully converted
      as part of the recovery attempt.
    * Zero or more projects found in the recovery file may fail to convert
      as part of the recovery attempt.
* Recovery files are not removed until all projects in the recovery files have been successfully
  converted.

## Connections

* The number of API calls to Checkmarx One is higher than normal due to the amount
  of data points needed to perform a batch conversion.
* The `--cxone-region` option is used for multi-tenant Checkmarx One connections.
* The `--cxone-hostname` option is used for single-tenant Checkmarx One connections.
* The `--retries` option is set to a high value to avoid missing data
  when the Checkmarx One API responses are delayed due to a higher than normal
  number of requests.
* In addition to delays, the Checkmarx One infrastructure may scale to handle the
  higher volume of requests.  This may cause a temporary series of 5XX responses.
  