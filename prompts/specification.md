TASK: SPECIFICATION

Prepare ou revise as especificações da história selecionada, orientadas pelas
especificações globais e pelo feedback humano. Mantenha-as leves e suficientes
para implementação autônoma. Preserve decisões corretas existentes. Questões
em aberto devem ficar explícitas para a revisão humana.

INPUT_JSON: ${data}

Retorne apenas JSON válido: {"files":{"acceptance.md":"...","design.md":"..."}}.
Inclua views.md quando houver mudança de UI ou especificação de views existente;
inclua tables.md quando houver mudança de banco ou especificação de tables existente.
Não inclua outros nomes.

acceptance.md deve conter seções `Normal Case` e `Edge Cases`, com critérios
observáveis e verificáveis. design.md deve conter decisões locais, APIs,
funções, bibliotecas e serviços necessários, respeitando architecture.md.
views.md descreve telas, componentes e interações; tables.md descreve mudanças
de esquema e restrições. Não imponha uma lista de tarefas ao agente implementador.

Não altere arquivos, código ou documentação global. O MHL só gravará os
documentos da história depois da aprovação humana desta rodada.
