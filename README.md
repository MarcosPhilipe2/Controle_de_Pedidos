# 📦 Controle de Pedidos

Sistema desktop desenvolvido em **Python** para cadastro, acompanhamento e gerenciamento de pedidos. O projeto nasceu com persistência em JSON e evoluiu para **SQLite**, adicionando autenticação de usuários, níveis de acesso, filtros, exportação, backup e geração de executável para Windows.

## 🎯 Objetivo do projeto

Criar uma aplicação simples e organizada para apoiar o controle operacional de pedidos, aplicando conceitos de desenvolvimento de software, banco de dados e melhoria de processos.

## ✨ Funcionalidades

- Login com usuários e níveis de acesso (`admin` e `operador`)
- Senhas protegidas com PBKDF2-HMAC-SHA256 e salt aleatório
- Cadastro, edição e exclusão de pedidos
- Alteração de status: `Pendente`, `Em transporte` e `Entregue`
- Busca por cliente ou cidade de destino
- Filtro por status e consulta por período
- Resumo dos pedidos e peso total
- Exportação dos dados para CSV
- Backup e restauração em JSON
- Migração automática de dados antigos em `pedidos.json`
- Geração de executável Windows com PyInstaller

## 🛠️ Tecnologias

- Python 3
- Tkinter
- SQLite
- JSON
- CSV
- PBKDF2 / `hashlib`
- PyInstaller
- Git e GitHub

## 🧱 Organização do projeto

```text
controle-de-pedidos/
├── main.py                  # Ponto de entrada da aplicação
├── gui.py                   # Interface gráfica e interação com o usuário
├── db.py                    # Conexão, esquema e migração do SQLite
├── auth.py                  # Login, usuários, papéis e senhas
├── regras_pedidos.py        # Validações e regras reutilizáveis
├── pedidos_repositorio.py   # Operações de leitura/escrita dos pedidos
├── build.bat                # Geração do executável no Windows
├── .gitignore
└── README.md
```

Fluxo simplificado:

```text
Interface (Tkinter)
        ↓
Regras / Autenticação
        ↓
Repositório de Pedidos
        ↓
SQLite local
```

## 🚀 Como executar

### Requisitos

- Python 3.9 ou superior
- Tkinter disponível na instalação do Python

O projeto utiliza apenas a biblioteca padrão do Python durante a execução.

### Passos

Clone o repositório e entre na pasta do projeto:

```bash
git clone URL_DO_REPOSITORIO
cd controle-de-pedidos
```

Execute:

```bash
python main.py
```

Na primeira execução, o sistema solicitará a criação do usuário administrador.

## 💾 Persistência dos dados

Os dados são armazenados localmente em `pedidos.db`. O arquivo é criado automaticamente e não deve ser versionado no GitHub.

Quando executado diretamente pelo Python, o banco fica na pasta do projeto. Quando a aplicação é gerada como `.exe`, o banco é criado ao lado do executável.

> **Observação sobre multiusuário:** esta versão utiliza SQLite local. Para uma futura versão com vários computadores acessando o mesmo conjunto de dados simultaneamente, a evolução recomendada é utilizar um banco servidor, como PostgreSQL, ou uma API centralizada. Não é recomendado compartilhar diretamente o arquivo SQLite por uma pasta de rede.

## 🔄 Evolução do armazenamento

A primeira versão do projeto utilizava `pedidos.json`. Conforme o sistema ganhou mais operações e estrutura, a persistência foi refatorada para SQLite.

A aplicação ainda reconhece um `pedidos.json` antigo e, quando o banco está vazio, pode migrar os registros existentes automaticamente. Essa evolução permitiu praticar conceitos de migração de dados e separação entre regras de negócio e persistência.

## 📤 Exportação e backup

O sistema cria automaticamente:

- `exportacoes/` para arquivos CSV;
- `backups/` para cópias de segurança em JSON.

Essas pastas são ignoradas pelo Git porque contêm dados gerados durante o uso da aplicação.

## 🪟 Gerar executável no Windows

O arquivo `build.bat` automatiza a criação do executável.

1. Instale o Python 3.9 ou superior.
2. Execute `build.bat`.
3. O script cria um ambiente de build, instala/atualiza o PyInstaller e gera `ControleDePedidos.exe`.

O ambiente e os arquivos temporários de build não são enviados para o GitHub.

## 🔐 Segurança

- Senhas não são armazenadas em texto puro.
- O sistema utiliza PBKDF2-HMAC-SHA256 com salt aleatório.
- A senha mínima é de 8 caracteres.
- As consultas SQL utilizam parâmetros em vez de concatenar entradas do usuário.
- A exportação CSV trata valores que poderiam ser interpretados como fórmulas por planilhas.

## 📌 Versão

**1.2.0 — versão preparada para portfólio**

## 👨‍💻 Autor

**Marcos Philipe Tavares**

Projeto desenvolvido como parte do meu portfólio de transição para tecnologia, unindo experiência em processos operacionais e logística com desenvolvimento de software e análise de dados.
