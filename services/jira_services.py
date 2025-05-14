#!/usr/bin/env python3
"""
jira_services.py

Serviço para interação com a API do Jira, incluindo criação de issues e manipulação de campos.
"""
import os
import requests
from requests.auth import HTTPBasicAuth

JIRA_URL = os.environ.get('JIRA_URL', 'https://dot-group.atlassian.net')
JIRA_EMAIL = os.environ.get('JIRA_EMAIL')
JIRA_API_TOKEN = os.environ.get('JIRA_API_TOKEN')
JIRA_PROJECT_ID = os.environ.get('JIRA_PROJECT_ID', '10879')

# Mapeamento por posição (índice da coluna : nome do campo no Jira do projeto 10879)
FIELD_MAP_BY_INDEX = {
    0: 'id_relation',         # A - ID do problema (identificador de referência)
    1: 'parent',              # B - Pai
    2: 'issuetype_name',      # C - Tipo de item (nome)
    3: 'customfield_11432',   # D - Portfólio DESEAD DOT
    4: 'summary',             # E - Resumo
    5: 'customfield_10015',   # F - Start Date
    6: 'duedate',             # G - Data limite
    7: 'timetracking',        # H - Estimativa original
    8: 'customfield_11630',   # I - Perfil de atuação - DESEAD
    9: 'customfield_10034',   # J - Story Points
    10: 'customfield_10109',  # K - Minutagem / telas / páginas
    11: 'customfield_11436',  # L - Ferramentas e IA
    12: 'customfield_11435',  # M - Acessibilidade type: array no mesmo campo
    13: 'customfield_11435',  # N - Acessibilidade type: array no mesmo campo
    14: 'customfield_11435',  # O - Acessibilidade type: array no mesmo campo
    15: 'customfield_11435',  # P - Acessibilidade type: array no mesmo campo
    16: 'customfield_11597',  # Q - Demanda terceirizada?
    17: 'customfield_10305',  # R - Pessoa Contratada
    18: 'customfield_10641',  # S - Categorias (Casting)
    19: 'customfield_10107',  # T - Nome do projeto
    20: 'customfield_10108',  # U - Cliente/Projeto/CC
    21: 'customfield_10105',  # V - Time Desenvolvimento EaD
    22: 'customfield_11437',  # W - Idioma
    23: 'labels',             # X - Categorias (Etiquetas / Labels)
}

# Mapeamento de nomes de tipos para IDs (msm coisa do de cima ^)
ISSUE_TYPE_MAP = {
    'Epic': '10000',
    'História': '10107',
    'Tarefa': '10164',
    'Subtarefa': '10109',
    'Bug': '10103'
}

# Campos que seguem o padrão de select
SELECT_FIELDS = {
    'customfield_10105',  # Time Desenvolvimento EaD
    'customfield_11437',  # Idioma
    'customfield_10108',  # Cliente/Projeto/CC
    'customfield_11597',  # Demanda terceirizada?
    'customfield_10641',  # Categorias (Casting)
    'customfield_11630',  # Perfil de atuação - DESEAD
}

# A descrição é feita em ADF (Atlassian Document Format), é uma linguagem de marcação para criar documentos. Nunca vi tbm, mas é parecido com o markdown.

def build_adf(text: str) -> dict:
    """
    Constrói o objeto Atlassian Document Format (ADF) para descrição.
    """
    return {
        'type': 'doc',
        'version': 1,
        'content': [
            {
                'type': 'paragraph',
                'content': [
                    {'type': 'text', 'text': text}
                ]
            }
        ]
    }

def create_issues_in_jira(issue_updates: list):
    """
    Envia um bulk create de issues para o Jira.
    Retorna um dicionário mapeando id_relation para as chaves do Jira.
    """
    url = f"{JIRA_URL}/rest/api/3/issue/bulk"
    headers = {'Content-Type': 'application/json'}
    payload = {'issueUpdates': issue_updates}
    
    print(f"Debug - Payload: {payload}")
    
    resp = requests.post(url, auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN), headers=headers, json=payload)
    if resp.ok:
        data = resp.json()
        created = data.get('issues', [])
        print(f"{len(created)} issues criadas com sucesso:")
        
        relation_to_key = {}
        for i, issue in enumerate(created):
            relation_id = issue_updates[i].get('id_relation')
            if relation_id:
                relation_to_key[relation_id] = issue['key']
            print(f"- {issue['key']}")
        
        return relation_to_key
    else:
        print(f"Falha ao criar issues ({resp.status_code}): {resp.text}")
        return None

def format_date(date_str: str) -> str:
    """
    Converte data do formato dd/mm/yyyy para yyyy-MM-dd
    """
    if not date_str:
        return None
    try:
        day, month, year = date_str.split('/')
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    except:
        return None

def prepare_jira_fields_by_index(row: list, relation_to_key: dict = None) -> dict:
    """
    Prepara os campos do Jira baseado nos índices da planilha.
    Retorna um dicionário com os campos e o id_relation para rastreamento.
    
    Args:
        row: Lista com os valores da linha
        relation_to_key: Dicionário mapeando id_relation para chaves do Jira
    """
    fields = {
        'project': {'id': JIRA_PROJECT_ID}
    }
    issuetype_id = None
    id_relation = None
    acessibilidade_values = []
    
    for idx, val in enumerate(row):
        if not val:
            continue
        key = FIELD_MAP_BY_INDEX.get(idx)
        if not key:
            continue
            
        if key == 'id_relation':
            id_relation = val
            continue
            
        if key == 'parent':
            if relation_to_key and val in relation_to_key:
                fields['parent'] = {'key': relation_to_key[val]}
            continue
        elif key == 'summary':
            fields['summary'] = val
        elif key == 'issuetype_name':
            issuetype_id = ISSUE_TYPE_MAP.get(val.strip())
            if not issuetype_id:
                raise ValueError(f"Tipo de item '{val}' não reconhecido. Use um dos seguintes: {list(ISSUE_TYPE_MAP.keys())}")
        elif key == 'labels':
            fields.setdefault('labels', []).append(val)
        elif key == 'duedate':
            fields['duedate'] = format_date(val)
        elif key == 'customfield_10015':  # Start date
            fields['customfield_10015'] = format_date(val)
        elif key == 'timetracking':
            fields['timetracking'] = {'originalEstimate': f"{val}h"}
        elif key in SELECT_FIELDS:
            fields[key] = {'value': val}
        elif key == 'customfield_11432':  # Portfólio DESEAD DOT (cascading select)
            if '->' in val:
                pai, filho = [v.strip() for v in val.split('->', 1)]
                fields[key] = {"value": pai, "child": {"value": filho}}
            else:
                fields[key] = {"value": val.strip()}
        elif key == 'customfield_10034':  # Story Points (botei pra converter pra int, alguns fóruns colocam float)
            try:
                fields[key] = int(val)
            except Exception:
                pass  # Ignora se não for número
        elif key == 'customfield_11435':  # Acessibilidade (multiselect)
            # Só adiciona se não for Epic
            if issuetype_id != '10000':  # 10000 é o ID do Epic
                acessibilidade_values.append(val.strip())
                continue
        elif key == 'customfield_11436':  # Ferramentas e IA (multiselect)
            # Só adiciona se não for Epic tbm
            if issuetype_id != '10000':  # 10000 é o ID do Epic
                values = [v.strip() for v in val.split(',') if v.strip()]
                fields.setdefault('customfield_11436', [])
                for v in values:
                    fields['customfield_11436'].append({"value": v})
            continue
        else:
            fields[key] = val
            
    if not issuetype_id:
        raise ValueError("Tipo de item (issuetype) não informado na planilha.")
    fields['issuetype'] = {'id': issuetype_id}
    
    # No final, adiciona o array de acessibilidade (se tiver)
    if acessibilidade_values:
        fields['customfield_11435'] = [{"value": v} for v in acessibilidade_values]
    
    return fields, id_relation 

def update_issue_parent(issue_key: str, parent_key: str):
    """
    Atualiza o campo parent de uma issue já criada no Jira.
    """
    url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {"fields": {"parent": {"key": parent_key}}}
    resp = requests.put(url, auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN), headers=headers, json=payload)
    if resp.ok:
        print(f"Parent de {issue_key} atualizado para {parent_key}")
        return True
    else:
        print(f"Erro ao atualizar parent de {issue_key}: {resp.status_code} - {resp.text}")
        return False 