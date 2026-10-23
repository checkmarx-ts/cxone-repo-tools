from .export_projects import ExportProjectsCommand
from .export_scms import ExportScmsCommand
from .convert_scms import ConvertScmsCommand
from .disconnect_scm import DisconnectScmCommand
from .connect_scm import ConnectScmCommand

command_map = {
    ExportProjectsCommand.CMD_NAME: ExportProjectsCommand,
    ExportScmsCommand.CMD_NAME: ExportScmsCommand,
    ConvertScmsCommand.CMD_NAME: ConvertScmsCommand,
    DisconnectScmCommand.CMD_NAME: DisconnectScmCommand,
    ConnectScmCommand.CMD_NAME: ConnectScmCommand,
}
