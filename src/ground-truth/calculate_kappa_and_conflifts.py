import pandas as pd
import os
import glob
import re
from pathlib import Path
from sklearn.metrics import cohen_kappa_score

# --- LOCALIZADOR DE PASTAS INTELIGENTE ---
def find_real_data_dir():
    current_path = Path(__file__).resolve().parent
    print(f"📍 Script rodando em: {current_path}")
    
    for _ in range(5):
        candidate = current_path / "data"
        if candidate.exists() and candidate.is_dir():
            print(f"✅ Pasta 'data' encontrada em: {candidate}")
            return candidate
        if current_path.parent == current_path:
            break
        current_path = current_path.parent
    return None

# --- CONFIGURAÇÃO ---
BASE_DATA_DIR = find_real_data_dir()

if not BASE_DATA_DIR:
    print("\n❌ ERRO CRÍTICO: Não consegui encontrar a pasta 'data' na raiz do projeto.")
    exit()

DIR_ESP1 = BASE_DATA_DIR / "ground_truth" / "esp1"
DIR_ESP2 = BASE_DATA_DIR / "ground_truth" / "esp2"
OUTPUT_CONFLICTS = BASE_DATA_DIR / "ground_truth" / "conflicts" / "relatorio_conflitos_final.xlsx"
OUTPUT_KAPPAS = BASE_DATA_DIR / "ground_truth" / "kappas_finais.csv"

OUTPUT_CONFLICTS.parent.mkdir(parents=True, exist_ok=True)

TARGET_CRITERIA = [
    "well_formed.no_role", "well_formed.no_means", "atomic.conjunctions",
    "minimal.punctuation", "minimal.brackets", "minimal.indicator_repetition",
    "unique.identical", "uniform.uniform"
]

def extract_group_id(filename):
    match = re.search(r'(?:g|group|grupo)[-_]?\s*(\d+)', str(filename).lower())
    if match: return match.group(1)
    return None

def find_pair_file(filename_esp1, dir_esp2):
    group_id = extract_group_id(filename_esp1)
    if not group_id: return None
    for c in Path(dir_esp2).glob("*.csv"):
        if extract_group_id(c.name) == group_id:
            return c
    return None

def identify_columns(df):
    df.columns = df.columns.str.strip()
    col_id = next((c for c in df.columns if c.lower() in ['id', 'story_id', '#']), df.columns[0])
    col_story = next((c for c in df.columns if c.lower() in ['user story', 'userstory', 'story', 'text']), df.columns[1])
    return col_id, col_story

def process_agreement():
    print("\n--- INICIANDO CÁLCULO DE KAPPA ---")
    
    if not DIR_ESP1.exists():
        print(f"❌ Pasta esp1 não existe: {DIR_ESP1}")
        return

    files_esp1 = list(DIR_ESP1.glob("*.csv"))
    if not files_esp1:
        print("❌ Nenhum arquivo CSV encontrado na pasta esp1.")
        return

    all_conflicts = []
    kappa_results = []

    for file1 in files_esp1:
        filename1 = file1.name
        file2 = find_pair_file(filename1, DIR_ESP2)
        
        if not file2:
            print(f"⚠️ Par não encontrado para {filename1} (Pulando)")
            continue
            
        print(f"\n🔵 Processando par: {filename1} <-> {file2.name}")
        
        try:
            df1 = pd.read_csv(file1, sep=None, engine='python', encoding='utf-8')
        except:
            df1 = pd.read_csv(file1, sep=None, engine='python', encoding='latin1')
            
        try:
            df2 = pd.read_csv(file2, sep=None, engine='python', encoding='utf-8')
        except:
            df2 = pd.read_csv(file2, sep=None, engine='python', encoding='latin1')

        id1, story1 = identify_columns(df1)
        id2, story2 = identify_columns(df2)

        df1[id1] = df1[id1].astype(str).str.strip()
        df2[id2] = df2[id2].astype(str).str.strip()
        
        df1 = df1.set_index(id1)
        df2 = df2.set_index(id2)
        
        common_idx = df1.index.intersection(df2.index)
        df1 = df1.loc[common_idx]
        df2 = df2.loc[common_idx]

        # Lista temporária para exibir no terminal
        current_group_scores = []

        # Calcula Kappa
        for crit in TARGET_CRITERIA:
            if crit not in df1.columns: continue
            
            val1 = df1[crit].fillna(0).astype(int)
            val2 = df2[crit].fillna(0).astype(int)
            
            try:
                if val1.nunique() <= 1 and val2.nunique() <= 1:
                    score = 1.0 if (val1 == val2).all() else 0.0
                else:
                    score = cohen_kappa_score(val1, val2)
                    if pd.isna(score): score = 0
            except: score = 0
            
            # Salva para o CSV final
            kappa_results.append({
                "Dataset": filename1,
                "Critério": crit,
                "Kappa": score
            })
            
            # Salva para exibir no terminal agora
            current_group_scores.append((crit, score))
            
            diffs = val1 != val2
            for idx in diffs[diffs].index:
                txt = df1.loc[idx, story1]
                if isinstance(txt, pd.Series): txt = txt.iloc[0]
                
                all_conflicts.append({
                    "Dataset": filename1,
                    "ID": idx,
                    "User Story": txt,
                    "Critério": crit,
                    "Esp1": val1.loc[idx],
                    "Esp2": val2.loc[idx],
                    "Consenso": "" 
                })

        # --- IMPRESSÃO NO TERMINAL (NOVA PARTE) ---
        print(f"   📊 Resultados para {filename1}:")
        print(f"   {'Critério':<30} | {'Kappa':<10}")
        print(f"   {'-'*30}-+-{'-'*10}")
        
        for crit_name, k_score in current_group_scores:
            print(f"   {crit_name:<30} | {k_score:.3f}")
        
        if current_group_scores:
            avg_kappa = sum(s for _, s in current_group_scores) / len(current_group_scores)
            print(f"   {'-'*43}")
            print(f"   {'MÉDIA DO GRUPO':<30} | {avg_kappa:.3f}")
        else:
            print("   (Nenhum critério encontrado neste arquivo)")
        print("   " + "="*43)
        # ------------------------------------------

    if kappa_results:
        pd.DataFrame(kappa_results).to_csv(OUTPUT_KAPPAS, index=False)
        print(f"\n✅ Todos os Kappas salvos em: {OUTPUT_KAPPAS}")

    if all_conflicts:
        df_conf = pd.DataFrame(all_conflicts).sort_values(by=["Dataset", "ID"])
        df_conf.to_excel(OUTPUT_CONFLICTS, index=False)
        print(f"✅ Relatório de Conflitos salvo: {OUTPUT_CONFLICTS}")
    else:
        print("\n🎉 Nenhum conflito encontrado!")

if __name__ == "__main__":
    process_agreement()