# Usage Clarification

This reference covers usage that applies to every command.  Command-specific behavior is
in `conversion-clarification.md` for SCM connection management and in
`sca-private-package-repos.md` for private package repository configurations.

## Identifying Projects

* The project id of any project, including manual projects that are not connected to an
  SCM, can be obtained from the Checkmarx One UI.  The project export only lists projects
  connected to an SCM.

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

### Dynamic Command Docstrings

`cxone-repo-tools-docs.md` is generated from the docstrings as written in the source code.
Some commands build their docstring at runtime from a template so that the options track
data defined elsewhere.  For those commands the reference shows the template, with
placeholders in braces where the generated text belongs.  The placeholders are never typed
on the command line.

How to recognise and expand a template:

* A usage line or option list containing a token such as `{USAGE_OPTIONS}` or `{PM_OPTIONS}`
  is a template.  The surrounding description text explains what the placeholder expands to.
* When the description says an option is generated per **package manager type**, the expansion
  is one option per supported type, named after the type in lower case.  The supported types
  are listed in `references/sca-private-package-repos.md`.  Today they are `nuget`, `maven`,
  `npm`, `pip`, and `gradle`, giving `--nuget FILE`, `--maven FILE`, `--npm FILE`,
  `--pip FILE`, and `--gradle FILE`.
* Option argument names in the template (for example `FILE`) keep their meaning for every
  generated option.
* The runtime help, `cxone-repo-tools -h <command>`, always shows the fully expanded options.
  When unsure of an expansion, instruct the user to run that command and paste the output
  rather than guessing.
* Treat a literal `{...}` token in a produced example as an error; expand it or ask the user
  for the help output.

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

## Connections

* Authentication with Checkmarx One is performed using either an API key or OAuth client credentials.  It is
  suggested that the user that creates the API key, or the OAuth client, has administrative
  rights in Checkmarx One.  The API key or OAuth client secret can be provided on the command
  line or read from the environment variables `CX_API_KEY` or `CX_CLIENT_SECRET`.
* The `--cxone-region` option is used for multi-tenant Checkmarx One connections.
* The `--cxone-hostname` option is used for single-tenant Checkmarx One connections.
* The `--retries` option is set to a high value to avoid missing data
  when the Checkmarx One API responses are delayed due to a higher than normal
  number of requests.
* In addition to delays, the Checkmarx One infrastructure may scale to handle the
  higher volume of requests.  This may cause a temporary series of 5XX responses.
  