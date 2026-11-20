TASK: IMPLEMENTATION

Implemente a história selecionada no diretório de trabalho, usando as
especificações aprovadas contidas nos dados e em AgileSpec/stories/storyN/.
Leia AgileSpec/project/ para o contexto global, inclusive backlog e Definition
of Done. Leia o código existente e as instruções de agente do projeto.

INPUT_JSON: ${data}

Siga acceptance.md, design.md e views.md/tables.md quando presentes.
Preserve funcionalidades existentes e evite mudanças sem relação com a história.
Organize seu próprio trabalho. Implemente e execute testes automatizados para
Normal Case e Edge Cases. Examine o estado atual antes de editar: uma retomada
pode repetir esta chamada. Não faça commits, pushes ou deploys.

Não altere especificações globais, especificações da história ou o estado do
backlog. Se houver conflito ou decisão importante ausente, pare e relate status
blocked, para esclarecimento humano e revisão das especificações pelo workflow.

Retorne apenas JSON válido com todos estes campos:
{"status":"ready","summary":"mudanças e testes executados/resultados",
"manual_validation":"passos reproduzíveis de validação humana",
"limitations":[],"pending_dod":[],"consolidation_context":"arquivos de código/teste relevantes e decisões efetivamente implementadas"}

status pode ser ready ou blocked. limitations e pending_dod são listas de texto.
Relate honestamente limitações, testes não executados e critérios pendentes.
Não declare validação humana ou consolidação como já aprovadas: ainda ocorrerão
nas próximas etapas. Aguarde a revisão humana antes da conclusão da história.
