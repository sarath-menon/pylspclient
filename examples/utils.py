import threading
import subprocess
import pylspclient
from pylspclient.lsp_pydantic_strcuts import TextDocumentItem, LanguageIdentifier, Position, Range, SymbolKind, CompletionTriggerKind, CompletionContext
from os import listdir, path
from typing import Optional

def to_uri(path: str, uri_scheme: str = "plain") -> str:
    if uri_scheme == "file":
        return f"file://{path}"

    elif uri_scheme == "plain":
        return f"uri://{path}"

def from_uri(path: str) -> str:
    return path.replace("uri://", "").replace("uri:", "")

class ReadPipe(threading.Thread):
    def __init__(self, pipe):
        threading.Thread.__init__(self)
        self.pipe = pipe

    def run(self):
        line = self.pipe.readline().decode('utf-8')
        while line:
            print(line)
            line = self.pipe.readline().decode('utf-8')

def json_rpc(server_process: subprocess.Popen) -> pylspclient.JsonRpcEndpoint:
    json_rpc_endpoint = pylspclient.JsonRpcEndpoint(server_process.stdin, server_process.stdout)
    return json_rpc_endpoint


def add_file(lsp_client: pylspclient.LspClient, relative_file_path: str):
    uri = to_uri(relative_file_path)
    text = open(relative_file_path, "r").read()
    languageId = LanguageIdentifier.PYTHON
    version = 1
    # First need to open the file, and then iterate over the docuemnt's symbols
    lsp_client.didOpen(TextDocumentItem(uri=uri, languageId=languageId, version=version, text=text))

def add_dir(lsp_client: pylspclient.LspClient, root: str):
    for filename in listdir(root):
        if filename.endswith(".py"):
            add_file(lsp_client, path.join(root, filename))

def string_in_text_to_position(text: str, string: str) -> Optional[Position]:
    for i, line in enumerate(text.splitlines()):
        char = line.find(string)
        if char != -1:
            return Position(line=i, character=char)
    return None

def range_in_text_to_string(text: str, range_: Range) -> Optional[str]:
    lines = text.splitlines()
    if range_.start.line == range_.end.line:
        # Same line
        return lines[range_.start.line][range_.start.character:range_.end.character]
    raise NotImplementedError