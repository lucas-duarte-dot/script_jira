#!/usr/bin/env python3
"""
create_jira_issues.py

Script principal para criar issues no Jira baseadas em planilhas do Google Drive.
"""
import os
import sys
from dotenv import load_dotenv
from services.google_drive_services import (
    get_services_service_account,
    find_folder_id,
    list_spreadsheets_in_folder,
    read_sheet,
    create_spreadsheet,
    get_folder_id_by_name
)
from services.jira_services import (
    create_issues_in_jira,
    prepare_jira_fields_by_index,
    update_issue_parent
)

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(script_dir, '.env')
    print(f"dotenv_path: {dotenv_path}")
    load_dotenv(dotenv_path)
    
    FOLDER_NAME = os.environ.get('JIRA_FOLDER_NAME', 'JiraCard - Importar')
    
    # inicia drive e sheets
    drive_service, sheets_service = get_services_service_account()

    try:
        folder_id = find_folder_id(drive_service, FOLDER_NAME)
        print(f"Pasta '{FOLDER_NAME}' encontrada (ID: {folder_id})")
        concluido_folder_id = get_folder_id_by_name(drive_service, 'JiraCard - Concluído')
        erro_folder_id = get_folder_id_by_name(drive_service, 'JiraCard - Erro')
    except Exception as e:
        print(e)
        sys.exit(1)

    sheets = list_spreadsheets_in_folder(drive_service, folder_id)
    if not sheets:
        print(f"Nenhuma planilha em '{FOLDER_NAME}'.")
        sys.exit(0)

    for sheet in sheets:
        print(f"Processando planilha: {sheet['name']}")
        values = read_sheet(sheets_service, sheet['id'])
        if len(values) < 2:
            print(" - sem dados (menos de 2 linhas)")
            continue

        # --- NOVO FLUXO EM ONDAS PARA HIERARQUIA ---
        # Prepara todas as linhas para processamento em ondas (criação de issues em hierarquia)
        all_rows = values[1:]
        headers = values[0]
        sucesso_rows = [["ID_JIRA"] + headers]
        erro_rows = [headers]
        id_to_row = {row[0]: row for row in all_rows if row and row[0]}
        id_to_parent = {row[0]: row[1] for row in all_rows if row and row[0]}
        id_to_fields = {}
        id_to_relation = {}
        for row in all_rows:
            try:
                fields, id_relation = prepare_jira_fields_by_index(row)
                id_to_fields[row[0]] = fields
                id_to_relation[row[0]] = id_relation
            except Exception as e:
                print(f" - linha com erro: {str(e)}")
                erro_rows.append(row)
        # Mapeamento de ID da planilha para chave Jira
        relation_to_key = {}
        # IDs ainda não criados
        ids_pendentes = set(id_to_fields.keys())
        # Enquanto houver issues para criar
        while ids_pendentes:
            prontos_para_criar = []
            refs_para_criar = []
            rels_para_criar = []
            for id_ in list(ids_pendentes):
                parent_id = id_to_parent.get(id_)
                # Se não tem pai ou o pai já foi criado
                if not parent_id or parent_id in relation_to_key:
                    fields = id_to_fields[id_].copy()
                    # Só adiciona parent se já existir
                    if parent_id and parent_id in relation_to_key:
                        fields['parent'] = {'key': relation_to_key[parent_id]}
                    prontos_para_criar.append({'fields': fields, 'id_relation': id_})
                    refs_para_criar.append(id_to_row[id_])
                    rels_para_criar.append(id_)
            if not prontos_para_criar:
                print("Erro: Não foi possível criar as issues restantes por dependência circular ou falta de pais.")
                for id_ in ids_pendentes:
                    erro_rows.append(id_to_row[id_])
                break
            # Cria as issues desta onda
            novos_relation_to_key = create_issues_in_jira(prontos_para_criar)
            if novos_relation_to_key:
                relation_to_key.update(novos_relation_to_key)
                for i, row in enumerate(refs_para_criar):
                    id_relation = rels_para_criar[i]
                    jira_key = relation_to_key[id_relation]
                    jira_url = f"https://dot-group.atlassian.net/browse/{jira_key}"
                    hyperlink = f"=HYPERLINK(\"{jira_url}\",\"{jira_key}\")"
                    sucesso_row = [hyperlink] + row
                    sucesso_rows.append(sucesso_row)
                # Remove IDs já criados
                ids_pendentes -= set(rels_para_criar)
            else:
                for row in refs_para_criar:
                    erro_rows.append(row)
                break
        # --- FIM DO NOVO FLUXO EM ONDAS ---

        # Cria planilhas de sucesso e erro
        if len(sucesso_rows) > 1:
            create_spreadsheet(sheets_service, drive_service, 
                             f"{sheet['name']} - Concluído", 
                             sucesso_rows, 
                             concluido_folder_id)
            print(f"Linhas concluídas enviadas para 'JiraCard - Concluído'")
            
        if len(erro_rows) > 1:
            create_spreadsheet(sheets_service, drive_service, 
                             f"{sheet['name']} - Erro", 
                             erro_rows, 
                             erro_folder_id)
            print(f"Linhas com erro enviadas para 'JiraCard - Erro'")

if __name__ == '__main__':
    main()
