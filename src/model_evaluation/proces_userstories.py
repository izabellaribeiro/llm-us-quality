from dotenv import load_dotenv
from openai import OpenAI

from pathlib import Path, PosixPath
import pandas as pd
import os
import time


BASE_DIR = Path(__file__).parent.parent.parent 
DATA_DIR = BASE_DIR / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
PROMPTS_DIR = BASE_DIR / "prompts"

load_dotenv(BASE_DIR / ".env")
client = OpenAI(api_key=os.environ["API_KEY"])
df = pd.DataFrame(columns=["user_story", "model","prompt", "response", "time"])


def get_template(user_story: str, template: str):
    return f"{template}\n\n{user_story}"


def send_to_openai(prompt: str, model: str):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )
    return response.choices[0].message.content


def get_file(file_path: str) -> str:
    with open(file_path, "r") as f:
        return f.read()

def get_prompt() -> str:
    return get_file(PROMPTS_DIR / "prompt.txt")


def process_user_stories(file_path: PosixPath, model: str):
    start_time = time.time()
    try:
        print(f"Processing user stories from {file_path.name} with model {model[:20]}")
        user_stories = get_file(file_path)
        
        prompt = get_prompt()
        template = get_template(user_stories, prompt)
        
        print(f"Sending request to OpenAI with model {model[:20]}")
        response = send_to_openai(template, model)
        
        df.loc[len(df)] = [user_stories, model, prompt, response, time.time() - start_time]

        print(f"Successfully processed {file_path.name} with {model[:20]}")
        print(f"Time taken: {time.time() - start_time}")

    except FileNotFoundError as e:
        print(f"Error: File not found - {file_path.name}: {e}")
        save_df()
    except Exception as e:  
        print(f"Error processing {file_path.name} with {model[:20]}: {e}")
        save_df()


def save_df():
    df.to_excel(PROCESSED_DIR / "data_processed2.xlsx", index=False)


if __name__ == "__main__":
    try:
        models = ["gpt-5-mini", "gpt-4", "gpt-5"]
        user_stories = ["g28-zooniverse.txt"]

        for model in models:
            for user_story in user_stories:
                process_user_stories(DATA_RAW_DIR / user_story, model)

    finally:
        save_df()

