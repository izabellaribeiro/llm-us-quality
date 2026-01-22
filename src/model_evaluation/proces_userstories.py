from dotenv import load_dotenv
from openai import OpenAI
from google import genai 
from google.genai import types 
from pathlib import Path
import pandas as pd
import os
import time
import sys

# --- CONFIGURAÇÕES DE CAMINHO ---
FILE_PATH = Path(__file__).resolve()
BASE_DIR = FILE_PATH.parent.parent.parent 
DATA_DIR = BASE_DIR / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
PROMPTS_DIR = BASE_DIR / "prompts"
ENV_PATH = BASE_DIR / ".env"

# Carrega variáveis de ambiente
print(f"--- Carregando ambiente ---")
print(f"Procurando .env em: {ENV_PATH}")
load_dotenv(ENV_PATH)

# --- VALIDAÇÃO DAS CHAVES ---
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
GOOGLE_KEY = os.environ.get("GOOGLE_API_KEY")
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY")

if not OPENAI_KEY:
    print("ERRO CRÍTICO: OPENAI_API_KEY não encontrada.")
    sys.exit(1)

if not GOOGLE_KEY:
    print("AVISO: GOOGLE_API_KEY não encontrada. Modelos Gemini falharão.")

if not DEEPSEEK_KEY:
    print("AVISO: DEEPSEEK_API_KEY não encontrada. Modelos DeepSeek falharão.")

# --- CONFIGURAÇÃO DOS CLIENTES ---

# 1. OpenAI (Original)
client_openai = OpenAI(api_key=OPENAI_KEY)

# 2. Google Gemini (Nova SDK)
client_google = None
if GOOGLE_KEY:
    client_google = genai.Client(api_key=GOOGLE_KEY)

# 3. DeepSeek (Via OpenAI Client - Compatível)
client_deepseek = None
if DEEPSEEK_KEY:
    client_deepseek = OpenAI(
        api_key=DEEPSEEK_KEY, 
        base_url="https://api.deepseek.com"
    )

# --- PARÂMETROS DO EXPERIMENTO ---
# 'deepseek-chat' geralmente aponta para a versão V3 (atual V3.2 ou similar na API)
# 'deepseek-reasoner' aponta para o modelo R1 (raciocínio)
LLM_MODELS = [
    "deepseek-chat",
    "deepseek-reasoner",
    "gemini-3-pro-preview", 
    "gemini-3-flash-preview", 
    "gemini-2.5-flash", 
    "gpt-5", 
    "gpt-5.2", 
    "gpt-4.1",
]

NUM_EXECUTIONS = 5 
TEMPERATURE = 0.5 

# DataFrame global
df_summary = pd.DataFrame(columns=[
    "dataset_name", "prompt_type", "model", "execution_id", "time_taken", "status"
])

def get_file_content(file_path: Path) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Erro ao ler arquivo {file_path}: {e}")
        return ""

def save_execution_result(base_path: Path, run_id: int, content: str):
    filename = f"execution_{run_id}.txt"
    file_path = base_path / filename
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

# --- FUNÇÕES DE CHAMADA AOS MODELOS ---

# --- FUNÇÕES DE CHAMADA AOS MODELOS (ATUALIZADAS) ---

def send_to_openai(system_prompt: str, user_content: str, model: str):
    """Envia requisição para OpenAI com limite de tokens aumentado."""
    current_temperature = TEMPERATURE 
    if model.startswith("o1") or "gpt-5" in model:
        current_temperature = 1

    try:
        response = client_openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=current_temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Erro OpenAI ({model}): {e}")
        return None

def send_to_gemini(system_prompt: str, user_content: str, model: str):
    """Envia requisição para Gemini com limite de tokens aumentado."""
    if not client_google:
        print("Cliente Google não inicializado.")
        return None

    max_retries = 3
    base_wait_time = 30

    for attempt in range(max_retries):
        try:
            response = client_google.models.generate_content(
                model=model,
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=TEMPERATURE,
                )
            )
            return response.text
        
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print(f"⚠️ Cota do Gemini excedida ({model}). Tentativa {attempt+1}/{max_retries}.")
                print(f"   Aguardando {base_wait_time}s...")
                time.sleep(base_wait_time)
            else:
                print(f"Erro Gemini ({model}): {e}")
                return None
    
    print(f"❌ Falha no Gemini ({model}) após tentativas.")
    return None

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import openai # Assumindo que você usa o client da OpenAI ou compatível

# --- CONFIGURAÇÃO DO RETRY ---
# Tenta 3 vezes, esperando 4s, 8s, 16s entre tentativas se der erro de API ou Timeout
@retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=1, min=4, max=20),
    reraise=True # Importante: se falhar 3x, ele joga o erro para o 'except' lá embaixo
)
def _execute_deepseek_call(system_prompt, user_content, model):
    """Função interna que faz a chamada bruta com retry automático."""
    return client_deepseek.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        temperature=TEMPERATURE,
        stream=False,
        timeout=180.0  # <--- AUMENTADO PARA 3 MINUTOS (padrão costuma ser 60s)
    )

def send_to_deepseek(system_prompt: str, user_content: str, model: str):
    """Envia requisição para DeepSeek com tratamento de erro e retries."""
    
    # Verificação inicial
    if not client_deepseek:
        print("Cliente DeepSeek não inicializado.")
        return None

    try:
        # Chamamos a função decorada com @retry
        response = _execute_deepseek_call(system_prompt, user_content, model)
        
        # Se chegou aqui, deu certo
        return response.choices[0].message.content

    except Exception as e:
        # Se cair aqui, é porque falhou todas as 3 tentativas (timeout ou outro erro)
        print(f"Erro CRÍTICO DeepSeek ({model}) após 3 tentativas: {e}")
        return None

def get_llm_response(system_prompt: str, user_content: str, model: str):
    model_lower = model.lower()
    
    # Roteamento
    if "gemini" in model_lower:
        return send_to_gemini(system_prompt, user_content, model)
    elif "deepseek" in model_lower:
        return send_to_deepseek(system_prompt, user_content, model)
    else:
        return send_to_openai(system_prompt, user_content, model)

# --- EXECUÇÃO PRINCIPAL ---

def run_experiment():
    global df_summary
    
    # Verificações básicas
    if not PROMPTS_DIR.exists():
        print(f"ERRO: Pasta prompts não existe em {PROMPTS_DIR}")
        return
    prompt_files = list(PROMPTS_DIR.glob("*.txt"))
    dataset_files = list(DATA_RAW_DIR.glob("*.txt"))

    if not prompt_files or not dataset_files:
        print("ALERTA: Faltando arquivos.")
        return

    print(f"--- Iniciando Experimento ---")
    print(f"Modelos: {LLM_MODELS}")
    print("-" * 50)

    for prompt_file in prompt_files:
        prompt_name = prompt_file.stem 
        prompt_content = get_file_content(prompt_file)

        for model in LLM_MODELS:
            for dataset_file in dataset_files:
                dataset_name = dataset_file.stem
                user_story_content = get_file_content(dataset_file)
                
                output_dir = PROCESSED_DIR / prompt_name / model / dataset_name
                output_dir.mkdir(parents=True, exist_ok=True)
                
                print(f"\n> {prompt_name} | {model} | {dataset_name}")

                for i in range(1, NUM_EXECUTIONS + 1):
                    start_time = time.time()
                    
                    response_content = get_llm_response(
                        system_prompt=prompt_content,
                        user_content=user_story_content,
                        model=model
                    )

                    duration = time.time() - start_time
                    status = "Success" if response_content else "Error"

                    if response_content:
                        save_execution_result(output_dir, i, response_content)

                    new_row = {
                        "dataset_name": dataset_name,
                        "prompt_type": prompt_name,
                        "model": model,
                        "execution_id": i,
                        "time_taken": round(duration, 2),
                        "status": status
                    }
                    df_summary = pd.concat([df_summary, pd.DataFrame([new_row])], ignore_index=True)
                    
                    print(f"  Run {i}: {status} ({duration:.2f}s)")
                    
                    # Pausas para Rate Limit
                    if "gemini" in model.lower():
                        time.sleep(4)
                    else:
                        time.sleep(1)

    try:
        excel_path = PROCESSED_DIR / "experiment_summary.xlsx"
        df_summary.to_excel(excel_path, index=False)
        print(f"\nSalvo em: {excel_path}")
    except Exception as e:
        print(f"Erro ao salvar excel: {e}")

if __name__ == "__main__":
    run_experiment()