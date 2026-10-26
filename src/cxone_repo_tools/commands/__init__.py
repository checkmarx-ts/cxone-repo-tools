from .scm import (
    ExportProjectsCommand,
    ExportScmsCommand,
    ConvertScmsCommand,
    DisconnectScmCommand,
    ConnectScmCommand,
)
from .sca.package_repo import (
    AuditAssocCommand,
    AuditTagsCommand,
    InspectProjectCommand,
    InspectTagCommand,
    ManageTagCommand,
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
    AuditTagsCommand.CMD_NAME: AuditTagsCommand,
    InspectProjectCommand.CMD_NAME: InspectProjectCommand,
    InspectTagCommand.CMD_NAME: InspectTagCommand,
    ManageTagCommand.CMD_NAME: ManageTagCommand,
    DeployTagCommand.CMD_NAME: DeployTagCommand,
    UndeployTagCommand.CMD_NAME: UndeployTagCommand,
    PruneCommand.CMD_NAME: PruneCommand,
}
