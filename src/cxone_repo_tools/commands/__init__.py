from .scm import (
    ExportProjectsCommand,
    ExportScmsCommand,
    ConvertScmsCommand,
    DisconnectScmCommand,
    ConnectScmCommand,
)
from .sca.package_repo import (
    AuditAssocCommand,
    AssocTagCommand,
    AuditTagsCommand,
    InspectProjectCommand,
    InspectTagCommand,
    UpdateTagCommand,
    CreateTagCommand,
    PurgeTagCommand,
    PruneRepoConfigsCommand,
)

command_map = {
    ExportProjectsCommand.CMD_NAME: ExportProjectsCommand,
    ExportScmsCommand.CMD_NAME: ExportScmsCommand,
    ConvertScmsCommand.CMD_NAME: ConvertScmsCommand,
    DisconnectScmCommand.CMD_NAME: DisconnectScmCommand,
    ConnectScmCommand.CMD_NAME: ConnectScmCommand,
    AuditAssocCommand.CMD_NAME: AuditAssocCommand,
    AssocTagCommand.CMD_NAME: AssocTagCommand,
    AuditTagsCommand.CMD_NAME: AuditTagsCommand,
    InspectProjectCommand.CMD_NAME: InspectProjectCommand,
    InspectTagCommand.CMD_NAME: InspectTagCommand,
    UpdateTagCommand.CMD_NAME: UpdateTagCommand,
    CreateTagCommand.CMD_NAME: CreateTagCommand,
    PurgeTagCommand.CMD_NAME: PurgeTagCommand,
    PruneRepoConfigsCommand.CMD_NAME: PruneRepoConfigsCommand,
}
