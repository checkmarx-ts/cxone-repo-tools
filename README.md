# Checkmarx One Repository Tools

This is a tool that is used for managing Code Repository import projects in
Checkmarx One.  Code repository import is used to establish a connection
between Checkmarx One and one or more SCMs to orchestrate scans.  Each connection
has an associated authentication method and stores the credentials to perform
the authentication with the SCM.

At a high level, this tool does the following:

* Dumps a list of SCM connection definitions to a CSV.
* Dumps a list of projects with associated SCM connections to a CSV.
* Changes the SCM connection for one or all projects to another SCM of the same type.
* Disconnect the SCM connection for one or all projects connected to a specific SCM.
* Connects one project not currently associated to and SCM to an SCM.

To install this tool, you will need Python 3.10 or greater.

## Quickstart

Once installed (see below), the command line help can be accessed with the following command:

`cxone-repo-tools -h`

This `README` covers the tool topics at a high level.  The command line help and the AI skill are
the primary documentation.

### AI Skill

The `releases` section of this repo has a downloadable AI skill that can be used by your AI agent.  It can provide
assistance with the following:

* Installation of the tool.
* Analysis of the CSV exports to plan for tool execution.
* Execution of the tool.

### Installation

The install is typically performed by using a direct URL with an optional associated hash for verification.  The `releases` section of this repo
has the required copy/paste lines with required hashes.

## Background

The primary use for this tool is to migrate the SCM connection definition of multiple projects to a different SCM connection definition.

The connection to each SCM is identified by an `SCM ID`.  The `SCM ID` is used by Checkmarx One to understand the authentication
method and store authentication credentials, among other data, that allows code to be retrieved from the SCM for scanning.

A project that is a Code Repository import project has a Git repository in an SCM. Each Code Repository import project has an
associated `REPO ID` that identifies, among other data items, the `SCM ID` where the repository is located.  A scan can be invoked
from the Checkmarx One UI or on receipt of a webhook event without the need to provide credentials needed to obtain the code
from the SCM.

## Limitations

* This tool currently does not work with Cloud-hosted SCMs in Checkmarx One multi-tenant tenants.  The Checkmarx One
  APIs do not allow conversions for Multi-tenant Cloud SCM configurations.
* If converting projects to an SCM that uses a Github App, it is a good idea to ensure the Github App is installed for
  all organizations containing conversion repositories.
* If the Github App is not installed in an organization, you can execute recovery after installing the Github App
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
  the batch of projects are completely converted.
* To retry projects that failed conversion if the projects need manual configuration before the
  conversion is successful.

## Other Notes

* Authentication is performed using an API key.  It is suggested that the user that creates the API key has
  administrative rights in Checkmarx One.

* There is a destructive step in the conversion process that will disconnect a project from a repository
  before the project is re-connected to a new repository.  This means no scans will be orchestrated by Checkmarx One
  for that project until the project is re-connected to an SCM.

* If the program is interrupted before a project is converted fully, the recovery process should finish the conversion.

* If a project is disconnected and there is no recovery file, it can be manually re-connected by providing required
  additional parameters.
  