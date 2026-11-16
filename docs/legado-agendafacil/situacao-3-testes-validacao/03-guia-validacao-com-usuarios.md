# 3. Guia da validação com usuários (5 testadores)

> "Oferecer a sua solução para cinco colegas de curso ou profissionais da área para que possam
> testá-la. (...) criar um formulário para que possam ser descritos os bugs, sugestões de melhoria
> e colocar snapshots das telas com erros."

## 3.1 O formulário (template do laudo)

O formulário de laudo está **dentro do próprio sistema**, em `/feedback/`. Ele não exige login,
tem os campos mínimos pedidos no enunciado e aceita até 3 prints:

| Campo exigido pelo enunciado | Campo no formulário |
|---|---|
| Nome de quem testou | "Seu nome" |
| Data do teste | "Data do teste" (já vem com a data de hoje) |
| O que testou e funcionou | "O que você testou e FUNCIONOU" |
| O que testou e não funcionou (e o que deve ser corrigido) | "O que você testou e NÃO funcionou (e o que deve ser corrigido)" |
| Funcionalidade não testada (por que faltou) | "Funcionalidades que você NÃO testou (e por quê)" |
| *(extra)* Sugestões de melhoria | "Sugestões de melhoria" |
| *(extra)* Prints das telas com erro | Upload de até 3 imagens |
| *(extra)* Nota geral | 1 a 5 |

Se algum testador preferir não usar o sistema para isso, use o template em papel/Word abaixo
(seção 3.4).

## 3.2 Passo a passo

1. Publique o sistema (ver `docs/situacao-2-desenvolvimento/03-instalacao-e-implantacao.md`).
2. Escolha **5 testadores** ("dublês de usuário"): colegas de curso ou profissionais da área.
   Se possível, inclua alguém sem perfil técnico.
3. Envie a mensagem da seção 3.3 para cada um.
4. Acompanhe os laudos em **Feedbacks de teste** (perfil administrador).
5. Para cada laudo, registre a **tratativa** (Corrigido / Em análise / Não será corrigido +
   explicação).
6. Faça as correções pertinentes, com um commit por correção. Cite o laudo na mensagem do
   commit, por exemplo `fix: telefone fixo aceito no cadastro (laudo #3)`.
7. Gere o PDF: **Feedbacks de teste → Relatório para PDF → Imprimir / Salvar em PDF**, e salve
   como `docs/situacao-3-testes-validacao/feedbacks/laudos-testadores.pdf`.
8. Atualize o [laudo de qualidade](04-laudo-de-qualidade.md) e o [registro de mudanças](05-registro-de-mudancas.md).
9. Grave o vídeo das mudanças (até 5 min — roteiro em `docs/situacao-2-desenvolvimento/04-roteiro-do-video.md`).

## 3.3 Mensagem para enviar aos testadores

```text
Oi, <nome>! Tudo bem?

Estou finalizando meu Projeto Integrador (Engenharia de Software) e preciso de 15–20 minutos
seus para testar o sistema como se você fosse a recepcionista de um salão.

🔗 Sistema: <link do sistema publicado>
👤 Login: atendente@agendafacil.com  |  senha: Agenda@2026
   (para testar a área de gerente: admin@agendafacil.com, mesma senha)

Sugestões do que testar:
1. Cadastrar um cliente (tente também telefone e CPF errados)
2. Fazer um agendamento escolhendo um horário livre
3. Tentar marcar o mesmo profissional no mesmo horário (o sistema deve impedir)
4. Confirmar, concluir ou cancelar um agendamento
5. Usar pelo celular

📝 No final, preencha o laudo (pode anexar prints dos erros):
<link do sistema>/feedback/

Pode ser sincero(a): erros encontrados me ajudam muito! Obrigado(a)! 🙏
```

## 3.4 Template do laudo (versão para papel/Word)

```text
LAUDO DE TESTE — AgendaFácil
Projeto Integrador Transdisciplinar em Engenharia de Software II

Nome de quem testou: ______________________________________________
Perfil: ( ) Colega de curso  ( ) Profissional de TI  ( ) Usuário final  ( ) Outro
Data do teste: ____/____/________
Dispositivo/navegador: ____________________________________________

1. O QUE TESTEI E FUNCIONOU (descreva cada funcionalidade):
__________________________________________________________________

2. O QUE TESTEI E NÃO FUNCIONOU (descreva o passo a passo, o que aconteceu,
   o que você esperava e o que deve ser corrigido):
__________________________________________________________________

3. FUNCIONALIDADES QUE NÃO TESTEI (e por quê: faltou tempo, não encontrei,
   não existe no sistema...):
__________________________________________________________________

4. SUGESTÕES DE MELHORIA:
__________________________________________________________________

5. NOTA GERAL (1 = muito ruim, 5 = excelente):  1  2  3  4  5

6. PRINTS: anexe as imagens das telas com erro (numere e cite no item 2).

Assinatura: ______________________________
```
