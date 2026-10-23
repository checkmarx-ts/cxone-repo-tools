# SCA Private Package Repository Configurations

This reference covers the commands listed under the heading
`SCA Private Package Repository Configurations` in the `Available Commands` section of the
`cxone_repo_tools.__main__` docstring in `cxone-repo-tools-docs.md`.  That list is the
authoritative set of commands; it may grow over time.  Each command's purpose is given by
its one-line description in that list, and its options are in the command's own section of
`cxone-repo-tools-docs.md`, located as described in `SKILL.md` and
`usage-clarification.md`.  When this reference describes an operation, such as deploying a
tag or auditing associations, use the command list to find the command that performs it.

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

## The Tool's Model: Tags Are Valid Deployment Groups

* A **configuration tag** is used by this tool to model a group of configurations that is
  valid to deploy to a project together.
* The tool **enforces tag membership**: a tag may contain **at most one configuration per
  supported package manager type**.  The command that manages a tag's configurations
  rejects adding a configuration whose package manager type is already represented in the
  tag.
* The command that deploys a tag associates every configuration in the tag with the
  selected projects, and the command that undeploys a tag removes them.  Because tag
  membership is enforced, deploying a single tag to a project never produces a duplicate
  package manager type on that project.
* The command that audits associations exports the configurations associated with each
  project so the user can find projects whose associations are not valid.

### Always Warn About Changes Made Outside the Tool

The tag enforcement applies only to operations performed through this tool.  A project can
be put into an invalid deployment state when configuration associations are managed by
other means, for example:

* Associating configurations with a project in the Checkmarx One UI.
* Calling the Checkmarx One API directly, or using the low-level API methods of
  `cxone-async-api`, to associate configurations.
* Deploying more than one tag to the same project where the tags overlap in package
  manager type.

When producing CLI examples for the command that deploys a tag, warn the user that:

* The project must not already have a configuration of a package manager type contained
  in the tag unless it came from the same tag.
* Associations made outside this tool are not validated and can leave the project with
  duplicate package manager types.
* The command that audits associations should be run to confirm the deployment state when
  there is any doubt.

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
deployment, in particular:

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
