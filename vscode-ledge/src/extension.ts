import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as path from 'path';

let outputChannel: vscode.OutputChannel;

export function activate(context: vscode.ExtensionContext) {
    outputChannel = vscode.window.createOutputChannel('Ledge');

    context.subscriptions.push(
        vscode.commands.registerCommand('ledge.runFile', runFile),
        vscode.commands.registerCommand('ledge.runSelection', runSelection),
        vscode.commands.registerCommand('ledge.openRepl', openRepl),
    );

    // Status bar button
    const statusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    statusItem.command = 'ledge.runFile';
    statusItem.text = '$(play) Run Ledge';
    statusItem.tooltip = 'Run the current Ledge file (Ctrl+Shift+Enter)';
    context.subscriptions.push(statusItem);

    // Show status bar item when a .ledge file is active
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor(editor => {
            if (editor?.document.languageId === 'ledge') {
                statusItem.show();
            } else {
                statusItem.hide();
            }
        })
    );

    if (vscode.window.activeTextEditor?.document.languageId === 'ledge') {
        statusItem.show();
    }
}

async function runFile() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active editor');
        return;
    }

    // Save the file first
    await editor.document.save();

    const config = vscode.workspace.getConfiguration('ledge');
    const pythonPath = config.get<string>('pythonPath', 'python');
    const clearOutput = config.get<boolean>('clearOutputOnRun', true);
    const showOutput = config.get<boolean>('showOutputOnRun', true);

    if (clearOutput) outputChannel.clear();
    if (showOutput) outputChannel.show(true);

    const filePath = editor.document.uri.fsPath;
    outputChannel.appendLine(`▶ Running ${path.basename(filePath)}\n`);

    const startTime = Date.now();

    const proc = cp.spawn(pythonPath, ['-m', 'ledge_lang.cli', 'run', filePath], {
        cwd: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath,
    });

    proc.stdout.on('data', (data: Buffer) => {
        outputChannel.append(data.toString());
    });

    proc.stderr.on('data', (data: Buffer) => {
        outputChannel.append(data.toString());
    });

    proc.on('close', (code: number) => {
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(3);
        outputChannel.appendLine(`\n──────────────────────────────────`);
        if (code === 0) {
            outputChannel.appendLine(`✓ Finished in ${elapsed}s`);
        } else {
            outputChannel.appendLine(`✗ Exited with code ${code} in ${elapsed}s`);
        }
    });

    proc.on('error', (err: Error) => {
        if (err.message.includes('ENOENT')) {
            vscode.window.showErrorMessage(
                `Python not found at '${pythonPath}'. ` +
                `Update the 'ledge.pythonPath' setting.`
            );
        } else {
            outputChannel.appendLine(`Error: ${err.message}`);
        }
    });
}

async function runSelection() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;

    const selection = editor.selection;
    if (selection.isEmpty) {
        vscode.window.showWarningMessage('No text selected');
        return;
    }

    const source = editor.document.getText(selection);
    const config = vscode.workspace.getConfiguration('ledge');
    const pythonPath = config.get<string>('pythonPath', 'python');

    outputChannel.clear();
    outputChannel.show(true);
    outputChannel.appendLine('▶ Running selection\n');

    // Write to temp file and run
    const tmpFile = path.join(require('os').tmpdir(), `ledge_selection_${Date.now()}.ledge`);
    require('fs').writeFileSync(tmpFile, source);

    const proc = cp.spawn(pythonPath, ['-m', 'ledge_lang.cli', 'run', tmpFile]);
    proc.stdout.on('data', (d: Buffer) => outputChannel.append(d.toString()));
    proc.stderr.on('data', (d: Buffer) => outputChannel.append(d.toString()));
    proc.on('close', () => require('fs').unlinkSync(tmpFile));
}

async function openRepl() {
    const config = vscode.workspace.getConfiguration('ledge');
    const pythonPath = config.get<string>('pythonPath', 'python');

    const terminal = vscode.window.createTerminal({
        name: 'Ledge REPL',
        shellPath: pythonPath,
        shellArgs: ['-m', 'ledge_lang.cli'],
    });
    terminal.show();
}

export function deactivate() {}
