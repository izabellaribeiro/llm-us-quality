import pandas as pd
import os
import glob
import re
import numpy as np

# --- CONFIGURAÇÃO ---
INPUT_DIR = os.path.join("data", "ground_truth", "esp2", "esp2-xp")
OUTPUT_DIR = os.path.join("data", "ground_truth", "esp2")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Colunas do QUS
SYNTACTIC_COLS = [
    'well_formed.no_role', 'well_formed.no_means',
    'minimal.brackets', 'minimal.indicator_repetition',
    'atomic.conjunctions', 'minimal.punctuation'
]
PRAGMATIC_COLS = [
    'unique.identical', 'uniform.uniform'
]
ALL_TARGET_DEFECTS = SYNTACTIC_COLS + PRAGMATIC_COLS

def find_header_row(filepath):
    """
    Lê as primeiras linhas do arquivo como texto puro para descobrir
    em qual linha está o cabeçalho real (contendo 'ID' e 'User Story').
    Retorna o índice da linha (0, 1, 2...) ou 0 se não achar.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [f.readline() for _ in range(20)] # Lê as primeiras 20 linhas
    except:
        with open(filepath, 'r', encoding='latin1') as f:
            lines = [f.readline() for _ in range(20)]
            
    for i, line in enumerate(lines):
        # Verifica se 'ID' e 'User Story' estão na linha (ignorando case)
        if 'id' in line.lower() and 'user story' in line.lower():
            return i
    return 0 # Padrão: linha 0

def extract_group_number(filename):
    match = re.search(r'(?:group|grupo|g)\s*[-_]?\s*(\d+)', filename, re.IGNORECASE)
    if match: return match.group(1)
    return None

def process_single_file(filepath):
    filename = os.path.basename(filepath)
    group_id = extract_group_number(filename)
    
    if not group_id:
        print(f"[PULADO] Grupo não identificado: {filename}")
        return

    print(f"Processando Grupo {group_id}: {filename}")

    # 1. Descobrir onde está o cabeçalho
    header_idx = find_header_row(filepath)
    if header_idx > 0:
        print(f"  -> Cabeçalho detectado na linha {header_idx} (pulando linhas vazias)")

    # 2. Ler o CSV usando o cabeçalho correto
    try:
        df = pd.read_csv(filepath, sep=None, engine='python', encoding='utf-8', header=header_idx)
    except:
        df = pd.read_csv(filepath, sep=None, engine='python', encoding='latin1', header=header_idx)

    # 3. Validação e Limpeza
    # Remove espaços dos nomes das colunas (ex: " ID " -> "ID")
    df.columns = df.columns.str.strip()

    if 'ID' not in df.columns:
        print(f"  [ERRO] Coluna 'ID' não encontrada mesmo após ajuste. Colunas: {list(df.columns)}")
        return

    # Remove linhas repetidas de cabeçalho ou vazias
    df = df[df['ID'].astype(str) != 'ID']
    df = df.dropna(subset=['ID'])
    df['ID_Int'] = pd.to_numeric(df['ID'], errors='coerce')

    # Encontra a coluna do Expert (flexível)
    expert_col = next((c for c in df.columns if "Expert" in str(c) or "Confirmation" in str(c)), None)
    if not expert_col:
        print(f"  [ERRO] Coluna Expert não encontrada. Disponíveis: {list(df.columns)}")
        return

    # 4. Processamento dos Defeitos
    grouped = df.groupby('ID_Int').agg({
        'User Story': 'first',
        expert_col: lambda x: set(str(v).strip() for v in x.dropna())
    }).reset_index()

    for defect in ALL_TARGET_DEFECTS:
        grouped[defect] = grouped[expert_col].apply(lambda x: 1 if defect in x else 0)

    # 5. Salvar
    grouped = grouped.sort_values('ID_Int')
    final_df = grouped[['User Story'] + ALL_TARGET_DEFECTS]

    output_filename = f"grupo{group_id}_esp2.csv"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # Cabeçalho Duplo
    header_row = [""] + ["Defeitos de qualidade sintática"] + [""]*(len(SYNTACTIC_COLS)-1) + \
                 ["Defeitos de qualidade pragmática"] + [""]*(len(PRAGMATIC_COLS)-1)

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        f.write(",".join(header_row) + "\n")
        final_df.to_csv(f, index=False)

    print(f"  -> SUCESSO: Salvo em {output_filename}")

def main():
    if not os.path.exists(INPUT_DIR):
        print(f"ERRO: Pasta não encontrada: {INPUT_DIR}")
        return
    
    files = glob.glob(os.path.join(INPUT_DIR, "*.csv"))
    print(f"Encontrados {len(files)} arquivos. Iniciando V3...\n")
    
    for f in files:
        process_single_file(f)

if __name__ == "__main__":
    main()