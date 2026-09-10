# Repository Authentication Conversions

* Checkmarx One establishes a connection to a source control system (SCM)
  when the user configures the connection via Code Repository Import.
* The connection is referenced internally by Checkmarx One with an SCM ID (e.g.
  `scmid` or `scm_id` data element label)
* Each SCM has a `type` that indicates the SCM type.
* Once connected, zero or more repositories found in the SCM can be "imported"
  into Checkmarx One as a `project`.
* Each Checkmarx One `project` has an associated Repo ID (e.g. `repoid` or
  `repo_id` data element label) which is associated with the `SCM ID`.
* A Checkmarx One `project` without a Repo ID is not connected to an SCM.
* The credentials for connecting to repositories found in the SCM are stored
  as part of the SCM data identified by the SCM ID.
* Checkmarx One will utilize the stored credentials for repository operations
  such as cloning and updating `pull-request` comments or status.
* The stored credentials are not retrievable for use outside of internal Checkmarx
  One operations.

## Projects Connected to an SCM

* Checkmarx One `projects` are connected to an SCM for the following reasons:
  * To enable scanning on SCM repository `push` and `pull-request` events.
  * To allow a scan to be started via Checkmarx One without the need to provide
    SCM credentials.
  * Automate feedback workflows such as:
    * Status and comments for `pull-requests`
    * Opening `pull-request` for proposed code changes that fix vulnerabilities
      found in a scan.
* Projects connected to an SCM are considered `imported` projects.
* Projects not connected to an SCM are considered `manual` projects and must manually
  be provided the source code to scan.
* Manual projects can be connected to an SCM using a conversion API.


## Conversion Process

* The conversion process involves the need to perform the following steps in this order:
  1. Identify the `source` SCM IDs and SCM types that will be converted.  More than one SCM
     may be a source.
  2. Identify the single `target` SCM ID that is to be used for as the authentication method
     for all specified `source` SCM IDs.
  3. Iterate through the Checkmarx One `projects` assigned to the specified `source` SCMs to
     disconnect the SCM that is currently used for authentication.
     * This turns the project into a `manual` project.
  4. Import the project by via the conversion API to connect the `target` SCM as the
     authentication method for the project.

* The concept of "one or all projects" for conversion means:
  * Parameters to the conversion can specify a single project id for conversion.  In this case, only one project will be converted.
  * If a single project is not specified in the conversion parameters, all projects from `source` `SCM IDs` will be converted
    to use the `target` `SCM ID`.

## Conversion Timing

The time it takes to perform the complete conversion will depend on the number of projects
in scope for conversion.  The more projects there are to convert, the more time it will take
to fully perform the conversion.

## Compatible Conversions

* The `source` SCM IDs cannot include the `target` SCM ID.
* Conversions between `source` and `target` SCM IDs can only be done when all SCMs
  are of the same `type`.
* The SCM type `github` and `githubApp` are considered the same SCM `type`.
* SCMs with differing types are currently not compatible for conversion due to the
  need to map repository URLs to different SCM organization concepts.
