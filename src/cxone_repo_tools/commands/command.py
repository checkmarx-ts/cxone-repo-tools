from __future__ import annotations
from typing import List
from cxone_api import CxOneClient

class Command:

  def __init__(self, client : CxOneClient | None, max_threads : int, version : str):
    self.__client = client
    self.__threads = max_threads
    self.__version = version

  @property
  def client(self) -> CxOneClient:
    return self.__client

  @property
  def threads(self) -> int:
    return self.__threads

  @property
  def version(self) -> str:
    return self.__version

  async def execute(self, cmdline_args : List[str]):
    raise NotImplementedError(Command.execute.__name__)

  @staticmethod
  def print_help():
    raise NotImplementedError(Command.print_help.__name__)
