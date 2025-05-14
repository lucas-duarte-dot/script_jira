# Script de Criação de Issues no Jira via Google Sheets

Este projeto automatiza a criação de issues no Jira a partir de planilhas no Google Drive, utilizando uma conta de serviço do Google e integração com a API do Jira.

## Funcionalidades
- Lê planilhas de uma pasta específica no Google Drive
- Cria issues no Jira em lote, respeitando hierarquia (Epic, História, Subtarefa, etc.)
- Escreve o resultado em novas planilhas de sucesso e erro
- Na planilha de sucesso, a coluna `ID_JIRA` contém um **hyperlink clicável** para a issue criada no Jira, usando a fórmula do Google Sheets:
  ```
  =HYPERLINK("https://dot-group.atlassian.net/browse/POCGESTAO-XXXX","POCGESTAO-XXXX")
  ```
- O script garante que o hyperlink seja interpretado como fórmula, usando o parâmetro `valueInputOption='USER_ENTERED'` ao escrever na planilha

## Pré-requisitos
- Python 3.8+
- Conta de serviço Google com permissões para Drive e Sheets
- Credenciais do Jira (e-mail e token de API)
- Variáveis de ambiente configuradas em `.env`

## Instalação
1. Clone o repositório
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure o arquivo `.env` com as variáveis necessárias:
   - `JIRA_URL`
   - `JIRA_EMAIL`
   - `JIRA_API_TOKEN`
   - `JIRA_PROJECT_ID`
   - `JIRA_FOLDER_NAME` (opcional)
4. Coloque o arquivo `service-account.json` na raiz do projeto

## Uso
Execute o script principal:
```bash
python create_jira_issues.py
```

## Observações
- As planilhas de sucesso terão links clicáveis para cada issue criada no Jira.
- O script utiliza a API do Google Sheets com `USER_ENTERED` para garantir que as fórmulas sejam interpretadas corretamente.
- Campos do Jira são tratados conforme o tipo de issue e a configuração do seu projeto.

## Licença
MIT