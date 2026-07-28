/**
 * appscript_trigger.gs
 * ─────────────────────
 * Google Apps Script para acionar o GitHub Actions workflow
 * do Canal Polêmico (FUT ZONA @futzona2026).
 *
 * ─── COMO CONFIGURAR ───────────────────────────────────────────────────────
 * 1. No Apps Script (script.google.com), abra as Configurações do Projeto
 * 2. Em "Propriedades de script", adicione:
 *    - GITHUB_TOKEN    → seu Personal Access Token com permissão "repo"
 *    - GITHUB_OWNER    → seu usuário GitHub (ex: "seuusuario")
 *    - GITHUB_REPO     → nome do repositório (ex: "canal-polemico")
 *
 * 3. Para agendar automaticamente:
 *    - Vá em Acionadores (relógio) > Adicionar acionador
 *    - Função: dispararWorkflow
 *    - Tipo de evento: Temporizador baseado em tempo
 *    - Intervalo: a cada 8 horas (3x/dia)
 * ────────────────────────────────────────────────────────────────────────────
 */

// ─── Configurações (via PropertiesService para segurança) ─────────────────
function _getConfig() {
  const props = PropertiesService.getScriptProperties();
  return {
    token: props.getProperty("GITHUB_TOKEN"),
    owner: props.getProperty("GITHUB_OWNER"),
    repo:  props.getProperty("GITHUB_REPO") || "canal-polemico",
    branch: props.getProperty("GITHUB_BRANCH") || "main",
  };
}


// ─── Função principal: aciona o workflow no GitHub ─────────────────────────
function dispararWorkflow() {
  const config = _getConfig();

  if (!config.token || !config.owner) {
    Logger.log("❌ ERRO: Configure GITHUB_TOKEN e GITHUB_OWNER nas propriedades do script.");
    return;
  }

  const url = `https://api.github.com/repos/${config.owner}/${config.repo}/actions/workflows/main.yml/dispatches`;

  const payload = JSON.stringify({
    ref: config.branch,
    inputs: {
      motivo: "agendamento_apps_script_" + new Date().toISOString()
    }
  });

  const options = {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${config.token}`,
      "Accept":        "application/vnd.github+json",
      "Content-Type":  "application/json",
      "X-GitHub-Api-Version": "2022-11-28",
    },
    payload: payload,
    muteHttpExceptions: true,
  };

  try {
    const response = UrlFetchApp.fetch(url, options);
    const codigo   = response.getResponseCode();

    if (codigo === 204) {
      Logger.log("✅ Workflow disparado com sucesso! " + new Date().toLocaleString("pt-BR"));
      _registrarLog("SUCESSO", "Workflow disparado");
    } else {
      const corpo = response.getContentText();
      Logger.log(`⚠️  Resposta inesperada: ${codigo}\n${corpo}`);
      _registrarLog("AVISO", `Código ${codigo}: ${corpo.substring(0, 200)}`);
    }
  } catch (e) {
    Logger.log("❌ Erro ao chamar GitHub API: " + e.toString());
    _registrarLog("ERRO", e.toString());
  }
}


// ─── Verificar status do último workflow ──────────────────────────────────
function verificarUltimoWorkflow() {
  const config = _getConfig();

  const url = `https://api.github.com/repos/${config.owner}/${config.repo}/actions/runs?per_page=1&workflow_id=main.yml`;

  const options = {
    method: "GET",
    headers: {
      "Authorization": `Bearer ${config.token}`,
      "Accept":        "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
    },
    muteHttpExceptions: true,
  };

  try {
    const response = UrlFetchApp.fetch(url, options);
    const data     = JSON.parse(response.getContentText());
    const runs     = data.workflow_runs || [];

    if (runs.length > 0) {
      const ultimo = runs[0];
      Logger.log(`\n📊 Último workflow:`);
      Logger.log(`   Status    : ${ultimo.status}`);
      Logger.log(`   Conclusão : ${ultimo.conclusion}`);
      Logger.log(`   Iniciado  : ${ultimo.created_at}`);
      Logger.log(`   URL       : ${ultimo.html_url}`);
    } else {
      Logger.log("Nenhuma execução encontrada.");
    }
  } catch (e) {
    Logger.log("Erro: " + e.toString());
  }
}


// ─── Log em planilha Google Sheets (opcional) ─────────────────────────────
function _registrarLog(status, mensagem) {
  try {
    // Tenta registrar em uma planilha chamada "Log Canal Polêmico"
    // Se não existir, pula silenciosamente
    const planilhas = SpreadsheetApp.openByName("Log Canal Polêmico");
    const aba = planilhas.getActiveSheet();
    aba.appendRow([
      new Date(),
      status,
      mensagem,
    ]);
  } catch (e) {
    // Planilha não configurada — não é obrigatório
  }
}


// ─── Criar acionadores automáticos (execute UMA VEZ manualmente) ──────────
function configurarAcionadores() {
  // Remove acionadores existentes para evitar duplicatas
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(t => {
    if (t.getHandlerFunction() === "dispararWorkflow") {
      ScriptApp.deleteTrigger(t);
    }
  });

  // Cria acionadores: 09:00, 15:00 e 21:00 BRT
  const horarios = [9, 15, 21];
  horarios.forEach(hora => {
    ScriptApp.newTrigger("dispararWorkflow")
      .timeBased()
      .atHour(hora)
      .everyDays(1)
      .inTimezone("America/Sao_Paulo")
      .create();
    Logger.log(`✅ Acionador criado: ${hora}:00 BRT`);
  });

  Logger.log("\n🔥 3 acionadores configurados para o Canal Polêmico!");
  Logger.log("   O workflow será disparado às 9h, 15h e 21h (BRT)");
}
