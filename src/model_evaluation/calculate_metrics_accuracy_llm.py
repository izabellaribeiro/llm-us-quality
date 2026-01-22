import pandas as pd
import os
import json
import glob
import re
from pathlib import Path
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score

# --- LÓGICA DE CAMINHOS ROBUSTA ---
def encontrar_pasta_data():
    """
    Sobe a árvore de diretórios a partir do script até encontrar a pasta 'data'.
    """
    caminho_atual = Path(__file__).resolve().parent
    
    # Tenta subir até 4 níveis procurando a pasta 'data'
    for _ in range(4):
        candidato = caminho_atual / "data"
        if candidato.exists() and candidato.is_dir():
            return caminho_atual, candidato
        
        # Se chegar na raiz do disco (C:\ ou /), para.
        if caminho_atual.parent == caminho_atual:
            break
        caminho_atual = caminho_atual.parent
        
    return None, None

# Executa a busca de caminhos
PROJECT_ROOT, BASE_DIR = encontrar_pasta_data()

print(f"--> Local do Script: {Path(__file__).resolve().parent}")

if BASE_DIR:
    print(f"--> Raiz do Projeto identificada: {PROJECT_ROOT}")
    print(f"--> Pasta DATA localizada em: {BASE_DIR}")
else:
    # Fallback: assume que está rodando da raiz se não encontrar
    BASE_DIR = Path("data").resolve()
    print(f"--> [AVISO] Pasta data não encontrada automaticamente. Tentando: {BASE_DIR}")

# --- CONFIGURAÇÕES ---
PROCESSED_DIR = BASE_DIR / "processed"
GT_DIR = BASE_DIR / "ground_truth" / "final"
OUTPUT_FILE = BASE_DIR / "relatorio_metricas_final.xlsx"

# Critérios Oficiais
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

def carregar_ground_truth(dataset_name):
    """
    Carrega o CSV do Gabarito.
    Ajustado para ler 'groundTruthXX_final.csv'.
    """
    # 1. Extrai números do nome da pasta (ex: 'g03-loudoun' -> '03')
    match = re.search(r'(\d+)', str(dataset_name))
    if not match: 
        return None, None
    
    num_str = match.group(1)      # "03"
    num_int = int(num_str)        # 3 (inteiro remove o zero à esquerda)
    
    # Valida se a pasta GT existe
    if not GT_DIR.exists():
        return None, None

    # 2. LISTA DE PADRÕES ATUALIZADA (Prioridade para o formato da sua imagem)
    candidates_patterns = [
        f"groundTruth{num_str}_final.csv",   # Tenta "groundTruth03_final.csv"
        f"groundTruth{num_int}_final.csv",   # Tenta "groundTruth3_final.csv"
        f"groundTruth{num_str}.csv",         # Variação sem '_final'
        f"GT_Grupo_{num_int}.csv",           # Padrão antigo
        f"*{num_str}*.csv",                  # Genérico com "03"
        f"*{num_int}*.csv"                   # Genérico com "3"
    ]
    
    found_file = None
    
    for pattern in candidates_patterns:
        # Se o padrão não tem curinga (*), verifica direto
        if "*" not in pattern:
            fpath = GT_DIR / pattern
            if fpath.exists():
                found_file = fpath
                break
        else:
            # Se tem curinga, usa glob
            matches = list(GT_DIR.glob(pattern))
            if matches:
                for m in matches:
                    # Verifica se o número extraído do arquivo bate com o número buscado
                    # Isso evita pegar 'groundTruth13' quando procuramos '3'
                    file_num_match = re.search(r'(\d+)', m.name)
                    if file_num_match:
                        # Compara string "03" com "03" OU int 3 com 3
                        f_num = file_num_match.group(1)
                        if f_num == num_str or int(f_num) == num_int:
                            found_file = m
                            break
                if found_file: break

    if found_file:
        try:
            df = pd.read_csv(found_file)
            if 'ID' in df.columns:
                df['ID'] = df['ID'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
            return df, found_file.name
        except Exception as e:
            print(f"  [ERRO] Falha ao ler GT {found_file}: {e}")
            return None, None

    return None, None

def parse_llm_json(file_content):
    """Lê o JSON de resposta do LLM."""
    content = re.sub(r'```json\s*', '', file_content, flags=re.IGNORECASE)
    content = re.sub(r'```', '', content)
    
    start = content.find('{')
    end = content.rfind('}')
    
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
    except:
        return {}

def calcular_metricas():
    print(f"\n--- Iniciando Avaliação de Métricas (LLM vs GT) ---")
    
    if not BASE_DIR.exists():
        print(f"[ERRO FATAL] A pasta 'data' não foi encontrada.")
        return

    print(f"Lendo Processados de: {PROCESSED_DIR}")
    print(f"Lendo Gabaritos de:   {GT_DIR}")
    
    if not PROCESSED_DIR.exists():
        print(f"[ERRO] Pasta 'processed' não encontrada.")
        return

    if not GT_DIR.exists():
        print(f"[ERRO] Pasta 'ground_truth' não encontrada.")
        return

    resultados_detalhados = []
    
    prompts = [p for p in PROCESSED_DIR.iterdir() if p.is_dir()]
    
    if not prompts:
        print("[AVISO] Nenhuma pasta de prompt encontrada.")
    
    for prompt_dir in prompts:
        models = [m for m in prompt_dir.iterdir() if m.is_dir()]
        for model_dir in models:
            datasets = [d for d in model_dir.iterdir() if d.is_dir()]
            for dataset_dir in datasets:
                
                # Carrega GT (Agora procurando groundTruthXX_final.csv)
                df_gt, gt_filename = carregar_ground_truth(dataset_dir.name)
                
                if df_gt is None:
                    print(f"[PULANDO] GT não encontrado para: {dataset_dir.name}")
                    print(f"   -> O script procurou por arquivos como 'groundTruthXX_final.csv' na pasta final.")
                    continue
                
                exec_files = list(dataset_dir.glob("execution_*.txt"))
                if not exec_files: continue

                print(f" Avaliando: {model_dir.name} | {dataset_dir.name} (usando {gt_filename})")

                for exec_file in exec_files:
                    exec_id = exec_file.stem.split('_')[-1]
                    try:
                        with open(exec_file, 'r', encoding='utf-8') as f: content = f.read()
                    except: continue
                        
                    preds_map = parse_llm_json(content)
                    
                    # Comparação
                    for _, row in df_gt.iterrows():
                        story_id = str(row['ID']).strip()
                        pred_defects = preds_map.get(story_id, set())
                        
                        for crit in CRITERIOS_QUS:
                            try:
                                y_true = int(float(row.get(crit, 0)))
                            except: y_true = 0
                                
                            y_pred = 1 if crit in pred_defects else 0
                            
                            resultados_detalhados.append({
                                "Prompt": prompt_dir.name,
                                "Model": model_dir.name,
                                "Dataset": dataset_dir.name,
                                "Execution": exec_id,
                                "Criteria": crit,
                                "GT": y_true,
                                "Pred": y_pred
                            })

    if not resultados_detalhados:
        print("Nenhum dado processado com sucesso.")
        return

    print("\nCalculando estatísticas finais...")
    df_full = pd.DataFrame(resultados_detalhados)
    metrics_list = []
    
    # Agrupa para métricas
    groups = df_full.groupby(["Model", "Prompt", "Dataset", "Criteria"])
    
    for name, group in groups:
        y_true = group['GT']
        y_pred = group['Pred']
        
        metrics_list.append({
            "Model": name[0],
            "Prompt": name[1],
            "Dataset": name[2],
            "Criteria": name[3],
            "Precision": precision_score(y_true, y_pred, zero_division=0),
            "Recall": recall_score(y_true, y_pred, zero_division=0),
            "F1_Score": f1_score(y_true, y_pred, zero_division=0),
            "Accuracy": accuracy_score(y_true, y_pred),
            "Support": y_true.sum()
        })
        
    df_metrics = pd.DataFrame(metrics_list)
    
    try:
        with pd.ExcelWriter(OUTPUT_FILE) as writer:
            df_metrics.to_excel(writer, sheet_name="Por_Criterio", index=False)
            
            df_summary = df_metrics.groupby(["Model", "Prompt"]).agg({
                "F1_Score": "mean",
                "Precision": "mean",
                "Recall": "mean"
            }).reset_index()
            df_summary.to_excel(writer, sheet_name="Resumo_Geral", index=False)
            
        print(f"\n✅ Relatório salvo com sucesso: {OUTPUT_FILE}")
    except Exception as e:
        print(f"\n[ERRO] Falha ao salvar Excel: {e}")

if __name__ == "__main__":
    calcular_metricas()