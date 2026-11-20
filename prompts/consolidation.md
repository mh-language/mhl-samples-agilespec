TASK: CONSOLIDATION

Consolide a história implementada, testada e validada nas especificações globais.
Leia o código relevante no diretório de trabalho e compare-o às especificações
da história e do projeto incluídas nos dados. A aprovação humana da implementação
e a verificação automatizada já ocorreram nesta rodada.

INPUT_JSON: ${data}

Use esta correspondência, ignorando documentos opcionais ausentes:
- acceptance.md -> backlog.md: ajuste a descrição se necessário, mantendo [ ].
- design.md -> architecture.md: incorpore decisões arquiteturais globais.
- views.md -> ui.md: incorpore estrutura e convenções globais de interface.
- tables.md -> database.md: incorpore mudanças de esquema.

Mantenha documentos concisos e consistentes com o código implementado. Não copie
especificações inteiras nem misture detalhes locais com decisões globais.
Não altere código, especificações da história ou qualquer arquivo. Não modifique
definition-of-done.md. Preserve todos os IDs e estados de checkbox do backlog.

Retorne apenas JSON válido:
{"files":{"backlog.md":"...","architecture.md":"..."},"discrepancies":[],"pending_dod":[]}
Inclua ui.md e database.md em files somente quando a história possuir os respectivos
views.md e tables.md. Inclua o documento completo atualizado em cada valor.

Relate discrepâncias entre código e especificações em discrepancies; o workflow
interromperá a consolidação. pending_dod deve conter critérios ainda não atendidos,
exceto a aprovação desta consolidação e a marcação final, que ocorrerão a seguir.
A história permanece desmarcada até aprovação humana da consolidação e confirmação
de todos os critérios da Definition of Done.
