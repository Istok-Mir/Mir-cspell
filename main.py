from __future__ import annotations
import sublime_plugin
from Mir.types.lsp import URI, DocumentUri, TextEdit
from Mir import LanguageServer, mir, deno, LoaderInStatusBar, PackageStorage, command
from typing import Dict, List, Optional, Tuple, TypedDict


server_storage = PackageStorage(tag='0.0.1')
server_path = server_storage / "language-server" / "_server" / 'main.cjs'

async def package_storage_setup():
    if server_path.exists():
        return
    await deno.setup()
    server_storage.copy("./language-server")
    with LoaderInStatusBar(f'installing cSpell'):
        await command([deno.path, "install"], cwd=str(server_storage / "language-server"))


class CspellLanguageServer(LanguageServer):
    name='cSpell'
    activation_events={
        'selector': 'source.dosbatch | source.c | source.c++ | source.objc | source.objc++ | source.clojure | source.cs | source.cake | source.css | source.dart | source.diff | source.dockerfile | source.elixir | source.erlang | source.fsharp | text.git-commit | source.go | source.gomod | source.graphql | source.haskell | text.html.basic | source.ini | source.java | source.jsx | source.js.react | source.js | source.tsx | source.ts | source.json | source.julia | text.tex.latex | source.less | source.lua | source.makefile | text.html.markdown | source.perl | text.html.twig | text.blade | embedding.php | text.plain | source.powershell | source.python | source.r | source.ruby | source.rust | source.scala | source.scss | source.sql | source.swift | text.html.vue | text.xml | text.html.svelte | source.yml | source.yaml',
    }
    settings_file="Mir-cspell.sublime-settings"

    async def activate(self):
        # setup runtime and install dependencies
        await package_storage_setup()

        async def on_workspace_config_for_document(params: WorkspaceConfigForDocumentRequest) -> WorkspaceConfigForDocumentResponse:
            # It looks like this method is necessary to enable code actions...
            return {
                'uri': None,
                'workspaceFile': None,
                'workspaceFolder': None,
                'words': {},
                'ignoreWords': {}
            }
        self.on_request('onWorkspaceConfigForDocumentRequest', on_workspace_config_for_document)

        await self.initialize({
            'communication_channel': 'stdio',
            'command': [deno.path, 'run', '-A', server_path, '--stdio'],
        })


WorkspaceConfigForDocumentRequest = TypedDict('WorkspaceConfigForDocumentRequest', {
    'uri': DocumentUri
})

FieldExistsInTarget = Dict[str, bool]

WorkspaceConfigForDocumentResponse = TypedDict('WorkspaceConfigForDocumentResponse', {
    'uri': Optional[DocumentUri],
    'workspaceFile': Optional[URI],
    'workspaceFolder': Optional[URI],
    'words': FieldExistsInTarget,
    'ignoreWords': FieldExistsInTarget
})

DocumentVersion = int
EditTextArguments = Tuple[URI, DocumentVersion, List[TextEdit]]


mir.commands.register_command('cSpell.editText', 'cspell_edit_text')

class CspellEditTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, arguments: EditTextArguments):
        _uri, document_version, text_edits = arguments
        self.view.run_command('mir_apply_text_edits', {
            'text_edits': text_edits
        })
