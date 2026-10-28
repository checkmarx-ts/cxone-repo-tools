# SCA Private Package Repository Configurations

This reference covers the commands listed under the heading
`SCA Private Package Repository Configurations` in the `Available Commands` section of the
`cxone_repo_tools.__main__` docstring in `cxone-repo-tools-docs.md`.  That list is the
authoritative set of commands; it may grow over time.  Each command's purpose is given by
its one-line description in that list, and its options are in the command's own section of
`cxone-repo-tools-docs.md`, located as described in `SKILL.md` and
`usage-clarification.md`.  When this reference describes an operation, such as associating a
tag's configurations with projects or auditing associations, use the command list to find
the command that performs it.

## Background

* SCA scans of a project may need to resolve dependencies from private package
  repositories.  Checkmarx One stores the package manager configuration content that
  grants that access as a **private package repository configuration** and associates
  configurations with projects.
* Each configuration has a **package manager type**.  The supported package manager types
  are NuGet, Maven, npm, Gradle, and Pip.
* The Checkmarx One documentation describes two ways to apply a configuration: committing
  a configuration file into each repository, or sending the configuration content through
  the API.  This tool uses only the API method.  **No file is added to any repository.**
  Do not instruct the user to add configuration files to repositories when they are using
  this tool.

## Server-Side Behavior That the Tool Works Around

* Checkmarx One does **not** enforce a limit of one configuration per package manager type
  for a project.  Two or more configurations of the same package manager type can be
  associated with one project.
* When a project has more than one configuration of the same package manager type, the
  SCA scan result is **undefined**.  SCA uses one of the configurations, chosen
  arbitrarily, and dependency resolution may succeed, fail, or resolve from the wrong
  repository on different scans.
* Checkmarx One does not enforce unique names for configurations or for configuration tags.

## The Tool's Model: Tags Are Valid Association Groups

* A **configuration tag** is used by this tool to model a group of configurations that is
  valid to associate with a project together.
* The tool **enforces tag membership**: a tag may contain **at most one configuration per
  supported package manager type**.  The command that manages a tag's configurations
  rejects adding a configuration whose package manager type is already represented in the
  tag.
* The command that creates a tag creates the tag and one configuration per package
  manager type from content files.  It does not associate anything with projects.
* The command that associates a tag's configurations with projects associates every
  configuration in the tag with the selected projects, then adds an SCA file exclusion
  for each configuration's file name to the SCA exclusions of every associated project so
  a file in the repository cannot override the associated configuration.  Because tag
  membership is enforced, associating a single tag with a project never produces a
  duplicate package manager type on that project.
* The command that purges a tag removes those SCA file exclusions from the associated
  projects, deletes the tag's configurations, and then deletes the tag.  Deleting a
  configuration removes it from every project it is associated with.
* The command that disassociates a tag's configurations from a single project removes
  the SCA file exclusions for those configurations from that project's settings and then
  removes the associations.  The configurations and the tag are not changed.  Use it to
  resolve a clash reported by the association command, or to take one project out of a
  tag's scope.
* The command that audits associations exports the configurations associated with each
  project so the user can find projects whose associations are not valid.

### Always Warn About Changes Made Outside the Tool

The tag enforcement applies only to operations performed through this tool.  A project can
be put into an invalid association state when configuration associations are managed by
other means, for example:

* Associating configurations with a project in the Checkmarx One UI.
* Calling the Checkmarx One API directly, or using the low-level API methods of
  `cxone-async-api`, to associate configurations.
* Associating more than one tag with the same project where the tags overlap in package
  manager type.

When producing CLI examples for the command that associates a tag's configurations with
projects, warn the user that:

* The project must not already have a configuration of a package manager type contained
  in the tag unless it came from the same tag.  A clash is resolved by disassociating the
  conflicting tag's configurations from the project with the disassociation command, then
  re-running the association command.
* Associations made outside this tool are not validated and can leave the project with
  duplicate package manager types.
* The command that audits associations should be run to confirm the association state when
  there is any doubt.

## Recommended Rollout Approach

Recommend the following approach when a user asks how to roll out private package
repository configurations with this tool.  Each step names an operation; find the command
that performs it in the SCA command list described at the top of this reference.

1. **Use a single tag if possible.**  One tag holding one configuration per package manager
   type is the simplest state to manage and audit.  Create additional tags only when
   different groups of projects genuinely need different repositories.
2. **Make each configuration cover every repository for its package manager type.**  Because
   a project can validly hold only one configuration per type, the configuration content for
   a type should list all private repositories of that type that any project may need.  At
   scan time every listed repository is queried for the required private packages, so a
   project does not need a configuration tailored to the repositories it happens to use.
3. **Create the tag, then associate it with all projects.**  Create the tag with its
   configuration content files, then run the operation that automates association of a
   tag's configurations with projects, selecting all projects with a match-all name filter.
   Projects that already hold a configuration of a conflicting type are skipped and reported;
   resolve those by inspecting the project and removing the conflicting association.
4. **Update the tag, not the projects.**  Changing the content of a configuration in the
   tag propagates automatically to every project associated with that configuration and takes
   effect on each project's next scan.  No re-association is needed after a content update.
5. **Run the automated association periodically.**  Projects created after the rollout have
   no configurations associated.  Schedule the automated association operation to run on a
   regular basis, for example daily or from a pipeline, with the same project filter used for
   the initial association.  Projects already holding the tag's configurations are unaffected,
   so the operation is safe to repeat.  Recommend this for every tag in use.
6. **Keep configuration content under source control.**  Store the content files passed to
   the create and update operations in a source control repository so that changes are
   reviewed, versioned, and recoverable.  The tool reads content from files for exactly this
   reason.

When several tags are unavoidable, warn the user that no two tags associated with the same
project may contain configurations of the same package manager type, and recommend the
project audit after any association run to confirm there are no duplicates.

## Audit CSV Data

Two commands write CSV files that the user may provide for analysis or to decide what to do next.
Both have one column per supported package manager type, named after the type (for example
`nuget`, `npm`), holding a count.  A count greater than 1 in any such column is a duplicate
package manager type and should be called out as a problem.

* **Project audit** (the command that audits configuration associations for every project):
  columns `project_name`, `project_id`, one count column per package manager type giving the
  number of configurations of that type associated with the project, and `sca_file_filters`
  holding the project's SCA file exclusions string as stored in Checkmarx One.  A project with
  all counts at 0 has no private package repository configurations.
* **Tag audit** (the command that audits every tag): columns `tag_name`, `tag_id`, and one
  count column per package manager type giving the number of configurations of that type in
  the tag.  A tag with all counts at 0 is empty.

## Recovering From a Failed Command

The Checkmarx One API has no way to make the multi-step changes these commands perform
atomically.  Each step is a separate API call, and if a step fails the earlier steps
remain in effect.  The log identifies the step that failed; a failed project settings
write is logged as an error naming the project id and the remaining projects are still
processed in the same run.  Recovery depends on the command:

* **Association command** (associates a tag's configurations with projects): re-run the
  same command.  Existing associations are kept, exclusion filters already present are
  not added again, and only the missing work is done.  This command is designed to be
  re-run on a schedule.
* **Update command**: re-run the same command.  Existing configurations are updated in
  place and configurations that were not created on the failed run are created.
* **Create command**: it is **not** re-runnable.  It refuses to run when a tag with the
  name already exists, which is the case after a partial failure.  Recover by running the
  update command with the same tag name and the same content files; it creates the
  configurations that are missing and leaves the ones that were created.  Alternatively,
  purge the partial tag and create it again.
* **Purge command**: it is **not** re-runnable once the tag is deleted, because the tag can
  no longer be found.  After a partial failure in which the tag still exists, re-run the
  purge to finish removing exclusions and deleting configurations and the tag.  Because
  exclusions are removed before configurations are deleted, a failure leaves projects
  briefly reading repository configuration files while the configuration still exists; if
  the user decides to keep the tag instead, re-run the association command to restore the
  exclusions.  If a project settings write failed and the purge then completed, the
  leftover exclusion filters for that project must be removed through the project's scan
  settings, since the tag no longer exists for the tool to act on.

The project audit can be used at any time to confirm the resulting state.

## Cloud Connections and Credential Substitution

Configuration content does not contain credentials or repository URLs directly.  Instead
it references a **Cloud Connection** defined in Checkmarx One under
`Integrations > Cloud Connections`.  The connection stores the URL, username, and
password.  At scan time Checkmarx One substitutes variables in the configuration content
from the named connection.

| Variable | Substituted with |
|---|---|
| `${{cx.<MASK_NAME>.url}}` | The connection URL |
| `${{cx.<MASK_NAME>.url\|no_protocol}}` | The connection URL with the `https://` scheme removed (used where a package manager needs a host and path without a scheme, such as the npm auth token line) |
| `${{cx.<MASK_NAME>.username}}` | The connection username |
| `${{cx.<MASK_NAME>.password}}` | The connection password, API key, or token |

`<MASK_NAME>` is replaced by the **name of the Cloud Connection**.  The user chooses the
name when creating the connection.

### Supported Connection Types

Cloud Connections currently support only two private registry types:

* **GitHub Packages**
* **JFrog Artifactory**

For these two types the `${{cx.<MASK_NAME>.url}}` variable is valid and the templates
below can be used as written, after editing the repository path segments.

### Other Package Repositories (for example Azure Artifacts)

For a package repository that is not GitHub Packages or JFrog Artifactory:

* There is no Cloud Connection type for it, so `${{cx.<MASK_NAME>.url}}` cannot produce
  the repository URL.  The repository URL **must be written explicitly** in the
  configuration content.
* Credentials can still be kept out of the content.  Create a JFrog Artifactory Cloud
  Connection that exists only to hold the username and password.  Give it a URL in
  CxLink format, `https://<subdomain>.<domain>/link/<UUID>`, so it is not mistaken for a
  real Artifactory endpoint.  Reference its `username` and `password` variables from the
  content and ignore its `url` variable.
* Example for Azure Artifacts: store the username `any` and an Azure DevOps personal
  access token as the password in the placeholder connection.  In the configuration
  content, write the Azure Artifacts feed URL explicitly and use
  `${{cx.<MASK_NAME>.username}}` and `${{cx.<MASK_NAME>.password}}` for the credentials.

When helping a user form content for such a repository, state clearly which parts are
literal and which are substituted, and remind them that the placeholder connection's URL
is never used.

## Configuration Content Formats

The content of a configuration is the text of a native package manager configuration
file.  The formats below are taken from the Checkmarx One documentation page
"GitHub Container Registry Integration for SCA Scanner".  They show the **intended basic
structure** of each format.  The user is expected to **modify the content** before
creating or updating a tag, in particular:

* Replace `<MASK_NAME>` with the Cloud Connection name.
* Replace the repository path segments (the examples use Artifactory paths containing
  `automatedtests-...`) with the user's actual repository paths.
* Replace scope names, repository ids, and profile ids with the user's values.
* Replace the `${{cx.<MASK_NAME>.url}}` variable with an explicit URL when the repository
  is not a supported Cloud Connection type.

The NuGet, npm, and Pip formats are reproduced exactly from the documentation.  The Maven
and Gradle formats are structurally equivalent reproductions; element names, ids, URL
paths, and variables match the documentation.

### NuGet

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <packageSources>
    <add key="nuget.org" value="https://api.nuget.org/v3/index.json" />
    <add key="Artifactory" value="${{cx.<MASK_NAME>.url}}/artifactory/api/nuget/v3/automatedtests-nuget/" />
  </packageSources>
  <packageSourceCredentials>
    <Artifactory>
      <add key="Username" value="${{cx.<MASK_NAME>.username}}" />
      <add key="ClearTextPassword" value="${{cx.<MASK_NAME>.password}}" />
    </Artifactory>
  </packageSourceCredentials>
</configuration>
```

### Maven

```xml
<?xml version="1.0" encoding="UTF-8"?>
<settings xmlns="http://maven.apache.org/SETTINGS/1.2.0"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.2.0 https://maven.apache.org/xsd/settings-1.2.0.xsd">
  <servers>
    <server>
      <id>jfrog</id>
      <username>${{cx.<MASK_NAME>.username}}</username>
      <password>${{cx.<MASK_NAME>.password}}</password>
    </server>
  </servers>
  <profiles>
    <profile>
      <id>artifactory</id>
      <repositories>
        <repository>
          <id>central</id>
          <name>cx-virtual</name>
          <url>${{cx.<MASK_NAME>.url}}/artifactory/automatedtests-maven/</url>
          <snapshots>
            <enabled>true</enabled>
          </snapshots>
        </repository>
      </repositories>
    </profile>
  </profiles>
  <activeProfiles>
    <activeProfile>artifactory</activeProfile>
  </activeProfiles>
</settings>
```

### npm

```
registry=https://registry.npmjs.org/

email = ${{cx.<MASK_NAME>.username}}
always-auth = true
@checkmarx:registry=${{cx.<MASK_NAME>.url}}/artifactory/api/npm/automatedtests-npm/
//${{cx.<MASK_NAME>.url|no_protocol}}/artifactory/api/npm/automatedtests-npm/:_authToken=${{cx.<MASK_NAME>.password}}
```

### Gradle

```groovy
allprojects {
  repositories {
    maven {
      name = 'private.repositories'
      url = '${{cx.<MASK_NAME>.url}}/artifactory/automatedtests-gradle/'
      credentials {
        username = '${{cx.<MASK_NAME>.username}}'
        password = '${{cx.<MASK_NAME>.password}}'
      }
    }
  }
}
```

### Pip

```
[global]
extra-index-url = 
https://${{cx.<MASK_NAME>.username}}:${{cx.<MASK_NAME>.password}}@${{cx.<MASK_NAME>.url}}/artifactory/api/pypi/automatedtests-pypi/simple
```
