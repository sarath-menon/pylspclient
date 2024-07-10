import {
    TextDocumentIdentifier,
    TextDocumentItem,
    LanguageIdentifier,
    Position,
    Range,
} from "pylspclient/lsp_pydantic_strcuts";


function main() {
    const textDocumentIdentifier = TextDocumentIdentifier({
        uri: "file:///path/to/your/file",
    });
}