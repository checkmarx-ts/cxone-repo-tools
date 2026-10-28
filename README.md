# Checkmarx One Repository Tools

This is a tool that is used for managing Code Repository import projects in
Checkmarx One.  Code repository import is used to establish a connection
between Checkmarx One and one or more SCMs to orchestrate scans.  Each connection
has an associated authentication method and stores the credentials to perform
the authentication with the SCM.

At a high level, this tool is used to:

* Batch change/add/remove project SCM connections.
* Batch management of private package repository configurations assigned to projects.

To install this tool, you will need Python 3.10 or greater.

## Quickstart

The `releases` section of this repo has a downloadable AI skill that can be used by your AI agent.  It can provide
assistance with the following:

* Installation of the tool.
* Analysis of the CSV exports to plan for tool execution.
* Commands that can be copy/pasted to execute the tool.

If you are trying to understand if this tool will help with a Checkmarx One maintenance scenario,
you can ask the AI skill or contact Checkmarx Professional Services for assistance.

### Manual Installation and Execution

The install is typically performed by using a direct URL with an optional associated hash for verification.  The `releases` section of this repo
has the required copy/paste lines with required hashes.

Once installed, the command line help can be accessed with the following command:

`cxone-repo-tools -h`

The command line help and the AI skill are the primary documentation for this tool.

  