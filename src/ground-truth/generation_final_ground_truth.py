import pandas as pd
import os
import glob
import re
import numpy as np

# --- CONFIGURAÇÕES ---
BASE_DIR = os.path.join("data", "ground_truth")
DIR_ESP1 = os.path.join(BASE_DIR, "esp1")
DIR_ESP2 = os.path.join(BASE_DIR, "esp2")
FILE_CONSENSO = os.path.join(BASE_DIR, "conflicts", "relatorio_conflitos_final.xlsx")
DIR_OUTPUT = os.path.join(BASE_DIR, "final")

os.makedirs(DIR_OUTPUT, exist_ok=True)

CRITERIOS_QUS = [
    "well_formed.no_role", 
    "well_formed.no_means", 
    "atomic.conjunctions", 
    "minimal.punctuation", 
    "minimal.brackets", 
    "minimal.indicator_repetition",
    "unique.identical", 
    "uniform.uniform"
]

def normalize_text(text):
    """Normaliza texto para comparação (remove espaços extras, quebras e lower)"""
    if not isinstance(text, str): return str(text)
    return " ".join(text.split()).lower().strip()

def extract_group_id(filename):
    match = re.search(r'(?:group|grupo|g)\s*[-_]?\s*(\d+)', filename.lower())
    if match: return match.group(1)
    return None

def find_pair_file(filename_esp1, dir_esp2):
    group_id = extract_group_id(filename_esp1)
    if not group_id: return None
    for c in glob.glob(os.path.join(dir_esp2, "*.csv")):
        if extract_group_id(os.path.basename(c)) == group_id:
            return c
    return None

def get_col_name(df, target):
    if target in df.columns: return target
    for col in df.columns:
        if target.lower() == col.lower().strip(): return col
    for col in df.columns:
        if target in col: return col
    return None

def get_id_column(df):
    candidates = ['id', 'story_id', 'story id', 'id_story', 'number', '#', 'no']
    for col in df.columns:
        if col.lower().strip() in candidates:
            return col
    return None

def carregar_consenso():
    """Carrega o Excel de conflitos e prepara para busca."""
    if not os.path.exists(FILE_CONSENSO):
        csv_path = str(FILE_CONSENSO).replace(".xlsx", ".csv")
        if os.path.exists(csv_path):
             print(f"Lendo consenso via CSV: {csv_path}")
             df = pd.read_csv(csv_path)
        else:
            print(f"ERRO CRÍTICO: Arquivo de consenso não encontrado em {FILE_CONSENSO}")
            return None
    else:
        print(f"Lendo consenso via Excel: {FILE_CONSENSO}")
        df = pd.read_excel(FILE_CONSENSO)

    df['Consenso'] = pd.to_numeric(df['Consenso'], errors='coerce')
    
    if 'User Story' in df.columns:
        df['text_norm'] = df['User Story'].apply(normalize_text)
    
    df['group_id'] = df['Dataset'].apply(lambda x: extract_group_id(str(x)))
    
    return df

def buscar_decisao(row_data, df_consenso_grupo):
    """
    Busca a decisão final baseada no conflito.
    """
    story_id = str(row_data['id'])
    story_text_norm = normalize_text(row_data['text'])
    criterio = row_data['criterio']
    val2 = row_data['val2']

    df_crit = df_consenso_grupo[df_consenso_grupo['Critério'] == criterio]
    match = pd.DataFrame()

    # 1. Busca por ID (se ID for válido no consenso)
    if story_id and story_id.lower() not in ['n/a', 'nan', 'none', '', '0']:
        if 'ID' in df_crit.columns:
            match = df_crit[df_crit['ID'].astype(str).str.strip() == story_id.strip()]

    # 2. Busca por Texto (Fallback principal)
    if match.empty:
        match = df_crit[df_crit['text_norm'] == story_text_norm]

    if not match.empty:
        decisao = match.iloc[0]['Consenso']
        if pd.notna(decisao):
            return int(decisao)
        else:
            # Encontrou o conflito mas não tem decisão preenchida -> Usa Esp2
            return int(val2)
    
    # Não achou no arquivo de conflitos -> Usa Esp2
    return int(val2)

def processar_ground_truths():
    df_consenso_full = carregar_consenso()
    if df_consenso_full is None: return

    files_esp1 = glob.glob(os.path.join(DIR_ESP1, "*.csv"))
    
    print(f"\n--- Gerando Ground Truths Finais em: {DIR_OUTPUT} ---\n")

    for file1 in files_esp1:
        filename1 = os.path.basename(file1)
        file2 = find_pair_file(filename1, DIR_ESP2)
        
        if not file2: continue
        
        group_id = extract_group_id(filename1)
        print(f"Processando Grupo {group_id}...")

        try:
            df1 = pd.read_csv(file1, sep=None, engine='python', header=1, encoding='utf-8')
            df2 = pd.read_csv(file2, sep=None, engine='python', header=1, encoding='utf-8')
        except:
            df1 = pd.read_csv(file1, sep=None, engine='python', header=1, encoding='latin1')
            df2 = pd.read_csv(file2, sep=None, engine='python', header=1, encoding='latin1')

        col_story1 = next((c for c in df1.columns if "story" in c.lower()), None)
        col_id1 = get_id_column(df1)
        col_story2 = next((c for c in df2.columns if "story" in c.lower()), None)
        
        df_consenso_grupo = df_consenso_full[df_consenso_full['group_id'] == group_id]

        final_rows = []

        # Itera pelo arquivo base (Esp1) com índice (idx começa em 0)
        for idx, row in df1.iterrows():
            story_text = row[col_story1]
            
            # --- LÓGICA DE ID ---
            # Se a coluna existe e não é nula/vazia, usa ela.
            # Senão, usa o índice da linha + 1.
            raw_id = row[col_id1] if col_id1 else None
            
            if pd.notna(raw_id) and str(raw_id).strip() not in ['', 'nan', 'N/A', 'None']:
                story_id = str(raw_id).strip()
            else:
                story_id = str(idx + 1) # Gera ID: 1, 2, 3...

            text_norm = normalize_text(story_text)
            
            # Tenta encontrar no Esp2
            row2_match = df2[df2[col_story2].apply(normalize_text) == text_norm]
            
            row2 = None
            if row2_match.empty:
                # Se não achar no Esp2, vamos usar os valores do Esp1 como padrão
                # para não quebrar o arquivo e manter a história.
                # Apenas registramos um aviso silencioso ou usamos print se quiser debug.
                pass 
            else:
                row2 = row2_match.iloc[0]

            new_row = {'ID': story_id, 'User Story': story_text}

            for crit in CRITERIOS_QUS:
                col1_name = get_col_name(df1, crit)
                val1 = int(row[col1_name]) if col1_name else 0
                
                # Definição de val2
                if row2 is not None:
                    col2_name = get_col_name(df2, crit)
                    val2 = int(row2[col2_name]) if col2_name else 0
                else:
                    # Se não achou a história no Esp2, assumimos val2 = val1
                    # Isso evita conflito e mantém o valor original do Esp1
                    val2 = val1 

                final_val = val1

                if val1 == val2:
                    final_val = val1
                else:
                    # CONFLITO: Buscar decisão
                    dados_conflito = {
                        'id': story_id,
                        'text': story_text,
                        'criterio': crit,
                        'val1': val1,
                        'val2': val2 
                    }
                    final_val = buscar_decisao(dados_conflito, df_consenso_grupo)

                new_row[crit] = final_val
            
            final_rows.append(new_row)

        if final_rows:
            df_final = pd.DataFrame(final_rows)
            # Ordenar colunas
            cols = ['ID', 'User Story'] + CRITERIOS_QUS
            df_final = df_final[cols]
            
            output_filename = f"GT_Grupo_{group_id}.csv"
            output_path = os.path.join(DIR_OUTPUT, output_filename)
            df_final.to_csv(output_path, index=False)
            print(f"  -> Salvo: {output_filename} (Total: {len(df_final)} histórias)")

if __name__ == "__main__":
    processar_ground_truths()