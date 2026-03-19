import * as vscode from 'vscode';
import { ScriptParser } from './scriptParser';

export function activate(context: vscode.ExtensionContext) {
    console.log('Live Script Editor is now active!');

    const generateRandomCommand = vscode.commands.registerCommand(
        'liveScript.generateRandom',
        async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('没有打开的编辑器');
                return;
            }

            const selection = editor.selection;
            const text = selection.isEmpty 
                ? editor.document.getText() 
                : editor.document.getText(selection);

            if (!text.trim()) {
                vscode.window.showErrorMessage('没有可处理的文本');
                return;
            }

            const generatedText = ScriptParser.generateRandom(text);
            const count = ScriptParser.countCombinations(text);
            
            const config = vscode.workspace.getConfiguration('liveScript');
            const autoCopy = config.get<boolean>('autoCopy', true);
            
            if (autoCopy) {
                await vscode.env.clipboard.writeText(generatedText);
            }

            const items: vscode.QuickPickItem[] = [
                { label: '$(copy) 复制到剪贴板', description: '复制生成的文案' },
                { label: '$(replace) 替换原文', description: '用生成的文案替换原文本' },
                { label: '$(new-file) 新建文件', description: '在新文件中打开' },
                { label: '$(info) 查看统计', description: `共 ${count} 种组合` }
            ];

            const result = await vscode.window.showQuickPick(items, {
                placeHolder: generatedText
            });

            if (result) {
                switch (result.label) {
                    case '$(copy) 复制到剪贴板':
                        await vscode.env.clipboard.writeText(generatedText);
                        vscode.window.showInformationMessage('已复制到剪贴板');
                        break;
                    case '$(replace) 替换原文':
                        editor.edit(editBuilder => {
                            const range = selection.isEmpty 
                                ? new vscode.Range(
                                    editor.document.positionAt(0),
                                    editor.document.positionAt(editor.document.getText().length)
                                )
                                : selection;
                            editBuilder.replace(range, generatedText);
                        });
                        break;
                    case '$(new-file) 新建文件':
                        const doc = await vscode.workspace.openTextDocument({
                            content: generatedText,
                            language: 'plaintext'
                        });
                        vscode.window.showTextDocument(doc);
                        break;
                    case '$(info) 查看统计':
                        const groups = ScriptParser.getOptionGroups(text);
                        let infoText = `总组合数: ${count}\n\n选项组详情:\n`;
                        groups.forEach((g, i) => {
                            infoText += `${i + 1}. ${g.match}\n   选项: ${g.choices.join(' | ')}\n`;
                        });
                        const infoDoc = await vscode.workspace.openTextDocument({
                            content: infoText,
                            language: 'plaintext'
                        });
                        vscode.window.showTextDocument(infoDoc);
                        break;
                }
            }
        }
    );

    const generateMultipleCommand = vscode.commands.registerCommand(
        'liveScript.generateMultiple',
        async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('没有打开的编辑器');
                return;
            }

            const selection = editor.selection;
            const text = selection.isEmpty 
                ? editor.document.getText() 
                : editor.document.getText(selection);

            if (!text.trim()) {
                vscode.window.showErrorMessage('没有可处理的文本');
                return;
            }

            const config = vscode.workspace.getConfiguration('liveScript');
            const defaultCount = config.get<number>('defaultGenerateCount', 5);
            
            const countInput = await vscode.window.showInputBox({
                prompt: '请输入生成数量',
                value: String(defaultCount),
                validateInput: (value) => {
                    const num = parseInt(value);
                    if (isNaN(num) || num < 1 || num > 100) {
                        return '请输入1-100之间的数字';
                    }
                    return null;
                }
            });

            if (!countInput) {
                return;
            }

            const count = parseInt(countInput);
            const results = ScriptParser.generateMultiple(text, count);
            const totalCombinations = ScriptParser.countCombinations(text);
            
            const outputContent = results.join('\n\n---\n\n');
            
            const items: vscode.QuickPickItem[] = [
                { label: '$(new-file) 新建文件查看', description: `生成 ${count} 条文案` },
                { label: '$(copy) 复制全部', description: '复制所有生成的文案' },
                { label: '$(list) 选择复制', description: '选择一条复制' }
            ];

            const result = await vscode.window.showQuickPick(items, {
                placeHolder: `已生成 ${count} 条文案 (总组合数: ${totalCombinations})`
            });

            if (result) {
                switch (result.label) {
                    case '$(new-file) 新建文件查看':
                        const doc = await vscode.workspace.openTextDocument({
                            content: outputContent,
                            language: 'plaintext'
                        });
                        vscode.window.showTextDocument(doc);
                        break;
                    case '$(copy) 复制全部':
                        await vscode.env.clipboard.writeText(outputContent);
                        vscode.window.showInformationMessage(`已复制 ${count} 条文案到剪贴板`);
                        break;
                    case '$(list) 选择复制':
                        const pickItems: vscode.QuickPickItem[] = results.map((r, i) => ({
                            label: `第 ${i + 1} 条`,
                            description: r.substring(0, 50) + (r.length > 50 ? '...' : ''),
                            detail: r
                        }));
                        const picked = await vscode.window.showQuickPick(pickItems, {
                            placeHolder: '选择一条文案复制'
                        });
                        if (picked) {
                            await vscode.env.clipboard.writeText(picked.detail || '');
                            vscode.window.showInformationMessage('已复制到剪贴板');
                        }
                        break;
                }
            }
        }
    );

    const previewAllCommand = vscode.commands.registerCommand(
        'liveScript.previewAll',
        async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('没有打开的编辑器');
                return;
            }

            const selection = editor.selection;
            const text = selection.isEmpty 
                ? editor.document.getText() 
                : editor.document.getText(selection);

            if (!text.trim()) {
                vscode.window.showErrorMessage('没有可处理的文本');
                return;
            }

            const totalCombinations = ScriptParser.countCombinations(text);
            
            if (totalCombinations > 10000) {
                const confirm = await vscode.window.showWarningMessage(
                    `组合数量过多 (${totalCombinations})，是否只生成前1000条？`,
                    '确认',
                    '取消'
                );
                if (confirm !== '确认') {
                    return;
                }
            }

            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: '生成所有组合...',
                cancellable: false
            }, async (progress) => {
                progress.report({ increment: 0 });
                
                const combinations = ScriptParser.getAllCombinations(text);
                const outputContent = `共 ${combinations.length} 种组合 (理论值: ${totalCombinations})\n${'='.repeat(50)}\n\n` + 
                    combinations.join('\n\n---\n\n');
                
                const doc = await vscode.workspace.openTextDocument({
                    content: outputContent,
                    language: 'plaintext'
                });
                vscode.window.showTextDocument(doc);
                
                progress.report({ increment: 100 });
            });
        }
    );

    context.subscriptions.push(generateRandomCommand);
    context.subscriptions.push(generateMultipleCommand);
    context.subscriptions.push(previewAllCommand);
}

export function deactivate() {}
