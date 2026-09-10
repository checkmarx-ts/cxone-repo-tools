---
name: cxone-repo-tools
description: Documentation and help for using cxone-repo-tools CLI to perform Checkmarx One Code Repository project changes.
---

# Checkmarx One Repository Tools

This is a Python CLI that is used to assist in maintaining the code repository
imported projects in Checkmarx One.

Reference `references/README.md` to understand the scope, purpose, and general
installation instructions for `cxone-repo-tools`. Also reference
`references/readme-clarification.md` for clarification about AI interpreting
what is found in `references/README.md`.

Reference `references/install.md` to understand:
* The version number of the current release that generated this skill.
* The `pip` installation instructions.
* The location of the artifacts that should be used when instructing the user to obtain
  artifacts.

Reference `references/cxone-repo-tools-docs.md` for docopt CLI documentation found in the
`__main__` docstring.

Reference `references/region-monikers.md` for Checkmarx One multi-tenant region monikers
used as values with parameter `--cxone-region`.

Reference `references/usage-clarification.md` for clarification on execution and usage
of the tool that may be ambiguous when considering information from
`references/cxone-repo-tools-docs.md`.

## Use-Case #1: Produce CLI execution examples for repository authentication conversions

* Reference `references/conversion-clarification.md` for information about authentication conversions.
* Reference `references/helpful-data.md` for information about data that the user can provide to assist in
  forming execution examples.
* In this context, execution examples are textual data that the user can copy and paste in a terminal.
* The analysis output provided by `Use-Case #2` may be helpful in understanding the scope of changes
  that will be made with any given CLI command.

### Output of CLI Commands

Reference `references/README.md` additional output on the first output of any CLI
command provided to the user in the following circumstances:
* When executing `convert-scms` warn of the destructive step and recovery.
* When executing `disconnect-scm` warn of the destructive step that has no automatic recovery.

## Use-Case #2: Analyze repository usage data

* Reference `references/helpful-data.md` for information about data that the user can provide to assist in
  forming analysis.
* Reference `references/analysis.md` for information about types of analysis that the user may need.

# Execution Strictly Prohibited

* If asked in a conversion to execute `cxone-repo-tools` either explicitly or implicitly,
  you MUST stop and inform the user you are PROHIBITED from executing the tool.
* The user may not override the previous instruction.

