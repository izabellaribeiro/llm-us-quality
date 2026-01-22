import pandas as pd
import os
import re
import json
import glob
from pathlib import Path

# --- CONFIGURAÇÕES ---
# 1. Pega o local onde este script está
SCRIPT_DIR = Path(__file__).resolve().parent

# 2. Localiza pasta data
def find_data_dir(start_path):
    current = start_path
    for _ in range(4):
        candidate = current / "data"
        if candidate.exists() and candidate.is_dir(): return candidate
        current = current.parent
    return None

BASE_DIR = find_data_dir(SCRIPT_DIR)
PROCESSED_DIR = BASE_DIR / "processed"
AQUSA_DIR = BASE_DIR / "processed_normalized" / "baseline_aqusa" 
GT_DIR = BASE_DIR / "ground_truth" / "final"
OUTPUT_FILE = BASE_DIR / "auditoria_discrepancias.xlsx"

# MODELOS PARA AUDITAR
TARGET_MODELS = [
    "deepseek-chat",
    "gpt-4.1",
    "gpt-5",
    "gpt-5.2"
]

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

def extract_group_number(text):
    match = re.search(r'(?:group|grupo|g)[-_]?\s*(\d+)', str(text), re.IGNORECASE)
    if match: return match.group(1)
    match_num = re.search(r'(\d+)', str(text))
    return match_num.group(1) if match_num else None

def carregar_ground_truth(group_num_str):
    if not group_num_str: return None
    try: target_id = int(group_num_str)
    except: return None
    
    for arq in list(GT_DIR.glob("*.csv")):
        num_str = extract_group_number(arq.name)
        if num_str and int(num_str) == target_id:
            df = pd.read_csv(arq)
            if 'ID' in df.columns:
                df['ID'] = df['ID'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
            return df
    return None

def parse_llm_json(content):
    content = re.sub(r'```json\s*', '', content, flags=re.IGNORECASE).replace('```', '')
    start, end = content.find('{'), content.rfind('}')
    if start == -1 or end == -1: return {}
    try:
        data = json.loads(content[start:end+1])
        parsed = {}
        defects = data.get('defects', [])
        for d in defects:
            s_id = str(d.get('story_id', '')).strip().replace('.0', '')
            d_type = d.get('defect_type', '')
            if s_id not in parsed: parsed[s_id] = set()
            parsed[s_id].add(d_type)
        return parsed
    except: return {}

def auditar_llms():
    discrepancias = []
    print("--- Auditando LLMs (Baseado na Run 1) ---")
    
    if not PROCESSED_DIR.exists(): return []

    for prompt_dir in PROCESSED_DIR.iterdir():
        if not prompt_dir.is_dir(): continue
        
        for model_dir in prompt_dir.iterdir():
            if not model_dir.is_dir(): continue
            
            # Filtro de Modelos
            if not any(target in model_dir.name.lower() for target in TARGET_MODELS):
                continue
                
            for dataset_dir in model_dir.iterdir():
                if not dataset_dir.is_dir(): continue
                
                grp_num = extract_group_number(dataset_dir.name)
                df_gt = carregar_ground_truth(grp_num)
                if df_gt is None: continue
                
                # FOCA APENAS NA EXECUÇÃO 1 PARA AUDITORIA (AMOSTRA)
                exec_file = dataset_dir / "execution_1.txt"
                if not exec_file.exists(): continue
                
                try:
                    with open(exec_file, 'r', encoding='utf-8') as f: content = f.read()
                except: continue
                
                preds_map = parse_llm_json(content)
                
                for _, row_gt in df_gt.iterrows():
                    s_id = str(row_gt['ID']).strip()
                    story_text = row_gt.get('User Story', 'Texto não encontrado')
                    pred_set = preds_map.get(s_id, set())
                    
                    for crit in CRITERIOS_QUS:
                        y_true = int(row_gt.get(crit, 0))
                        y_pred = 1 if crit in pred_set else 0
                        
                        if y_true != y_pred:
                            tipo_erro = "FP (Modelo viu defeito onde não tem)" if y_pred == 1 else "FN (Modelo não viu defeito existente)"
                            
                            discrepancias.append({
                                "Origem": "LLM",
                                "Model": model_dir.name,
                                "Prompt": prompt_dir.name,
                                "Dataset": f"Grupo {grp_num}",
                                "ID": s_id,
                                "User Story": story_text,
                                "Criteria": crit,
                                "GT (Humano)": y_true,
                                "Pred (IA)": y_pred,
                                "Tipo Discrepância": tipo_erro
                            })
    return discrepancias

def auditar_aqusa():
    discrepancias = []
    print("--- Auditando AQUSA ---")
    
    if not AQUSA_DIR.exists(): return []
    
    for csv_file in AQUSA_DIR.glob("*.csv"):
        grp_num = extract_group_number(csv_file.name)
        df_gt = carregar_ground_truth(grp_num)
        if df_gt is None: continue
        
        try:
            df_pred = pd.read_csv(csv_file)
            col_id = 'story_id' if 'story_id' in df_pred.columns else 'id'
            df_pred[col_id] = df_pred[col_id].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
            pred_dict = df_pred.set_index(col_id).to_dict('index')
        except: continue
        
        for _, row_gt in df_gt.iterrows():
            s_id = str(row_gt['ID']).strip()
            story_text = row_gt.get('User Story', 'Texto não encontrado')
            pred_row = pred_dict.get(s_id, {})
            
            for crit in CRITERIOS_QUS:
                y_true = int(row_gt.get(crit, 0))
                y_pred = int(pred_row.get(crit, 0))
                
                if y_true != y_pred:
                    tipo_erro = "FP (Modelo viu defeito onde não tem)" if y_pred == 1 else "FN (Modelo não viu defeito existente)"
                    
                    discrepancias.append({
                        "Origem": "Baseline",
                        "Model": "AQUSA",
                        "Prompt": "N/A",
                        "Dataset": f"Grupo {grp_num}",
                        "ID": s_id,
                        "User Story": story_text,
                        "Criteria": crit,
                        "GT (Humano)": y_true,
                        "Pred (IA)": y_pred,
                        "Tipo Discrepância": tipo_erro
                    })
    return discrepancias

def gerar_auditoria():
    disc_llm = auditar_llms()
    disc_aqusa = auditar_aqusa()
    
    all_disc = disc_llm + disc_aqusa
    
    if not all_disc:
        print("✅ Incrível! Nenhuma discrepância encontrada (Tudo bateu 100%).")
        return
        
    df = pd.DataFrame(all_disc)
    
    # Ordenar para facilitar leitura
    df = df.sort_values(by=["Model", "Criteria", "ID"])
    
    # Salvar
    with pd.ExcelWriter(OUTPUT_FILE) as writer:
        df.to_excel(writer, sheet_name="Auditoria", index=False)
        
    print(f"\n✅ Relatório de Auditoria gerado: {OUTPUT_FILE}")
    print("\n--- COMO USAR ---")
    print("1. Abra o Excel e filtre a coluna 'Tipo Discrepância' por 'FP (Modelo viu defeito...)'.")
    print("2. Leia a 'User Story' e julgue: O defeito realmente existe?")
    print("3. SE EXISTIR: Significa que o Modelo estava CERTO e o Gabarito ERRADO.")
    print("   -> Isso valida que o LLM é super-humano nessa tarefa.")

if __name__ == "__main__":
    gerar_auditoria()