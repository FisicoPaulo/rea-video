// Backend falso do Tauri: deixa a interface real do ÉguaTeX rodar no navegador para gravar telas.
(() => {
  const P = '/home/curupira/Documentos/EguaTex/a-pororoca-do-guama';
  const S = window.__CENA__ || {};
  const arquivos = { [P + '/main.tex']: S.tex || '' };
  const cbs = {}; let n = 1;
  window.__emitir = (evento, payload) => {
    for (const [id, c] of Object.entries(cbs)) if (c.evento === evento) c.fn({ event: evento, id: +id, payload });
  };
  const ouvintes = {};
  async function invoke(cmd, a = {}) {
    (window.__log = window.__log || []).push(cmd);
    switch (cmd) {
      case 'plugin:event|listen': { const id = a.handler; ouvintes[id] = a.event; cbs[id] = { evento: a.event, fn: window['_' + id] }; return id; }
      case 'plugin:event|unlisten': return null;
      case 'cmd_listar_arvore': return [{ nome: 'main.tex', tipo: 'arquivo', caminho: '/main.tex', tamanho: 900 }];
      case 'cmd_ler_arquivo': case 'cmd_ler': return arquivos[P + '/main.tex'];
      case 'cmd_salvar_arquivo': case 'cmd_salvar': return null;
      case 'cmd_detectar_motores': return { distribuicao: 'TinyTeX', motores: [{ nome: 'pdflatex' }, { nome: 'xelatex' }, { nome: 'lualatex' }] };
      case 'cmd_detectar_principal': return 'main.tex';
      case 'cmd_pasta_projetos': return '/home/curupira/Documentos/EguaTex';
      case 'cmd_modificacao_projetos': return {};
      case 'cmd_compilar_completo': {
        await new Promise(r => setTimeout(r, S.tempoCompilar || 900));
        if (S.erro) return { sucesso: false, pdf: null, log: S.erro.log, erros: S.erro.erros, tempo_ms: 812, motor_usado: 'pdflatex' };
        return { sucesso: true, pdf: P + '/main.pdf', log: 'Output written on main.pdf (1 page).', erros: [], tempo_ms: 1340, motor_usado: 'pdflatex', motor_lembrar: null };
      }
      case 'cmd_ler_pdf_bytes': case 'cmd_ler_bytes_projeto': { const r = await fetch(S.pdfUrl); return await r.arrayBuffer(); }
      case 'cmd_synctex_disponivel': return false;
      case 'cmd_ia_chave_status': return !!S.ia;
      case 'cmd_ia_carregar_config': return { ativa: !!S.ia, provedor: 'gemini', modelo: 'gemini-2.5-flash', nivel: 'ler' };
      case 'cmd_ia_modelos': return ['gemini-2.5-flash'];
      case 'cmd_versao': return '1.0.3';
      case 'cmd_ortografia_verificar': return [];
      case 'cmd_drive_info': return { conectado: false, email: null, nome: null };
      case 'cmd_versoes_listar': return [];
      case 'cmd_ia_google_info': return { conectado: false, configurado: true, email: '', nome: '', foto: '', aviso: '' };
      case 'cmd_drive_projeto': return null;
      case 'cmd_aviso_do_instalador': return null;
      case 'cmd_procurar_atualizacao': return null;
      case 'cmd_ia_agente': return window.__iaAgente ? window.__iaAgente(a) : null;
      default: return null;
    }
  }
  window.__TAURI_INTERNALS__ = {
    invoke,
    transformCallback(fn, once) { const id = n++; window['_' + id] = fn; return id; },
    unregisterCallback(id) { delete window['_' + id]; },
    convertFileSrc(p) { return p; },
    metadata: { currentWindow: { label: 'main' }, currentWebview: { label: 'main', windowLabel: 'main' } },
  };
  window.__TAURI_EVENT_PLUGIN_INTERNALS__ = { unregisterListener() {} };
  try {
    localStorage.setItem('eguatex.recentes', JSON.stringify([{ nome: 'A pororoca do Guamá', caminho: P, abertoEm: new Date().toISOString(), estado: 'ativo' }]));
    for (const [k, v] of Object.entries(S.localStorage || {})) localStorage.setItem(k, v);
  } catch (e) {}
})();
