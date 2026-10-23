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


## Composing CLI Invocations

The CLI is a single executable with global options followed by exactly one command.  The
command is followed by options that belong only to that command.  Each part is documented
in a different section of `cxone-repo-tools-docs.md`:

| Position | Content | Documented in |
|---|---|---|
| 1 | Connection options (tenant, endpoint, credentials) | `cxone_repo_tools.__main__` |
| 2 | Operation options (threads, retries, `-k`, proxy) | `cxone_repo_tools.__main__` |
| 3 | The command name | `Available Commands` in `cxone_repo_tools.__main__` |
| 4 | The command's own options | The `<Name>Command` class whose usage line starts with `cxone-repo-tools <command>` |

Rules:

* **Ordering is strict.** All global options MUST appear before the command name.  Parsing stops
  reading global options at the first word that is not an option, and that word is taken as the
  command.  Everything after the command is passed to the command.  Placing the command first, or
  placing a global option after the command, causes an `Incorrect arguments provided` error.
* The usage lines in a command's section begin with `cxone-repo-tools <command>` for readability
  only.  When producing an example, the global options from the `__main__` section are inserted
  between `cxone-repo-tools` and `<command>`.
* A global option is never repeated after the command, and a command option is never placed
  before the command.
* Exactly one of the credential groups is used: an API key (`--api-key` or `--api-key-env`) or an
  OAuth client (`--client-id` with `--client-secret` or `--client-secret-env`).  Prefer the
  environment variable forms in examples so secrets do not appear in shell history.
* Exactly one endpoint option is used: `--cxone-region` for multi-tenant or `--cxone-hostname` for
  single-tenant.
* When a command's usage shows several alternative usage lines, pick the one line that matches
  the user's intent and supply only the options from that line.

Composition example for disconnecting all projects from SCM ID `12` in a multi-tenant region:

```
cxone-repo-tools --tenant mytenant --cxone-region US --api-key-env disconnect-scm --scm-id 12
```

* `--tenant mytenant --cxone-region US --api-key-env` comes from the `__main__` section.
* `disconnect-scm` comes from `Available Commands`.
* `--scm-id 12` comes from the `DisconnectScmCommand` section.

### Obtaining Help

* `cxone-repo-tools -h` displays the global options and the list of available commands.
* `cxone-repo-tools -h <command>` displays the usage and options for one command.  This is the
  form to give the user when they want to see a command's options.
* The command-specific help can also be shown by placing `-h` after the command when the global
  options are present, for example
  `cxone-repo-tools --tenant mytenant --cxone-region US --api-key-env disconnect-scm -h`.
* `cxone-repo-tools <command> -h` (the command first, with no global options) does NOT work even
  though a command's usage text shows that shape.  Do not give that form to the user.

### Default Output Files

Commands that write files have per-command defaults that differ from older releases.  Use
the `[default: ...]` value shown in the command's own section, not a value remembered from a
previous version of the tool.

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
  