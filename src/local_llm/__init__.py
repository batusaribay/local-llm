import ollama
import os
import webbrowser
import sys
import re
import json
from pathlib import Path
from rich.console import Console

console = Console()


def get_config_path() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "local-llm" / "config.json"


CONFIG_PATH = get_config_path()
MODELS_PATH = Path(__file__).parent / "models.json"

ASCII_ART = r""" _                    _       _     _     __  __ 
| |    ___   ___ __ _| |     | |   | |   |  \/  |
| |   / _ \ / __/ _` | |_____| |   | |   | |\/| |
| |__| (_) | (_| (_| | |_____| |___| |___| |  | |
|_____\___/ \___\__,_|_|     |_____|_____|_|  |_|
"""

help_text = """Help:
 General:
  /help, /h              Show help
  /quit, /exit, /q       Exit
  /clear, /cls, /c       Clear screen

 Models:
  /models                List models
  /model                 Show current model
  /switch <model>        Switch model
  /install <model>       Install model

 Appearance:
  /colors                List colors, shows current
  /set <color>           Set response color
"""

AVAILABLE_COLORS = [
    "white", "red", "green", "yellow", "blue", "magenta", "cyan",
    "bright_red", "bright_green", "bright_yellow", "bright_blue",
    "bright_magenta", "bright_cyan"
]


def print_banner() -> None:
    print(ASCII_ART)


def load_models() -> dict:
    try:
        with open(MODELS_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: models.json not found at {MODELS_PATH}\n")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: models.json is invalid\n")
        sys.exit(1)


def load_config() -> dict:
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_used_model": None, "response_color": "yellow"}


def save_config(config: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


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


def get_last_used_model(config: dict) -> str | None:
    last_model = config.get("last_used_model")
    available_models = [m["model"] for m in ollama.list()["models"]]

    if last_model and last_model in available_models:
        return last_model
    return available_models[0] if available_models else None


def print_models(uncensored_models: dict) -> None:
    models_list = ollama.list()["models"]

    if models_list:
        print("Installed models:")
        for m in models_list:
            print(f" - {m['model']}")
    else:
        print("No models installed")

    print("\nAvailable models:")
    first_category = True
    for category, models in uncensored_models.items():
        if not first_category:
            print()
        print(f"  {category}:")
        first_category = False
        for model in models:
            sizes_str = ", ".join(model["sizes"])
            print(f"    - {model['name']}: {model['desc']} ({sizes_str})")
    print()


def print_colors(current_color: str) -> None:
    print("Colors:")
    for color in AVAILABLE_COLORS:
        marker = " (current)" if color == current_color else ""
        console.print(f"  {color}{marker}", style=color, markup=False, highlight=False)
    print()


def install_model(model_name: str) -> bool:
    try:
        response = ollama.pull(model_name)
        status = response.get("status") if isinstance(response, dict) else None
        if status != "success":
            print(f"Install did not complete: {status or 'unknown status'}\n")
            return False
        print(f"Successfully installed {model_name}\n")
        return True
    except ollama.ResponseError as e:
        print(f"Failed to install {model_name}: {e.error}\n")
        return False
    except Exception as e:
        print(f"Failed to install {model_name}: {e}\n")
        return False


def main() -> None:
    if not is_ollama_installed():
        if not prompt_ollama_install():
            sys.exit(0)
        return

    uncensored_models = load_models()
    config = load_config()
    model = get_last_used_model(config)
    response_color = config.get("response_color", "yellow")

    print_banner()
    should_exit = False

    try:
        while True:
            content = get_input_safe("> ")

            if not content:
                continue

            parts = content.split(" ", 1)
            command = parts[0]
            argument = parts[1].strip() if len(parts) > 1 else ""

            # /quit and /exit shouldn't print a leading blank line before exiting
            if command in ["/quit", "/exit", "/q"]:
                should_exit = True
                break

            print()

            if command in ["/help", "/h"]:
                print(help_text)

            elif command in ["/clear", "/cls", "/c"]:
                os.system("cls" if os.name == "nt" else "clear")
                print_banner()

            elif command == "/models":
                print_models(uncensored_models)

            elif command == "/model":
                print(f"Current model: {model or 'none'}\n")

            elif command == "/switch":
                if not argument:
                    print("Usage: /switch <model>\n")
                    continue
                models = [m["model"] for m in ollama.list()["models"]]
                if argument in models:
                    model = argument
                    config["last_used_model"] = model
                    save_config(config)
                    print(f"Switched to: {model}\n")
                else:
                    print(f"Model not found. Use /install {argument} to install it first\n")

            elif command == "/install":
                if not argument:
                    print("Usage: /install <model>\n")
                    continue
                print(f"Installing {argument}...")
                if install_model(argument):
                    if not model:
                        model = argument
                        config["last_used_model"] = model
                        save_config(config)

            elif command == "/colors":
                print_colors(response_color)

            elif command == "/set":
                if not argument:
                    print("Usage: /set <color>\n")
                    continue
                if argument in AVAILABLE_COLORS:
                    response_color = argument
                    config["response_color"] = argument
                    save_config(config)
                    print(f"Response color set to: {argument}\n")
                else:
                    print("Color not found. Use /colors to see available colors\n")

            elif command.startswith("/"):
                print(f"Unknown command: {command}\n")

            else:
                if not model:
                    print("No model available. Use /install <model> first\n")
                    continue

                try:
                    stream = ollama.chat(
                        model=model,
                        messages=[{"role": "user", "content": content}],
                        stream=True,
                    )
                    print(f"{model}: ", end="")
                    try:
                        for chunk in stream:
                            console.print(
                                chunk["message"]["content"],
                                style=response_color,
                                end="",
                                markup=False,
                                highlight=False,
                            )
                        print("\n")
                    except KeyboardInterrupt:
                        print("\n[Response stopped]\n")
                except ollama.ResponseError as e:
                    print(f"Error: {e.error}\n")
                except Exception as e:
                    print(f"Error: {e}\n")

    except (KeyboardInterrupt, EOFError):
        should_exit = True

    if should_exit:
        print("\nExiting...\n")
    else:
        print("Exiting...\n")


if __name__ == "__main__":
    main()