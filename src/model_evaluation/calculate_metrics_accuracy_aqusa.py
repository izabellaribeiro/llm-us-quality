import pandas as pd
import os
import re
import glob
from pathlib import Path
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score

# --- CONFIGURAÇÕES DE CAMINHOS DINÂMICAS ---

def encontrar_pasta_data():
    """
    Sobe a árvore de diretórios a partir do script até encontrar a pasta 'data'.
    Funciona independente se o script está em src/, src/model_evaluation/ ou na raiz.
    """
    caminho_atual = Path(__file__).resolve().parent
    
    # Tenta subir até 4 níveis procurando a pasta 'data'
    for _ in range(4):
        candidato = caminho_atual / "data"
        if candidato.exists() and candidato.is_dir():
            return caminho_atual, candidato
        
        # Sobe um nível
        if caminho_atual.parent == caminho_atual: # Chegou na raiz do disco (C:\)
            break
        caminho_atual = caminho_atual.parent
        
    return None, None

# Executa a busca
PROJECT_ROOT, BASE_DIR = encontrar_pasta_data()

print(f"--> Local do Script: {Path(__file__).resolve().parent}")

if BASE_DIR:
    print(f"--> Raiz do Projeto encontrada em: {PROJECT_ROOT}")
    print(f"--> Pasta DATA localizada em: {BASE_DIR}")
else:
    # Fallback se falhar (assume execução da raiz)
    BASE_DIR = Path("data").resolve()
    print(f"--> [AVISO] Pasta data não encontrada automaticamente. Tentando: {BASE_DIR}")

# Caminhos derivados
AQUSA_DIR = BASE_DIR / "processed_normalized" / "baseline_aqusa"
GT_DIR = BASE_DIR / "ground_truth" / "final"
OUTPUT_FILE = BASE_DIR / "relatorio_metricas_aqusa.xlsx"

# Critérios Oficiais do QUS
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
    """
    Extrai número do grupo de strings variadas.
    """
    match = re.search(r'(?:group|grupo|g)[-_]?\s*(\d+)', str(text), re.IGNORECASE)
    if match: return match.group(1)
    
    match_num = re.search(r'(\d+)', str(text))
    return match_num.group(1) if match_num else None

def carregar_ground_truth(group_num_str):
    """
    Carrega o CSV do Gabarito correspondente.
    """
    if not group_num_str: return None
    
    try:
        target_id = int(group_num_str)
    except:
        return None
    
    if not GT_DIR.exists():
        return None

    todos_arquivos = list(GT_DIR.glob("*.csv"))
    
    for arq in todos_arquivos:
        num_str = extract_group_number(arq.name)
        if num_str:
            try:
                if int(num_str) == target_id:
                    df = pd.read_csv(arq)
                    if 'ID' in df.columns:
                        df['ID'] = df['ID'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
                    return df
            except:
                continue
    return None

def calcular_metricas_aqusa():
    print("\n--- Avaliação Baseline: AQUSA ---")
    
    # Verificação crítica
    if not BASE_DIR.exists():
        print(f"\n[ERRO FATAL] A pasta 'data' não foi encontrada.")
        print(f"Certifique-se que a pasta 'data' existe na raiz do projeto 'llm-us-quality-xp26'.")
        return

    if not AQUSA_DIR.exists():
        print(f"\n[ERRO] Pasta de predições não encontrada: {AQUSA_DIR}")
        return

    # Busca CSVs
    aqusa_files = list(AQUSA_DIR.glob("*.csv"))
    
    if not aqusa_files:
        print("Nenhum arquivo CSV encontrado na pasta do AQUSA.")
        return

    resultados_detalhados = []

    for file_path in aqusa_files:
        print(f"\nProcessando arquivo: {file_path.name}")
        
        # 1. Carrega AQUSA
        try:
            df_pred = pd.read_csv(file_path)
        except Exception as e:
            print(f"  [ERRO] Leitura falhou: {e}")
            continue

        # Normaliza ID
        col_id_pred = 'story_id' if 'story_id' in df_pred.columns else 'id'
        if col_id_pred not in df_pred.columns:
            print(f"  [PULAR] Coluna de ID não encontrada.")
            continue
            
        df_pred[col_id_pred] = df_pred[col_id_pred].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
        pred_dict = df_pred.set_index(col_id_pred).to_dict('index')

        # 2. Carrega Gabarito
        grp_num_str = extract_group_number(file_path.name)
        if not grp_num_str:
            print("  [AVISO] Grupo não identificado no nome do arquivo.")
            continue

        df_gt = carregar_ground_truth(grp_num_str)
        if df_gt is None:
            print(f"  [AVISO] Gabarito (GT) não encontrado para Grupo {grp_num_str}")
            continue

        print(f"  -> Comparando com GT Grupo {grp_num_str} ({len(df_gt)} itens)")

        # 3. Cruzamento
        for _, row_gt in df_gt.iterrows():
            story_id = str(row_gt['ID']).strip()
            
            # Busca no AQUSA (default=0 se não achar ou tiver erro)
            pred_row = pred_dict.get(story_id, {})
            
            for crit in CRITERIOS_QUS:
                try:
                    y_true = int(float(row_gt.get(crit, 0)))
                except: y_true = 0
                    
                try:
                    y_pred = int(float(pred_row.get(crit, 0)))
                except: y_pred = 0

                resultados_detalhados.append({
                    "Model": "AQUSA",
                    "Dataset": f"Grupo {grp_num_str}",
                    "Criteria": crit,
                    "GT": y_true,
                    "Pred": y_pred
                })

    # --- MÉTRICAS ---
    if not resultados_detalhados:
        print("\nNenhum dado foi cruzado com sucesso.")
        return

    df_full = pd.DataFrame(resultados_detalhados)
    metrics_list = []

    for criteria, group in df_full.groupby("Criteria"):
        y_true = group['GT']
        y_pred = group['Pred']
        
        metrics_list.append({
            "Model": "AQUSA",
            "Criteria": criteria,
            "Precision": precision_score(y_true, y_pred, zero_division=0),
            "Recall": recall_score(y_true, y_pred, zero_division=0),
            "F1_Score": f1_score(y_true, y_pred, zero_division=0),
            "Accuracy": accuracy_score(y_true, y_pred),
            "Support": y_true.sum()
        })

    df_metrics = pd.DataFrame(metrics_list)

    # --- EXPORTAÇÃO ---
    try:
        with pd.ExcelWriter(OUTPUT_FILE) as writer:
            df_metrics.to_excel(writer, sheet_name="Metricas_AQUSA", index=False)
            
            df_summary = df_metrics.agg({
                "F1_Score": "mean",
                "Precision": "mean",
                "Recall": "mean"
            }).to_frame().T
            df_summary["Model"] = "AQUSA - Média Geral"
            df_summary.to_excel(writer, sheet_name="Resumo_Geral", index=False)

        print(f"\n✅ Sucesso! Relatório salvo em: {OUTPUT_FILE}")
    except Exception as e:
        print(f"\n[ERRO] Não foi possível salvar o arquivo Excel: {e}")
        print("Verifique se o arquivo já está aberto no Excel.")

if __name__ == "__main__":
    calcular_metricas_aqusa()