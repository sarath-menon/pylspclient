#%%
from typing import Optional
from os import path, listdir
import subprocess

import pylspclient
from pylspclient.lsp_pydantic_strcuts import TextDocumentIdentifier, TextDocumentItem, LanguageIdentifier, Position, Range, SymbolKind, CompletionTriggerKind, CompletionContext
from utils import to_uri, from_uri, add_file, add_dir, string_in_text_to_position, range_in_text_to_string

#%%

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
DEFAULT_ROOT = path.abspath("../examples/example-files/python/")

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




def get_function_definition(lsp_client: pylspclient.LspClient, file_path: str, function_name: str):
    add_dir(lsp_client, DEFAULT_ROOT)
    relative_file_path = path.join(DEFAULT_ROOT, file_path)
    uri = to_uri(relative_file_path)
    file_content = open(relative_file_path, "r").read()

    position = string_in_text_to_position(file_content, function_name)
    print(f"position: {position}")
    
    definitions = lsp_client.definition(TextDocumentIdentifier(uri=uri), position)
    print(f"definitions: {definitions}")

    # result_path = from_uri(definitions[0].uri)
    # result_file_content = open(result_path, "r").read()
    # result_definition = range_in_text_to_string(result_file_content, definitions[0].range)

#%% # get symbols in file

p = server_process()    
rpc = json_rpc(p)
client = initialize_lsp(rpc)

file_path = "lsp_client.py"
symbols = get_document_symbols("lsp_client.py", client)

for symbol in symbols:
    print(f"Name: {symbol.name},  Kind: {SymbolKind(symbol.kind).name}")

p.kill()
p.communicate()
#%% # get definition

p = server_process()    
rpc = json_rpc(p)
client = initialize_lsp(rpc)
print("Initialization successful.")

file_path = "lsp_client.py"
function_name = "shutdown"
get_function_definition(client, file_path, function_name)

p.kill()
p.communicate()