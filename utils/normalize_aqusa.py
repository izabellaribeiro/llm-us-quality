import os
import re
import glob
import pandas as pd
from pathlib import Path

# --- CONFIGURAÇÃO ---
INPUT_DIR = os.path.join("data", "aqusa_results") 
OUTPUT_DIR = os.path.join("data", "processed_normalized", "baseline_aqusa")

# Onde estão os arquivos ORIGINAIS (para contarmos o total de linhas/histórias)?
RAW_DIR = os.path.join("data", "raw") 

# Critérios do Framework QUS
ALL_CRITERIA = [
    "well_formed.no_role", 
    "well_formed.no_means", 
    "atomic.conjunctions", 
    "minimal.punctuation", 
    "minimal.brackets", 
    "minimal.indicator_repetition",
    "unique.identical", 
    "uniform.uniform"
]

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def count_stories_in_raw_file(dataset_key):
    """
    Procura na pasta RAW um arquivo que tenha o nome do dataset e conta as linhas.
    """
    if not os.path.exists(RAW_DIR):
        print(f"   [AVISO] Pasta RAW não encontrada: {RAW_DIR}. Usando fallback (Max ID).")
        return None

    # Tenta achar um arquivo que contenha a chave (ex: 'g03-loudoun')
    search_pattern = os.path.join(RAW_DIR, f"*{dataset_key}*")
    candidates = glob.glob(search_pattern)
    
    # Remove o próprio arquivo de resultado do AQUSA se ele estiver lá
    candidates = [c for c in candidates if "result" not in c and "aqusa" not in c]

    if not candidates:
        print(f"   [AVISO] Arquivo raw original para '{dataset_key}' não encontrado em {RAW_DIR}.")
        return None
    
    raw_file = candidates[0]
    
    try:
        with open(raw_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            # Conta linhas não vazias (assumindo 1 user story por linha)
            count = len([l for l in lines if l.strip()])
            print(f"   [INFO] Dataset original encontrado: {os.path.basename(raw_file)} ({count} histórias)")
            return count
    except Exception as e:
        print(f"   [ERRO] Falha ao ler raw file: {e}")
        return None

def parse_aqusa_log(file_path):
    """Lê o arquivo de log do AQUSA e extrai defeitos."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    defects_map = {}
    current_story_id = None
    max_id_found = 0

    story_pattern = re.compile(r'^Story\s+#(\d+):')
    defect_pattern = re.compile(r'^\s*Defect type:\s+([\w\.]+)')

    for line in lines:
        line = line.strip()
        story_match = story_pattern.search(line)
        
        # Identificou nova história
        if story_match:
            current_story_id = int(story_match.group(1))
            if current_story_id > max_id_found:
                max_id_found = current_story_id
            if current_story_id not in defects_map:
                defects_map[current_story_id] = set()
            continue

        # Identificou defeito na história atual
        defect_match = defect_pattern.search(line)
        if defect_match and current_story_id is not None:
            defect_type = defect_match.group(1)
            # Só adiciona se for um critério conhecido do QUS
            if defect_type in ALL_CRITERIA:
                defects_map[current_story_id].add(defect_type)

    return defects_map, max_id_found

def normalize_aqusa_data(defects_map, total_stories_limit):
    """Cria a lista de dicionários normalizada."""
    normalized_rows = []
    
    # Garante que loop vai até o limite real (cria linhas zeradas para histórias sem defeitos)
    for i in range(1, total_stories_limit + 1):
        found_defects = defects_map.get(i, set())
        
        row = {
            "story_id": i,
            "defects_found": 1 if found_defects else 0
        }

        # Preenche 0 ou 1 para cada critério
        for criterion in ALL_CRITERIA:
            row[criterion] = 1 if criterion in found_defects else 0
        
        normalized_rows.append(row)

    return normalized_rows

def process_all_aqusa():
    if not os.path.exists(INPUT_DIR):
        print(f"ERRO: A pasta '{INPUT_DIR}' não existe.")
        return

    files = glob.glob(os.path.join(INPUT_DIR, "*.txt"))
    
    print(f"--- INICIANDO PROCESSAMENTO AQUSA -> CSV ---")
    
    for input_path in files:
        filename = os.path.basename(input_path)
        
        # Extrai a chave do dataset
        dataset_key = filename.replace("-result.txt", "").replace(".txt", "")
        
        print(f"\nProcessando: {filename}")

        # 1. Lê os defeitos do AQUSA
        defects_map, max_id_found = parse_aqusa_log(input_path)
        
        # 2. Tenta descobrir o tamanho REAL lendo o arquivo raw
        real_total = count_stories_in_raw_file(dataset_key)
        
        # Lógica de fallback para o total de linhas
        if real_total is None:
            print(f"   [ATENÇÃO] Usando Max ID ({max_id_found}) como total.")
            final_limit = max_id_found
        else:
            final_limit = real_total
            if max_id_found > final_limit:
                final_limit = max_id_found
        
        # 3. Normaliza os dados
        normalized_rows = normalize_aqusa_data(defects_map, final_limit)

        # 4. Converte para DataFrame e Salva CSV
        df = pd.DataFrame(normalized_rows)
        
        # Reordena colunas para ficar bonito
        cols = ['story_id', 'defects_found'] + ALL_CRITERIA
        df = df[cols]

        output_name = f"{dataset_key}-baseline.csv"
        output_path = os.path.join(OUTPUT_DIR, output_name)
        ensure_dir(output_path)

        df.to_csv(output_path, index=False)
        
        print(f"   [OK] Salvo CSV: {output_name} ({len(df)} linhas)")

if __name__ == "__main__":
    process_all_aqusa()