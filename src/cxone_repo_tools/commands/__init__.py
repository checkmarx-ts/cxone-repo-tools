from .export_projects import ExportProjectsCommand
from .export_scms import ExportScmsCommand
from .convert_scms import ConvertScmsCommand
from .disconnect_scm import DisconnectScmCommand
from .connect_scm import ConnectScmCommand
from .audit_assoc import AuditAssocCommand
from .manage_tag import ManageTagCommand
from .deploy_tag import DeployTagCommand
from .undeploy_tag import UndeployTagCommand
from .inspect_project import InspectProjectCommand
from .inspect_tag import InspectTagCommand
from .audit_tags import AuditTagsCommand
from .prune import PruneCommand

command_map = {
    ExportProjectsCommand.CMD_NAME: ExportProjectsCommand,
    ExportScmsCommand.CMD_NAME: ExportScmsCommand,
    ConvertScmsCommand.CMD_NAME: ConvertScmsCommand,
    DisconnectScmCommand.CMD_NAME: DisconnectScmCommand,
    ConnectScmCommand.CMD_NAME: ConnectScmCommand,
    AuditAssocCommand.CMD_NAME: AuditAssocCommand,
    ManageTagCommand.CMD_NAME: ManageTagCommand,
    DeployTagCommand.CMD_NAME: DeployTagCommand,
    UndeployTagCommand.CMD_NAME: UndeployTagCommand,
    InspectProjectCommand.CMD_NAME: InspectProjectCommand,
    InspectTagCommand.CMD_NAME: InspectTagCommand,
    AuditTagsCommand.CMD_NAME: AuditTagsCommand,
    PruneCommand.CMD_NAME: PruneCommand,
}
