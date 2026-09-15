// Runs inside a disposable VS Code extension-test host, using the installed Zoo.
const vscode = require('vscode');
const fs = require('fs');
exports.run = async function () {
  const resultPath = process.env.NOERELAY_ZOO_RESULT;
  let api;
  try {
    const ext = vscode.extensions.getExtension('zoocodeorganization.zoo-code');
    if (!ext) throw new Error('Zoo Code extension is not installed in this test host');
    api = await ext.activate();
    await vscode.commands.executeCommand('zoo-code.importSettings', process.env.NOERELAY_ZOO_SETTINGS);
    const profile = api.getProfileEntry('NoeRelay');
    if (!profile) throw new Error('Generated Zoo profile was not imported');
    await api.setActiveProfile('NoeRelay');
    const config = JSON.parse(fs.readFileSync(process.env.NOERELAY_ZOO_SETTINGS, 'utf8')).providerProfiles.apiConfigs.NoeRelay;
    const id = await api.startNewTask({
      text: 'Read the file nonce.txt in the current workspace using your file tool. Then complete the task with its exact contents. Do not modify any files.',
      configuration: {...config, mode: 'code', autoApprovalEnabled: true,
        alwaysAllowReadOnly: true, alwaysAllowReadOnlyOutsideWorkspace: false,
        alwaysAllowWrite: false, alwaysAllowExecute: false, alwaysAllowMcp: false,
        alwaysAllowSubtasks: false, alwaysAllowFollowupQuestions: false,
        currentApiConfigName: 'NoeRelay', telemetrySetting: 'disabled'},
    });
    // Zoo waits for user acknowledgement after attempt_completion; observing
    // its persisted completion is sufficient, without approving further work.
    const storage = process.env.NOERELAY_ZOO_STORAGE;
    const deadline = Date.now() + 240000;
    let completed = false;
    while (Date.now() < deadline) {
      const uiPath = `${storage}/tasks/${id}/ui_messages.json`;
      if (fs.existsSync(uiPath)) {
        const ui = JSON.parse(fs.readFileSync(uiPath, 'utf8'));
        if (ui.some(m => m.say === 'completion_result' && !m.partial)) { completed = true; break; }
      }
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    if (!completed) throw new Error('Zoo tool test timed out');
    const historyLength = await api.getTaskApiConversationHistoryLength(id);
    const expected = fs.readFileSync(process.env.NOERELAY_ZOO_NONCE, 'utf8').trim();
    // Persisted history is independent of the model's final success claim.
    const history = fs.readFileSync(`${storage}/tasks/${id}/api_conversation_history.json`, 'utf8');
    const messages = JSON.parse(history);
    const final = JSON.stringify(messages.slice(-2));
    const readToolUsed = history.includes('read_file') && history.includes('tool_result');
    const passed = historyLength >= 3 && final.includes(expected) && readToolUsed;
    fs.writeFileSync(resultPath, JSON.stringify({passed, version: ext.packageJSON.version,
      historyLength, readToolUsed, nonceVerified: final.includes(expected)}, null, 2));
    if (!passed) throw new Error('Zoo did not complete a verified file-tool round trip');
  } catch (error) {
    if (!fs.existsSync(resultPath)) fs.writeFileSync(resultPath, JSON.stringify({passed:false,error:String(error)}));
    throw error;
  } finally {
    if (api) await api.cancelCurrentTask().catch(() => {});
  }
};
