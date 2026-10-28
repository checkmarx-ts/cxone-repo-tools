# Repository Authentication Conversions

* Checkmarx One establishes a connection to a source code management (SCM) 
  system when the user configures the connection via Code Repository Import.
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
* When executing `convert-scms` warn of the destructive step and recovery.
* When executing `disconnect-scm` warn of the destructive step that has no automatic recovery.


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
  2. Identify the single `target` SCM ID that is to be used as the authentication method
     for all specified `source` SCM IDs.
  3. Iterate through the Checkmarx One `projects` assigned to the specified `source` SCMs to
     disconnect the SCM that is currently used for authentication.
     * This turns the project into a `manual` project.
  4. Import the project via the conversion API to connect the `target` SCM as the
     authentication method for the project.

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

## Filtering Selected Projects

* The `--project-id` flag can be used to limit conversion to a single project.  This is not
  the most efficient method of conversion but can be used to control conversion logic implemented
  in custom shell scripts.
* There are filters using regular expressions to control which projects are selected during a batch
  conversion:
  * The `--regex-ignore-case` parameter, if included, forces regular expression matching with case-insensitivity.
  * The `--project-name-match` parameter takes a regular expression that is applied to find matching project
    names.  Any project names matching the regular expression are converted.
  * The `--project-group-match` parameter takes a regular expression that is applied to find matching
    project group paths in groups to which a project is assigned.  If at least one assigned group's path
    is matched, the project is converted.


## Background

The purpose of SCM connection management tools is to migrate the SCM connection definition of multiple Checkmarx One projects
to a different SCM connection definition.

The connection to each SCM is identified by an `SCM ID`.  The `SCM ID` is used by Checkmarx One to understand the authentication
method and store authentication credentials, among other data, that allows code to be retrieved from the SCM for scanning.

A project that is a Code Repository import project has a Git repository in an SCM. Each Code Repository import project has an
associated `REPO ID` that identifies, among other data items, the `SCM ID` where the repository is located.  A scan can be invoked
from the Checkmarx One UI or on receipt of a webhook event without the need to provide credentials needed to obtain the code
from the SCM.

## Limitations

* This tool currently does not work with Cloud-hosted SCMs in Checkmarx One multi-tenant systems.  The Checkmarx One
  APIs do not allow conversions for Multi-tenant Cloud SCM configurations.
* If converting projects to an SCM that uses a GitHub App, it is a good idea to ensure the Github App is installed for
  all organizations containing conversion repositories.
* If the GitHub App is not installed in an organization, you can execute recovery after installing the Github App
  in the organization.  You may need to wait several minutes before starting the recovery to allow Checkmarx One
  to re-authenticate with the target organization.

## Execution Workflow

Changing the SCM connection for all projects connected to an SCM starts with obtaining one or more `source` `SCM IDs`
and a single `target` `SCM ID`.  The CSV output options can be used to obtain lists of data that will assist in
obtaining the required `SCM IDs`.

The conversion can execute multiple times and will perform conversion on any projects found connected to any `source` SCM
and convert them to the `target` SCM.

It is suggested to pick a single work directory for executing the tool as `*.recovery.json` files are written during the
conversion process.  These recovery files are loaded on start of the tool and executed before any processing of new
repositories.  When all projects in a recovery file are converted, the recovery file is deleted.

The recovery files have the following purpose:

* To resume the conversion of a batch of projects in the event the program stops executing before 
  a project batch is completely converted.
* To retry projects that failed conversion if the projects need manual configuration before the
  conversion is successful.

**If there is a failure, preserve the recovery files so that disconnected repositories can be reconnected
manually if the recovery doesn't do it automatically.  Contact Checkmarx Professional Services for assistance
if recovery is not performed automatically.**

## Other Notes

* Authentication is performed using either an API key or OAuth client credentials.  It is suggested that the
  user that creates the API key, or the OAuth client, has
  administrative rights in Checkmarx One.  The API key or OAuth client secret can be provided on the command
  line or read from the environment variables CX_API_KEY or CX_CLIENT_SECRET.

* There is a destructive step in the conversion process that will disconnect a project from a repository
  before the project is re-connected to a new repository.  This means no scans will be orchestrated by Checkmarx One
  for that project until the project is re-connected to an SCM.

* If the program is interrupted before a project is converted fully, the recovery process should
  finish the conversion on the next run.

* Recovery failures can happen when repositories are misconfigured or have been renamed and the stored repository
  URL is no longer valid.  The recovery file can be modified to perform the import for the correct repository URL.

* If a project is disconnected and there is no recovery file, it can be manually re-connected by providing required
  additional parameters.
