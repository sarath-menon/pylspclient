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
    #pylsp_cmd = ["python", "-m", "pylsp"]
    pylsp_cmd = ["pyright-langserver", "--stdio"]
    # pylsp_cmd = ["ruff", "server", "--preview"]
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

def main():
    p = server_process()
    try:
        rpc = json_rpc(p)
        client = initialize_lsp(rpc)
        print("Initialization successful.")
        symbols = get_document_symbols("lsp_client.py", client)
        for symbol in symbols:
            print(f"Name: {symbol.name},  Kind: {SymbolKind(symbol.kind).name}")
    finally:
        p.kill()
        p.communicate()

if __name__ == "__main__":
    main()