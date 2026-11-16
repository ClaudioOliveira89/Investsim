# 3. Modelagem UML (revisada)

> Os diagramas estão em **Mermaid**: o GitHub os desenha automaticamente e eles ficam
> versionados como texto junto com o código. Para exportar como imagem, use
> <https://mermaid.live> (cole o bloco e baixe em PNG/SVG).

## 3.1 Diagrama de casos de uso

```mermaid
flowchart LR
    AT([👤 Atendente])
    AD([👤 Administrador])
    TE([👤 Testador])

    subgraph Sistema AgendaFácil
        UC01((Fazer login / sair))
        UC02((Alterar a própria senha))
        UC03((Manter clientes))
        UC04((Consultar histórico do cliente))
        UC05((Agendar atendimento))
        UC06((Consultar horários livres))
        UC07((Reagendar))
        UC08((Confirmar / concluir / registrar falta))
        UC09((Cancelar com motivo))
        UC10((Ver agenda do dia e lista com filtros))
        UC11((Ver painel de indicadores))
        UC12((Manter serviços))
        UC13((Manter profissionais))
        UC14((Manter usuários))
        UC15((Enviar laudo de teste))
        UC16((Tratar feedbacks e gerar relatório))
    end

    AT --- UC01 & UC02 & UC03 & UC04 & UC05 & UC07 & UC08 & UC09 & UC10 & UC11
    AD --- UC12 & UC13 & UC14 & UC16
    AD -. herda tudo do .-> AT
    TE --- UC15
    UC05 -. «include» .-> UC06
    UC07 -. «include» .-> UC06
```

**Especificação do caso de uso principal — UC05 Agendar atendimento**

| Item | Descrição |
|---|---|
| Ator | Atendente (ou Administrador) |
| Pré-condição | Usuário autenticado; existe ao menos um cliente, um serviço e um profissional ativos |
| Fluxo principal | 1. Atendente abre "Novo agendamento". 2. Escolhe o cliente. 3. Escolhe o profissional; o sistema mostra só os serviços que ele realiza (RN05). 4. Escolhe o serviço e a data. 5. O sistema consulta e exibe os horários livres (UC06). 6. Atendente clica em um horário; o resumo mostra duração, término e valor. 7. Atendente confirma. 8. O sistema valida RN01–RN06, grava com status "Agendado" e valor congelado (RN10) e mostra o detalhe com a mensagem de sucesso. |
| Fluxo alternativo A1 | Cliente não cadastrado: o atendente usa "Cadastrar novo cliente" → "Salvar e agendar", que volta para o agendamento com o cliente já selecionado. |
| Fluxo de exceção E1 | Horário ocupado ou fora do expediente: o sistema não grava e mostra a mensagem junto ao campo "Horário", mantendo os dados preenchidos. |
| Fluxo de exceção E2 | Dois atendentes salvam o mesmo horário ao mesmo tempo: o PostgreSQL rejeita o segundo (*exclusion constraint*) e o sistema exibe "Esse horário acabou de ser ocupado…". |
| Pós-condição | Horário ocupado na agenda do profissional; aparece no painel e no histórico do cliente. |

## 3.2 Diagrama de classes de domínio

```mermaid
classDiagram
    direction LR
    class Usuario {
        +int id
        +str nome
        +str email
        +str perfil
        +bool ativo
        +definir_senha(senha)
        +verificar_senha(senha) bool
        +is_admin() bool
    }
    class Cliente {
        +int id
        +str nome
        +str telefone
        +str email
        +str cpf
        +date data_nascimento
        +str observacoes
    }
    class Profissional {
        +int id
        +str nome
        +str especialidade
        +str telefone
        +bool ativo
        +realiza(servico) bool
    }
    class Servico {
        +int id
        +str nome
        +int duracao_min
        +Decimal preco
        +bool ativo
    }
    class Agendamento {
        +int id
        +datetime inicio
        +datetime fim
        +str status
        +Decimal valor
        +str observacoes
        +str motivo_cancelamento
        +proximos_status() list
        +editavel() bool
    }
    class StatusAgendamento {
        <<enumeration>>
        AGENDADO
        CONFIRMADO
        CONCLUIDO
        CANCELADO
        NAO_COMPARECEU
        +TRANSICOES
    }
    class FeedbackTeste {
        +int id
        +str nome_testador
        +date data_teste
        +str funcionou
        +str nao_funcionou
        +str nao_testado
        +int nota
        +str status
        +str tratativa
    }
    class FeedbackAnexo {
        +int id
        +str nome_arquivo
        +str tipo_mime
        +bytes conteudo
    }

    Cliente "1" --> "0..*" Agendamento : possui
    Profissional "1" --> "0..*" Agendamento : atende
    Servico "1" --> "0..*" Agendamento : é prestado em
    Usuario "0..1" --> "0..*" Agendamento : registrou
    Profissional "1..*" -- "1..*" Servico : realiza
    Agendamento ..> StatusAgendamento
    FeedbackTeste "1" *-- "0..3" FeedbackAnexo : prints
```

## 3.3 Diagrama de classes da arquitetura (MVC em camadas)

```mermaid
classDiagram
    direction TB
    namespace Controller {
        class AgendamentosController {
            +listar()
            +agenda()
            +novo()
            +editar(id)
            +alterar_status(id)
        }
        class ApiController {
            +horarios() JSON
        }
    }
    namespace Model_Servicos {
        class AgendaService {
            +criar_agendamento(...) Agendamento
            +reagendar(...) Agendamento
            +alterar_status(...) Agendamento
            +horarios_disponiveis(...) list
            +validar_horario(...) datetime
        }
        class RegraNegocioError {
            +str mensagem
            +str campo
        }
    }
    namespace View {
        class FormHtml["agendamentos/form.html"]
        class AgendamentoJs["agendamento.js"]
    }
    AgendamentosController --> AgendaService : usa
    ApiController --> AgendaService : usa
    AgendaService ..> RegraNegocioError : lança
    AgendamentosController --> FormHtml : renderiza
    AgendamentoJs ..> ApiController : fetch /api/horarios
```

## 3.4 Diagrama de sequência — agendar atendimento

```mermaid
sequenceDiagram
    autonumber
    actor A as Atendente
    participant V as View (form.html + agendamento.js)
    participant API as Controller API (/api/horarios)
    participant C as Controller Agendamentos
    participant S as AgendaService (Model)
    participant DB as PostgreSQL

    A->>V: escolhe profissional, serviço e data
    V->>V: filtra serviços do profissional (RN05)
    V->>API: GET /api/horarios?profissional_id&servico_id&data
    API->>S: horarios_disponiveis()
    S->>DB: SELECT agendamentos ativos do dia
    DB-->>S: ocupados
    S-->>API: ["08:00", "10:00", ...]
    API-->>V: JSON
    V-->>A: botões de horários livres + resumo
    A->>V: clica em 14:00 e confirma
    V->>C: POST /agendamentos/novo (com token CSRF)
    C->>C: valida formulário (WTForms)
    C->>S: criar_agendamento()
    S->>S: validar_horario() — RN01 a RN06
    alt regra violada
        S-->>C: RegraNegocioError(campo="hora")
        C-->>A: formulário com a mensagem no campo
    else tudo válido
        S->>DB: INSERT agendamento (valor congelado — RN10)
        alt conflito simultâneo
            DB-->>S: violação ex_agendamento_conflito_profissional
            S-->>C: RegraNegocioError("acabou de ser ocupado")
            C-->>A: mensagem amigável
        else sucesso
            DB-->>S: id
            S-->>C: Agendamento
            C-->>A: redirect para o detalhe + "Agendamento criado"
        end
    end
```

## 3.5 Diagrama de atividades — atendimento do início ao fim

```mermaid
flowchart TD
    I([Início]) --> B{Cliente já cadastrado?}
    B -- Não --> CC[Cadastrar cliente] --> AG
    B -- Sim --> AG[Escolher profissional, serviço e data]
    AG --> H{Há horário livre?}
    H -- Não --> OD[Escolher outra data ou profissional] --> AG
    H -- Sim --> SV[Selecionar horário e salvar]
    SV --> V{Regras válidas?}
    V -- Não --> MSG[Mostrar erro no campo] --> AG
    V -- Sim --> AGD[(Status: Agendado)]
    AGD --> CF{Cliente confirmou?}
    CF -- Pediu para desmarcar --> CAN[Cancelar com motivo] --> F1([Horário liberado])
    CF -- Sim --> CON[(Status: Confirmado)]
    CON --> D{No dia do atendimento}
    D -- Compareceu --> CONC[Marcar como concluído] --> F2([Entra no faturamento])
    D -- Faltou --> NC[Registrar falta] --> F3([Histórico de faltas])
    D -- Desmarcou --> CAN
```

## 3.6 Diagrama de estados — Agendamento

```mermaid
stateDiagram-v2
    [*] --> Agendado : criar_agendamento()
    Agendado --> Confirmado : confirmar presença
    Agendado --> Cancelado : cancelar (motivo obrigatório)
    Confirmado --> Concluido : concluir [após o início]
    Confirmado --> NaoCompareceu : registrar falta [após o início]
    Confirmado --> Cancelado : cancelar (motivo obrigatório)
    Concluido --> [*]
    Cancelado --> [*]
    NaoCompareceu --> [*]

    note right of Agendado
        Agendado e Confirmado ocupam o horário
        e podem ser reagendados.
    end note
```

## 3.7 Diagrama de implantação

```mermaid
flowchart LR
    subgraph Cliente
        N[Navegador<br/>desktop ou celular]
    end
    subgraph Hospedagem["Hospedagem (Render)"]
        G[Gunicorn<br/>Flask app MVC]
    end
    subgraph Banco["PostgreSQL gerenciado"]
        P[(agendafacil)]
    end
    N -- HTTPS --> G
    G -- psycopg 3 / TLS --> P
```
