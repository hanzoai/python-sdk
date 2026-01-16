/**
 * Hanzo MCP VS Code Extension
 * ===========================
 * 
 * Integrates the 6 universal tools with VS Code for intelligent workspace operations.
 */

import * as vscode from 'vscode';
import axios from 'axios';

interface ToolResult {
    ok: boolean;
    root: string;
    language_used: string | string[];
    backend_used: string | string[];
    scope_resolved: string | string[];
    touched_files: string[];
    stdout: string;
    stderr: string;
    exit_code: number;
    errors: string[];
    execution_time: number;
    session_id: string;
}

class HanzoMCPClient {
    private backendUrl: string;
    
    constructor() {
        const config = vscode.workspace.getConfiguration('hanzo.mcp');
        this.backendUrl = config.get('backend.url', 'http://localhost:8765');
    }
    
    async callTool(toolName: string, args: any): Promise<ToolResult> {
        try {
            const response = await axios.post(`${this.backendUrl}/tools/${toolName}`, args);
            return response.data;
        } catch (error) {
            throw new Error(`Failed to call ${toolName}: ${error}`);
        }
    }
    
    private getCurrentTarget(): string {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            return `file:${editor.document.uri.fsPath}`;
        }
        
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (workspaceFolder) {
            return 'ws';
        }
        
        return 'dir:.';
    }
    
    private showResult(result: ToolResult, toolName: string) {
        const status = result.ok ? '✅' : '❌';
        const message = `${status} ${toolName} completed (${result.execution_time.toFixed(2)}s)`;
        
        if (result.ok) {
            vscode.window.showInformationMessage(message);
        } else {
            vscode.window.showErrorMessage(message);
        }
        
        // Show detailed output in output channel
        const output = vscode.window.createOutputChannel(`Hanzo MCP - ${toolName}`);
        output.clear();
        output.appendLine(`=== ${toolName.toUpperCase()} RESULT ===`);
        output.appendLine(`Status: ${status}`);
        output.appendLine(`Root: ${result.root}`);
        output.appendLine(`Language: ${result.language_used}`);
        output.appendLine(`Backend: ${result.backend_used}`);
        output.appendLine(`Files touched: ${result.touched_files.length}`);
        
        if (result.touched_files.length > 0) {
            output.appendLine('\nModified files:');
            result.touched_files.forEach(file => output.appendLine(`  - ${file}`));
        }
        
        if (result.stdout) {
            output.appendLine('\nOutput:');
            output.appendLine(result.stdout);
        }
        
        if (result.stderr) {
            output.appendLine('\nErrors:');
            output.appendLine(result.stderr);
        }
        
        if (result.errors.length > 0) {
            output.appendLine('\nIssues:');
            result.errors.forEach(error => output.appendLine(`  - ${error}`));
        }
        
        output.show();
        
        // Refresh file system for touched files
        if (result.touched_files.length > 0) {
            result.touched_files.forEach(file => {
                const uri = vscode.Uri.file(file);
                vscode.workspace.fs.stat(uri); // Trigger refresh
            });
        }
    }
}

export function activate(context: vscode.ExtensionContext) {
    const client = new HanzoMCPClient();
    
    // Command: Rename Symbol
    const renameSymbol = vscode.commands.registerCommand('hanzo.edit.rename', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }
        
        const newName = await vscode.window.showInputBox({
            prompt: 'Enter new symbol name',
            placeHolder: 'new_name'
        });
        
        if (!newName) return;
        
        const position = editor.selection.active;
        
        try {
            const result = await client.callTool('edit', {
                target: `file:${editor.document.uri.fsPath}`,
                op: 'rename',
                file: editor.document.uri.fsPath,
                pos: {
                    line: position.line,
                    character: position.character
                },
                new_name: newName
            });
            
            client.showResult(result, 'Rename');
        } catch (error) {
            vscode.window.showErrorMessage(`Rename failed: ${error}`);
        }
    });
    
    // Command: Organize Imports
    const organizeImports = vscode.commands.registerCommand('hanzo.edit.organizeImports', async () => {
        const target = client.getCurrentTarget();
        
        try {
            const result = await client.callTool('edit', {
                target,
                op: 'organize_imports'
            });
            
            client.showResult(result, 'Organize Imports');
        } catch (error) {
            vscode.window.showErrorMessage(`Organize imports failed: ${error}`);
        }
    });
    
    // Command: Format Code
    const formatCode = vscode.commands.registerCommand('hanzo.fmt.format', async () => {
        const config = vscode.workspace.getConfiguration('hanzo.mcp');
        const target = client.getCurrentTarget();
        
        try {
            const result = await client.callTool('fmt', {
                target,
                opts: {
                    local_prefix: config.get('localPrefix')
                }
            });
            
            client.showResult(result, 'Format');
        } catch (error) {
            vscode.window.showErrorMessage(`Format failed: ${error}`);
        }
    });
    
    // Command: Run Tests
    const runTests = vscode.commands.registerCommand('hanzo.test.run', async (uri?: vscode.Uri) => {
        let target = 'ws';
        
        if (uri) {
            const stat = await vscode.workspace.fs.stat(uri);
            if (stat.type === vscode.FileType.File) {
                target = `file:${uri.fsPath}`;
            } else {
                target = `dir:${uri.fsPath}`;
            }
        } else {
            target = client.getCurrentTarget();
        }
        
        try {
            const result = await client.callTool('test', {
                target,
                opts: {}
            });
            
            client.showResult(result, 'Test');
        } catch (error) {
            vscode.window.showErrorMessage(`Test failed: ${error}`);
        }
    });
    
    // Command: Build Project
    const buildProject = vscode.commands.registerCommand('hanzo.build.run', async (uri?: vscode.Uri) => {
        let target = 'ws';
        
        if (uri) {
            target = `dir:${uri.fsPath}`;
        }
        
        try {
            const result = await client.callTool('build', {
                target,
                opts: {}
            });
            
            client.showResult(result, 'Build');
        } catch (error) {
            vscode.window.showErrorMessage(`Build failed: ${error}`);
        }
    });
    
    // Command: Lint Code
    const lintCode = vscode.commands.registerCommand('hanzo.lint.check', async (uri?: vscode.Uri) => {
        let target = client.getCurrentTarget();
        
        if (uri) {
            const stat = await vscode.workspace.fs.stat(uri);
            if (stat.type === vscode.FileType.File) {
                target = `file:${uri.fsPath}`;
            } else {
                target = `dir:${uri.fsPath}`;
            }
        }
        
        const config = vscode.workspace.getConfiguration('hanzo.mcp');
        
        try {
            const result = await client.callTool('lint', {
                target,
                opts: {
                    fix: config.get('autoFix', false)
                }
            });
            
            client.showResult(result, 'Lint');
        } catch (error) {
            vscode.window.showErrorMessage(`Lint failed: ${error}`);
        }
    });
    
    // Command: Check Guard Rules
    const checkGuard = vscode.commands.registerCommand('hanzo.guard.check', async () => {
        const config = vscode.workspace.getConfiguration('hanzo.mcp');
        const rules = config.get('guardRules', []);
        
        if (rules.length === 0) {
            vscode.window.showWarningMessage('No guard rules configured');
            return;
        }
        
        try {
            const result = await client.callTool('guard', {
                target: 'ws',
                rules
            });
            
            client.showResult(result, 'Guard');
        } catch (error) {
            vscode.window.showErrorMessage(`Guard check failed: ${error}`);
        }
    });
    
    // Command: Search Symbols
    const searchSymbols = vscode.commands.registerCommand('hanzo.search.symbols', async () => {
        const query = await vscode.window.showInputBox({
            prompt: 'Search for symbols',
            placeHolder: 'symbol name or pattern'
        });
        
        if (!query) return;
        
        try {
            const result = await client.callTool('search_codebase', {
                query,
                type: 'symbols',
                limit: 50
            });
            
            client.showResult(result, 'Search');
        } catch (error) {
            vscode.window.showErrorMessage(`Search failed: ${error}`);
        }
    });
    
    // Command: Workspace Refactor (composition)
    const workspaceRefactor = vscode.commands.registerCommand('hanzo.workspace.refactor', async () => {
        const actions = await vscode.window.showQuickPick([
            'Multi-language rename',
            'Organize imports + format',
            'Format + test + guard',
            'Full workspace cleanup'
        ], {
            placeHolder: 'Select refactor action'
        });
        
        if (!actions) return;
        
        try {
            // Compose multiple tool calls based on selection
            switch (actions) {
                case 'Multi-language rename':
                    await vscode.commands.executeCommand('hanzo.edit.rename');
                    await vscode.commands.executeCommand('hanzo.fmt.format');
                    await vscode.commands.executeCommand('hanzo.test.run');
                    break;
                    
                case 'Organize imports + format':
                    await vscode.commands.executeCommand('hanzo.edit.organizeImports');
                    await vscode.commands.executeCommand('hanzo.fmt.format');
                    break;
                    
                case 'Format + test + guard':
                    await vscode.commands.executeCommand('hanzo.fmt.format');
                    await vscode.commands.executeCommand('hanzo.test.run');
                    await vscode.commands.executeCommand('hanzo.guard.check');
                    break;
                    
                case 'Full workspace cleanup':
                    await vscode.commands.executeCommand('hanzo.edit.organizeImports');
                    await vscode.commands.executeCommand('hanzo.fmt.format');
                    await vscode.commands.executeCommand('hanzo.lint.check');
                    await vscode.commands.executeCommand('hanzo.test.run');
                    await vscode.commands.executeCommand('hanzo.guard.check');
                    break;
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Workspace refactor failed: ${error}`);
        }
    });
    
    // Command: Session History
    const sessionHistory = vscode.commands.registerCommand('hanzo.session.history', async () => {
        try {
            const result = await client.callTool('get_session_history', {
                limit: 10
            });
            
            client.showResult(result, 'Session History');
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to get session history: ${error}`);
        }
    });
    
    // Auto-format on save
    const autoFormatSubscription = vscode.workspace.onDidSaveTextDocument(async (document) => {
        const config = vscode.workspace.getConfiguration('hanzo.mcp');
        
        if (config.get('autoFormat', true)) {
            try {
                await client.callTool('fmt', {
                    target: `file:${document.uri.fsPath}`
                });
            } catch (error) {
                console.log('Auto-format failed:', error);
            }
        }
        
        if (config.get('autoOrganizeImports', true)) {
            try {
                await client.callTool('edit', {
                    target: `file:${document.uri.fsPath}`,
                    op: 'organize_imports'
                });
            } catch (error) {
                console.log('Auto-organize imports failed:', error);
            }
        }
    });
    
    // Register all commands and subscriptions
    context.subscriptions.push(
        renameSymbol,
        organizeImports,
        formatCode,
        runTests,
        buildProject,
        lintCode,
        checkGuard,
        searchSymbols,
        workspaceRefactor,
        sessionHistory,
        autoFormatSubscription
    );
    
    // Initialize status bar
    const statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    statusBar.text = "$(symbol-class) Hanzo MCP";
    statusBar.tooltip = "Hanzo MCP Tools Ready";
    statusBar.command = 'hanzo.workspace.refactor';
    statusBar.show();
    
    context.subscriptions.push(statusBar);
    
    vscode.window.showInformationMessage('Hanzo MCP extension activated! 🚀');
}

export function deactivate() {}