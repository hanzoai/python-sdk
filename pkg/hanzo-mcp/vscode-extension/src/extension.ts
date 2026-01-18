import * as vscode from 'vscode';
import * as path from 'path';
import * as os from 'os';
import { spawn, ChildProcess } from 'child_process';
import { WebSocketServer, WebSocket } from 'ws';

interface HanzoSession {
    session_id: string;
    start_time: string;
    tool_count: number;
    tools_used: string[];
}

class HanzoMCPProvider implements vscode.TreeDataProvider<HanzoSession> {
    private _onDidChangeTreeData: vscode.EventEmitter<HanzoSession | undefined | null | void> = new vscode.EventEmitter<HanzoSession | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<HanzoSession | undefined | null | void> = this._onDidChangeTreeData.event;
    
    private sessions: HanzoSession[] = [];
    private mcpProcess: ChildProcess | null = null;
    private wsServer: WebSocketServer | null = null;

    constructor(private context: vscode.ExtensionContext) {
        this.startMCPBackend();
        this.refreshSessions();
    }

    refresh(): void {
        this.refreshSessions();
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: HanzoSession): vscode.TreeItem {
        const item = new vscode.TreeItem(
            `Session ${element.session_id.substring(0, 8)}`,
            vscode.TreeItemCollapsibleState.None
        );
        item.description = `${element.tool_count} tools, ${element.tools_used.join(', ')}`;
        item.tooltip = `Started: ${element.start_time}`;
        return item;
    }

    getChildren(element?: HanzoSession): Thenable<HanzoSession[]> {
        if (!element) {
            return Promise.resolve(this.sessions);
        }
        return Promise.resolve([]);
    }

    private startMCPBackend() {
        const config = vscode.workspace.getConfiguration('hanzo-mcp');
        
        // Start the unified MCP backend
        this.mcpProcess = spawn('python', ['-m', 'hanzo_mcp.unified_backend'], {
            stdio: ['pipe', 'pipe', 'pipe'],
            env: { ...process.env, PYTHONPATH: process.env.PYTHONPATH }
        });

        this.mcpProcess.on('error', (err) => {
            vscode.window.showErrorMessage(`Hanzo MCP backend error: ${err.message}`);
        });

        // Start WebSocket server for real-time communication
        this.wsServer = new WebSocketServer({ port: 8765 });
        this.wsServer.on('connection', (ws: WebSocket) => {
            ws.on('message', (data: Buffer) => {
                const message = JSON.parse(data.toString());
                this.handleMCPMessage(message);
            });
        });
    }

    private handleMCPMessage(message: any) {
        if (message.type === 'tool_executed') {
            this.refreshSessions();
            
            // Show notification for important operations
            if (message.data.tool === 'guard' && !message.data.result.ok) {
                vscode.window.showWarningMessage(
                    `Guard violations found: ${message.data.result.violations.length} issues`
                );
            }
        }
    }

    private async refreshSessions() {
        try {
            const result = await this.executeMCPCommand('get_sessions');
            this.sessions = result.sessions || [];
        } catch (err) {
            console.error('Failed to refresh sessions:', err);
        }
    }

    private async executeMCPCommand(command: string, args: any = {}): Promise<any> {
        return new Promise((resolve, reject) => {
            if (!this.mcpProcess) {
                reject(new Error('MCP backend not running'));
                return;
            }

            const request = JSON.stringify({ command, args, id: Date.now() });
            this.mcpProcess.stdin?.write(request + '\n');

            const timeout = setTimeout(() => {
                reject(new Error('Command timeout'));
            }, 10000);

            const handler = (data: Buffer) => {
                try {
                    const response = JSON.parse(data.toString());
                    if (response.id === JSON.parse(request).id) {
                        clearTimeout(timeout);
                        this.mcpProcess?.stdout?.off('data', handler);
                        if (response.error) {
                            reject(new Error(response.error));
                        } else {
                            resolve(response.result);
                        }
                    }
                } catch (err) {
                    // Ignore parsing errors, might be partial data
                }
            };

            this.mcpProcess.stdout?.on('data', handler);
        });
    }

    async executeEdit(operation: string) {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }

        const document = editor.document;
        const position = editor.selection.active;
        
        try {
            const result = await this.executeMCPCommand('edit', {
                target: `file:${document.fileName}`,
                op: operation,
                file: document.fileName,
                pos: { line: position.line, character: position.character }
            });

            if (result.touched_files?.length > 0) {
                // Reload affected files
                for (const file of result.touched_files) {
                    const uri = vscode.Uri.file(file);
                    const doc = await vscode.workspace.openTextDocument(uri);
                    await vscode.window.showTextDocument(doc);
                }
                vscode.window.showInformationMessage(`Edit completed: ${result.touched_files.length} files modified`);
            }
        } catch (err) {
            vscode.window.showErrorMessage(`Edit failed: ${err}`);
        }
    }

    async executeFormat() {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('No workspace folder');
            return;
        }

        const config = vscode.workspace.getConfiguration('hanzo-mcp');
        const localPrefix = config.get('goLocalPrefix', 'github.com/luxfi');

        try {
            const result = await this.executeMCPCommand('fmt', {
                target: 'changed',  // Format only changed files
                local_prefix: localPrefix
            });

            if (result.ok) {
                vscode.window.showInformationMessage(`Formatted ${result.touched_files.length} files`);
            } else {
                vscode.window.showErrorMessage(`Format failed: ${result.errors.join(', ')}`);
            }
        } catch (err) {
            vscode.window.showErrorMessage(`Format failed: ${err}`);
        }
    }

    async executeTest() {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('No workspace folder');
            return;
        }

        try {
            const result = await this.executeMCPCommand('test', {
                target: 'ws'  // Test entire workspace
            });

            const output = vscode.window.createOutputChannel('Hanzo Test');
            output.appendLine(result.stdout);
            if (result.stderr) {
                output.appendLine('STDERR:');
                output.appendLine(result.stderr);
            }
            output.show();

            if (result.ok) {
                vscode.window.showInformationMessage('Tests passed');
            } else {
                vscode.window.showErrorMessage(`Tests failed (exit code: ${result.exit_code})`);
            }
        } catch (err) {
            vscode.window.showErrorMessage(`Test failed: ${err}`);
        }
    }

    async executeBuild() {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('No workspace folder');
            return;
        }

        try {
            const result = await this.executeMCPCommand('build', {
                target: 'ws'
            });

            const output = vscode.window.createOutputChannel('Hanzo Build');
            output.appendLine(result.stdout);
            if (result.stderr) {
                output.appendLine('STDERR:');
                output.appendLine(result.stderr);
            }
            output.show();

            if (result.ok) {
                vscode.window.showInformationMessage('Build succeeded');
            } else {
                vscode.window.showErrorMessage(`Build failed (exit code: ${result.exit_code})`);
            }
        } catch (err) {
            vscode.window.showErrorMessage(`Build failed: ${err}`);
        }
    }

    async executeLint(fix: boolean = false) {
        const editor = vscode.window.activeTextEditor;
        const target = editor ? `file:${editor.document.fileName}` : 'ws';

        try {
            const result = await this.executeMCPCommand('lint', {
                target,
                fix
            });

            if (result.ok) {
                if (fix && result.touched_files.length > 0) {
                    vscode.window.showInformationMessage(`Lint fixes applied to ${result.touched_files.length} files`);
                    // Reload the files
                    for (const file of result.touched_files) {
                        const uri = vscode.Uri.file(file);
                        const doc = await vscode.workspace.openTextDocument(uri);
                        await vscode.window.showTextDocument(doc);
                    }
                } else {
                    vscode.window.showInformationMessage('Lint check passed');
                }
            } else {
                vscode.window.showErrorMessage(`Lint failed: ${result.errors.join(', ')}`);
            }
        } catch (err) {
            vscode.window.showErrorMessage(`Lint failed: ${err}`);
        }
    }

    async executeGuard() {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('No workspace folder');
            return;
        }

        try {
            const result = await this.executeMCPCommand('guard', {
                target: 'ws',
                rules: [
                    {
                        id: 'no_node_in_sdk',
                        type: 'import',
                        glob: 'sdk/**',
                        forbid_import_prefix: 'github.com/luxfi/node/'
                    },
                    {
                        id: 'no_generated_edits',
                        type: 'generated',
                        glob: 'api/pb/**',
                        forbid_writes: true
                    }
                ]
            });

            if (result.violations && result.violations.length > 0) {
                const violationsText = result.violations.map((v: any) => 
                    `${v.file}:${v.line} - ${v.rule_id}: ${v.text}`
                ).join('\n');
                
                const output = vscode.window.createOutputChannel('Hanzo Guard');
                output.appendLine('Guard Violations:');
                output.appendLine(violationsText);
                output.show();
                
                vscode.window.showWarningMessage(`${result.violations.length} guard violations found`);
            } else {
                vscode.window.showInformationMessage('All guard checks passed');
            }
        } catch (err) {
            vscode.window.showErrorMessage(`Guard check failed: ${err}`);
        }
    }

    dispose() {
        this.mcpProcess?.kill();
        this.wsServer?.close();
    }
}

export function activate(context: vscode.ExtensionContext) {
    const provider = new HanzoMCPProvider(context);
    
    // Register tree view
    vscode.window.createTreeView('hanzo-mcp-sessions', { 
        treeDataProvider: provider,
        showCollapseAll: true
    });

    // Register commands
    const commands = [
        vscode.commands.registerCommand('hanzo-mcp.edit', () => provider.executeEdit('organize_imports')),
        vscode.commands.registerCommand('hanzo-mcp.fmt', () => provider.executeFormat()),
        vscode.commands.registerCommand('hanzo-mcp.test', () => provider.executeTest()),
        vscode.commands.registerCommand('hanzo-mcp.build', () => provider.executeBuild()),
        vscode.commands.registerCommand('hanzo-mcp.lint', () => provider.executeLint(false)),
        vscode.commands.registerCommand('hanzo-mcp.guard', () => provider.executeGuard()),
        vscode.commands.registerCommand('hanzo-mcp.sessions.view', () => provider.refresh()),
        vscode.commands.registerCommand('hanzo-mcp.workspace.refactor', async () => {
            const choice = await vscode.window.showQuickPick([
                'Multi-language rename',
                'Go workspace refactor',
                'Format all',
                'Test all',
                'Lint all'
            ], { placeHolder: 'Choose refactoring operation' });
            
            switch (choice) {
                case 'Multi-language rename':
                    const symbolName = await vscode.window.showInputBox({ 
                        prompt: 'Enter symbol to rename' 
                    });
                    const newName = await vscode.window.showInputBox({ 
                        prompt: 'Enter new name' 
                    });
                    if (symbolName && newName) {
                        // Implementation for multi-language rename
                    }
                    break;
                case 'Go workspace refactor':
                    // Execute wide Go refactor
                    break;
                case 'Format all':
                    await provider.executeFormat();
                    break;
                case 'Test all':
                    await provider.executeTest();
                    break;
                case 'Lint all':
                    await provider.executeLint(true);
                    break;
            }
        }),
        vscode.commands.registerCommand('hanzo-mcp.codebase.index', async () => {
            vscode.window.showInformationMessage('Indexing codebase...');
            try {
                await provider.executeMCPCommand('index_codebase');
                vscode.window.showInformationMessage('Codebase indexing completed');
            } catch (err) {
                vscode.window.showErrorMessage(`Indexing failed: ${err}`);
            }
        })
    ];

    context.subscriptions.push(...commands, provider);
}

export function deactivate() {}