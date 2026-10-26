from .scm import (
    ExportProjectsCommand,
    ExportScmsCommand,
    ConvertScmsCommand,
    DisconnectScmCommand,
    ConnectScmCommand,
)
from .sca.package_repo import (
    AuditAssocCommand,
    AutoAssocCommand,
    AuditTagsCommand,
    InspectProjectCommand,
    InspectTagCommand,
    UpdateTagCommand,
    DeployTagCommand,
    UndeployTagCommand,
    PruneCommand,
)

command_map = {
    ExportProjectsCommand.CMD_NAME: ExportProjectsCommand,
    ExportScmsCommand.CMD_NAME: ExportScmsCommand,
    ConvertScmsCommand.CMD_NAME: ConvertScmsCommand,
    DisconnectScmCommand.CMD_NAME: DisconnectScmCommand,
    ConnectScmCommand.CMD_NAME: ConnectScmCommand,
    AuditAssocCommand.CMD_NAME: AuditAssocCommand,
    AutoAssocCommand.CMD_NAME: AutoAssocCommand,
    AuditTagsCommand.CMD_NAME: AuditTagsCommand,
    InspectProjectCommand.CMD_NAME: InspectProjectCommand,
    InspectTagCommand.CMD_NAME: InspectTagCommand,
    UpdateTagCommand.CMD_NAME: UpdateTagCommand,
    DeployTagCommand.CMD_NAME: DeployTagCommand,
    UndeployTagCommand.CMD_NAME: UndeployTagCommand,
    PruneCommand.CMD_NAME: PruneCommand,
}
