from typing import Optional
from os import path, listdir
import subprocess
import threading

import pylspclient
from pylspclient.lsp_pydantic_strcuts import TextDocumentIdentifier, TextDocumentItem, LanguageIdentifier, Position, Range, SymbolKind, CompletionTriggerKind, CompletionContext

def to_uri(path: str) -> str:
    if path.startswith("uri://"):
        return path
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

def server_process() -> subprocess.Popen:
    pylsp_cmd = ["pyright-langserver", "--stdio"]

    #pylsp_cmd = ["python", "-m", "pylsp"]
    #pylsp_cmd = ["ruff", "server", "--preview"]
    #pylsp_cmd = ["pylyzer", "--server"]
    p = subprocess.Popen(pylsp_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p

DEFAULT_CAPABILITIES = {
    'textDocument': {
        'completion': {
            'completionItem': {
                'commitCharactersSupport': True,
                'documentationFormat': ['markdown', 'plaintext'],
                'snippetSupport': True
            }
        }
    }
}
DEFAULT_ROOT = path.abspath("./examples/example-files/python/")

def json_rpc(server_process: subprocess.Popen) -> pylspclient.JsonRpcEndpoint:
    json_rpc_endpoint = pylspclient.JsonRpcEndpoint(server_process.stdin, server_process.stdout)
    return json_rpc_endpoint

def initialize_lsp(json_rpc: pylspclient.JsonRpcEndpoint) -> pylspclient.LspClient:
    lsp_endpoint = pylspclient.LspEndpoint(json_rpc)
    lsp_client = pylspclient.LspClient(lsp_endpoint)
    process_id = None
    root_path = None
    root_uri = to_uri(DEFAULT_ROOT)
    initialization_options = None
    capabilities = DEFAULT_CAPABILITIES
    trace = "off"
    workspace_folders = None

    initialize_response = lsp_client.initialize(process_id, root_path, root_uri, initialization_options, capabilities, trace, workspace_folders)

    # if initialize_response['serverInfo']['name'] != 'pylsp':
    #     raise RuntimeError("failed to initialize lsp_client")
    lsp_client.initialized()
    return lsp_client

def get_document_symbols(file_path: str, lsp_client: pylspclient.LspClient):
    relative_file_path = path.join(DEFAULT_ROOT, file_path)
    uri = to_uri(relative_file_path)
    text = open(relative_file_path, "r").read()
    languageId = LanguageIdentifier.PYTHON
    version = 1
    lsp_client.didOpen(TextDocumentItem(uri=uri, languageId=languageId, version=version, text=text))
    symbols = lsp_client.documentSymbol(TextDocumentIdentifier(uri=uri))
    return symbols


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

def get_function_definition(lsp_client: pylspclient.LspClient):
    add_dir(lsp_client, DEFAULT_ROOT)
    file_path = "lsp_client.py"
    relative_file_path = path.join(DEFAULT_ROOT, file_path)
    uri = to_uri(relative_file_path)
    file_content = open(relative_file_path, "r").read()

    position = string_in_text_to_position(file_content, "shutdown")
    print(f"position: {position}")
    
    definitions = lsp_client.definition(TextDocumentIdentifier(uri=uri), position)
    print(f"definitions: {definitions}")

    # result_path = from_uri(definitions[0].uri)
    # result_file_content = open(result_path, "r").read()
    # result_definition = range_in_text_to_string(result_file_content, definitions[0].range)

def main():
    p = server_process()
    try:
        rpc = json_rpc(p)
        client = initialize_lsp(rpc)
        print("Initialization successful.")

        # # get symbols in file
        # symbols = get_document_symbols("lsp_client.py", client)
        # for symbol in symbols:
        #     print(f"Name: {symbol.name},  Kind: {SymbolKind(symbol.kind).name}")

        # get definition
        get_function_definition(client)

    finally:
        p.kill()
        p.communicate()

if __name__ == "__main__":
    main()