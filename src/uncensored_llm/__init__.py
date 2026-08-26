import ollama
import os
import webbrowser
import sys
import re

help_text = """Commands:
 /help, /h              Show help
 /quit, /exit, /q       Exit
 /clear, /cls, /c       Clear screen
 /models                List models
 /model <model_name>    Switch model\n"""

UNCENSORED_MODELS = {
    "Fully uncensored": [
        {
            "name": "llama2-uncensored",
            "desc": "Uncensored Llama 2 model by George Sung and Jarrad Hope.",
            "sizes": ["7b", "70b"],
        },
    ],
    "Partially uncensored": [
        {
            "name": "dolphin-mistral",
            "desc": "Uncensored Dolphin model based on Mistral, excels at coding.",
            "sizes": ["7b"],
        },
    ],
    "Unverified": [
        {
            "name": "wizardlm-uncensored",
            "desc": "Uncensored version of Wizard LM model.",
            "sizes": ["13b"],
        },
        {
            "name": "wizard-vicuna-uncensored",
            "desc": "Wizard Vicuna Uncensored based on Llama 2 uncensored.",
            "sizes": ["7b", "13b", "30b"],
        },
        {
            "name": "dolphincoder",
            "desc": "Uncensored Dolphin variant, excels at coding, based on StarCoder2.",
            "sizes": ["7b", "15b"],
        },
        {
            "name": "dolphin-phi",
            "desc": "Uncensored Dolphin model based on Microsoft Research Phi.",
            "sizes": ["2.7b"],
        },
        {
            "name": "dolphin-mixtral",
            "desc": "Uncensored Mixtral variant, excels at coding tasks.",
            "sizes": ["8x7b", "8x22b"],
        },
        {
            "name": "everythinglm",
            "desc": "Uncensored Llama2 based model with 16K context window.",
            "sizes": ["13b"],
        },
    ],
}


def is_ollama_installed() -> bool:
    try:
        ollama.list()
        return True
    except Exception:
        return False


def prompt_ollama_install() -> bool:
    print("Ollama is not installed.")
    response = input("Do you want to visit the Ollama download page? (y/n): ").lower()
    if response == "y":
        webbrowser.open("https://ollama.com/download")
    return False


def get_input_safe(prompt: str) -> str:
    content = input(prompt)
    return re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", content)


def get_last_used_model() -> str:
    try:
        with open("last_used_model.txt", "r") as f:
            last_model = f.read().strip()

        available_models = [m["model"] for m in ollama.list()["models"]]
        if last_model in available_models:
            return last_model
        else:
            return available_models[0] if available_models else None
    except FileNotFoundError:
        models = ollama.list()["models"]
        return models[0]["model"] if models else None


def save_model(model_name: str) -> None:
    with open("last_used_model.txt", "w") as f:
        f.write(model_name)


def print_models() -> None:
    models_list = ollama.list()['models']
    installed = {m['model'] for m in models_list}
    
    if installed:
        print("Installed models:")
        for m in models_list:
            print(f" - {m['model']}")
    else:
        print("No models installed")

    print("\nAvailable uncensored models:")
    first_category = True
    for category, models in UNCENSORED_MODELS.items():
        if not first_category:
            print()
        print(f"  {category}:")
        first_category = False
        for model in models:
            sizes_str = ", ".join(model["sizes"])
            print(f"    - {model['name']}: {model['desc']} ({sizes_str})")
    print()


def main() -> None:
    if not is_ollama_installed():
        if not prompt_ollama_install():
            sys.exit(0)
        return

    model = get_last_used_model()
    print(f"Model: {model or 'None'}")
    print(f"\n{help_text}")

    try:
        while True:
            content = get_input_safe("> ")

            if not content:
                continue

            if content in ["/help", "/h"]:
                print(help_text)
            elif content in ["/quit", "/exit", "/q"]:
                break
            elif content in ["/clear", "/cls", "/c"]:
                os.system("cls" if os.name == "nt" else "clear")
            elif content == "/models":
                print_models()
            elif content.startswith("/model "):
                model_name = content.split(" ", 1)[1]
                models = [m["model"] for m in ollama.list()["models"]]
                if model_name in models:
                    model = model_name
                    save_model(model)
                    print(f"Switched to: {model}\n")
                else:
                    print(f"Model not found\n")
            else:
                if not model:
                    model = ollama.list()["models"][0]["model"]

                stream = ollama.chat(
                    model=model,
                    messages=[{"role": "user", "content": content}],
                    stream=True,
                )
                print("\nAI: ", end="", flush=True)
                for chunk in stream:
                    print(chunk["message"]["content"], end="", flush=True)
                print("\n")

    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        print("\nExiting...\n")


if __name__ == "__main__":
    main()
