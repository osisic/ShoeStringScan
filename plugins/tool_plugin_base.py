from abc import ABC, abstractmethod

class ToolError(Exception): pass
class ToolInstallError(ToolError): pass
class ToolScanError(ToolError): pass
class ToolParseError(ToolError): pass

class ToolPlugin(ABC):
    NAME = None
    PRIORITY = 100
    DEFAULT_CPU = "1"
    DEFAULT_MEM = "1g"
    DOCKER_IMAGE = None
    DOCKER_TAG_CMD = None

    @abstractmethod
    def ensure_image(self, offline: bool):
        pass

    @abstractmethod
    def scan(self, target, work_dir, cpu_limit, mem_limit):
        pass

    @abstractmethod
    def parse_results(self, raw_path):
        pass

    def cleanup(self):
        pass 