import pandas as pd
import shutil
import os
import re
from pathlib import Path

# --- CONFIGURAÇÃO DE CAMINHOS ---
def find_real_data_dir():
    current_path = Path(__file__).resolve().parent
    for _ in range(5):
        candidate = current_path / "data"
        if candidate.exists() and candidate.is_dir(): return candidate
        if current_path.parent == current_path: break
        current_path = current_path.parent
    return None

BASE_DATA_DIR = find_real_data_dir()
if not BASE_DATA_DIR:
    print("❌ Pasta 'data' não encontrada.")
    exit()

DIR_ESP1 = BASE_DATA_DIR / "ground_truth" / "esp1"
DIR_ESP2 = BASE_DATA_DIR / "ground_truth" / "esp2"
DIR_FINAL = BASE_DATA_DIR / "ground_truth" / "final"

# Cria a pasta final se não existir
DIR_FINAL.mkdir(parents=True, exist_ok=True)

def extract_group_id(filename):
    match = re.search(r'(?:g|group|grupo)[-_]?\s*(\d+)', str(filename).lower())
    if match: return match.group(1)
    return None

def consolidate_ground_truth():
    print("--- CONSOLIDANDO GROUND TRUTH FINAL (ADJUDICAÇÃO AUTOMÁTICA) ---")
    print(f"📂 Lendo de: {DIR_ESP1}")
    print(f"📂 Salvando em: {DIR_FINAL}")
    print("-" * 50)

    files_esp1 = list(DIR_ESP1.glob("*.csv"))
    
    if not files_esp1:
        print("❌ Nenhum arquivo encontrado em esp1.")
        return

    for file1 in files_esp1:
        group_id = extract_group_id(file1.name)
        if not group_id: continue

        # Tenta achar o par (apenas para contar conflitos resolvidos)
        file2 = next((f for f in DIR_ESP2.glob("*.csv") if extract_group_id(f.name) == group_id), None)
        
        # 1. Carrega o Expert 1 (Nossa Referência de Verdade)
        try:
            df_final = pd.read_csv(file1, sep=None, engine='python', encoding='utf-8')
        except:
            df_final = pd.read_csv(file1, sep=None, engine='python', encoding='latin1')

        # 2. (Opcional) Conta divergências resolvidas
        conflicts_resolved = 0
        if file2:
            try:
                df2 = pd.read_csv(file2, sep=None, engine='python')
                # Alinha colunas comuns numéricas
                common_cols = [c for c in df_final.columns if c in df2.columns and df_final[c].dtype in ['int64', 'float64']]
                # Simplificação: conta células diferentes
                if len(df_final) == len(df2):
                    for col in common_cols:
                         # Conta diferenças (fillna 0 para garantir comparação)
                        diff = (df_final[col].fillna(0) != df2[col].fillna(0)).sum()
                        conflicts_resolved += diff
            except:
                pass # Se der erro ao ler esp2, ignora, o importante é o esp1

        # 3. Salva o arquivo FINAL
        # Nome padronizado: groundTruthXX_final.csv
        final_name = f"groundTruth{group_id}_final.csv"
        final_path = DIR_FINAL / final_name
        
        df_final.to_csv(final_path, index=False)
        
        print(f"✅ Grupo {group_id}:")
        if conflicts_resolved > 0:
            print(f"   -> {conflicts_resolved} conflitos resolvidos (Prevalecendo Expert 1).")
        else:
            print(f"   -> Consolidado baseando-se no Expert 1.")
        print(f"   -> Salvo: {final_name}")

    print("-" * 50)
    print("🎉 PROCESSO CONCLUÍDO!")
    print(f"Os arquivos finais estão prontos em: {DIR_FINAL}")
    print("Agora você pode rodar a avaliação dos LLMs apontando para essa pasta.")

if __name__ == "__main__":
    consolidate_ground_truth()