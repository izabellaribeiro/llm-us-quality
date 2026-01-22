import os
import json
import glob
from pathlib import Path

# --- CONFIGURAÇÃO ---
INPUT_DIR = os.path.join("data", "processed") 
OUTPUT_DIR = os.path.join("data", "processed_normalized")

# Critérios do Framework QUS que estamos monitorando
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
    """Garante que o diretório de saída exista."""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def clean_json_text(text):
    """Limpa blocos de código markdown (```json ... ```) se existirem."""
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        try:
            text = text.split("```")[1].split("```")[0]
        except IndexError:
            pass 
    return text.strip()

def normalize_execution(file_path):
    """Lê o arquivo bruto, extrai o JSON e converte para formato binário (0/1)."""
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_content = f.read()
    
    try:
        clean_content = clean_json_text(raw_content)
        if not clean_content: return None
        data = json.loads(clean_content)
    except json.JSONDecodeError:
        print(f"ERRO: JSON inválido ou corrompido em {os.path.basename(file_path)}")
        return None

    # 1. Descobrir o Total de Histórias
    # Tenta pegar do sumário ou inferir pelo maior ID encontrado
    total_stories = 0
    if "summary" in data and "total_stories" in data["summary"]:
        total_stories = int(data["summary"]["total_stories"])
    else:
        ids = [int(d.get("story_id", 0)) for d in data.get("defects", [])]
        if ids:
            total_stories = max(ids)
        else:
            # Se não tem defeitos e não tem summary, assume que falhou ou está vazio
            # Mas cuidado: pode ser que não tenha defeitos (tudo 0). 
            # Idealmente, você saberia o tamanho do dataset (ex: 291).
            # Vou assumir 0 aqui, mas você pode fixar um valor se souber o dataset.
            return None 

    # 2. Mapear os Defeitos encontrados
    defects_map = {}
    raw_defects = data.get("defects", [])
    
    for d in raw_defects:
        s_id = int(d.get("story_id", -1))
        d_type = d.get("defect_type")
        
        if s_id != -1 and d_type in ALL_CRITERIA:
            if s_id not in defects_map:
                defects_map[s_id] = set()
            defects_map[s_id].add(d_type)

    # 3. Construir a Lista Normalizada (Binária)
    normalized_analysis = []
    
    for i in range(1, total_stories + 1):
        story_obj = {
            "story_id": i,
            "defects_found": 0
        }
        
        found_defects = defects_map.get(i, set())
        
        for criterion in ALL_CRITERIA:
            if criterion in found_defects:
                story_obj[criterion] = 1
                story_obj["defects_found"] = 1
            else:
                story_obj[criterion] = 0
        
        normalized_analysis.append(story_obj)

    # 4. Monta o Novo JSON de Saída
    new_json = {
        "metadata": {
            "source_file": os.path.basename(file_path),
            "total_stories_processed": total_stories,
            "prompt_technique": "detected_auto" # Pode melhorar isso parseando o nome do arquivo se quiser
        },
        "analysis": normalized_analysis,
        "original_summary": data.get("summary", {})
    }
    
    return new_json

def process_all():
    if not os.path.exists(INPUT_DIR):
        print(f"ERRO: A pasta '{INPUT_DIR}' não existe.")
        return

    # Busca todos os arquivos .txt recursivamente
    files = glob.glob(os.path.join(INPUT_DIR, "**", "*.txt"), recursive=True)
    
    print(f"--- INICIANDO PROCESSAMENTO (Todos os arquivos .txt encontrados) ---")
    print(f"Diretório de entrada: {INPUT_DIR}")
    print(f"Total de arquivos encontrados: {len(files)}")
    
    count = 0
    errors = 0
    
    for input_path in files:
        # Normaliza o caminho
        rel_path = os.path.relpath(input_path, INPUT_DIR)
        
        # Define onde vai salvar (mantendo a estrutura de pastas)
        output_path = os.path.join(OUTPUT_DIR, rel_path)
        output_path = str(Path(output_path).with_suffix('.json'))
        
        ensure_dir(output_path)
        
        # Processa
        normalized_data = normalize_execution(input_path)
        
        if normalized_data:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(normalized_data, f, indent=2)
            count += 1
            print(f"[OK] Processado: {rel_path}")
        else:
            errors += 1
            print(f"[FALHA] Ignorado (conteúdo inválido): {rel_path}")

    print("\n--- CONCLUSÃO ---")
    print(f"Arquivos processados com sucesso: {count}")
    print(f"Arquivos com falha/vazios: {errors}")
    print(f"Saída salva em: {OUTPUT_DIR}")

if __name__ == "__main__":
    process_all()