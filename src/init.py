# /// script
# dependencies = [
#   "pyyaml",
#   "loguru"
# ]
# ///

import os
import sys
import shutil
import subprocess
from pathlib import Path
import yaml
import argparse
from loguru import logger
from typing import Optional, Literal


def setup_logger(
    filename: Optional[str] = None, level: Literal["INFO", "DEBUG", "WARNING"] = "INFO"
):
    format = "{time:YYYY-MM-DD - HH:mm:ss} - {file}:{line} - {level} - {message}"
    logger.remove()
    handler_id = logger.add(
        sys.stdout,
        colorize=False,
        format=format,
        level=level,
    )
    if filename:
        logger.add(filename, format=format, mode="w", level=level)
        logger.info("Log file: {}", filename)
        logger.remove(handler_id)


def backup_file(file_path):
    if file_path.exists():
        counter = 0
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        while backup_path.exists():
            counter += 1
            backup_path = file_path.with_suffix(file_path.suffix + f".bak{counter}")
        shutil.copy(file_path, backup_path)
        logger.info(f"Backup created: {backup_path}")
    else:
        logger.warning(f"{file_path} does not exist.")


def run_command(command: list[str], check=True, shell=False):
    subprocess.run(command, check=check, shell=shell)


def create_symlink(src: Path, dest: Path):
    """
    Creates a symbolic link from `src` to `dest`. If `dest` already exists, it handles the situation
    based on the type of `dest`:

    - If `dest` is a symlink, it is removed and replaced with a new symlink pointing to `src`.
    - If `dest` is a directory:
        - If `src` does not exist, `dest` is renamed to `src`.
        - If `src` exists, `dest` is removed (with a warning) and replaced with a symlink to `src`.
    - If `dest` is any other type (e.g., a file), a `ValueError` is raised.

    Args:
        src (Path): The source path for the symbolic link.
        dest (Path): The destination path where the symbolic link will be created.

    Raises:
        ValueError: If `dest` exists and is not a symlink or directory.
    """
    if not dest.exists():
        os.symlink(src, dest)
        return

    if dest.is_symlink():
        dest.unlink()
    elif dest.is_dir():
        if not src.exists():
            dest.rename(src)
        else:
            logger.warning(f"{dest} already exists and it is removed.")
            shutil.rmtree(dest)
    else:
        raise ValueError(f"{dest} exists and is not a symlink or directory.")

    os.symlink(src, dest)


def initialize_oh_my_zsh(
    workspace_directory: Path, home_dir: Path, config: dict
) -> tuple[Path, Path]:
    """
    Initializes Oh My Zsh by creating a symlink to the work directory and installing Oh My Zsh.
    Also backs up the existing .zshrc file and Oh My Zsh installation if specified in the config.
    Args:
        workspace_directory (Path): The work directory where Oh My Zsh will be installed.
        home_dir (Path): The home directory of the user.
        config (dict): The configuration dictionary containing Oh My Zsh settings.
    Returns:
        zshrc_file (Path): The path to the .zshrc file.
    """

    # Remove ZSH-related environment variables
    zsh_env_vars = {
        key: value for key, value in os.environ.items() if key.startswith("ZSH")
    }
    for var in zsh_env_vars:
        del os.environ[var]
        logger.info(f"Removed environment variable: {var}")

    # Backup existing .zshrc file if needed.
    zshrc_file = home_dir / ".zshrc"
    if config.get("backup_zshrc", True):
        backup_file(zshrc_file)

    # Clean up existing installation paths for oh-my-zsh.
    oh_my_zsh_dir = home_dir / ".oh-my-zsh"
    if oh_my_zsh_dir.is_symlink():
        oh_my_zsh_dir.unlink()
    if oh_my_zsh_dir.exists():
        shutil.rmtree(oh_my_zsh_dir)

    # Clean up installation path.
    zsh_installation_path = workspace_directory / ".oh-my-zsh"
    if zsh_installation_path.exists():
        shutil.rmtree(zsh_installation_path.resolve())
    os.environ["ZSH"] = str(zsh_installation_path)

    logger.info("Attempting to install oh-my-zsh...")

    run_command(
        'sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended',
        shell=True,
    )

    logger.info("Oh-my-zsh installed!")

    logger.info(f"Creating symlink: {oh_my_zsh_dir} --> {zsh_installation_path}")
    os.symlink(zsh_installation_path, oh_my_zsh_dir)

    logger.info("Initializing oh-my-zsh plugins...")

    # Copy custom .zshrc
    custom_zshrc = Path(config["custom_zshrc"])
    if not custom_zshrc.exists():
        raise FileNotFoundError(
            f"Error: Custom .zshrc file {custom_zshrc} not found.",
        )

    shutil.copy(custom_zshrc, zshrc_file)

    # Update Oh My Zsh installation path
    with zshrc_file.open("r+") as f:
        content = f.read()
        content = content.replace(
            'export ZSH="${ZSH_INSTALLATION_PATH}"',
            f'export ZSH="{zsh_installation_path}"',
        )
        f.seek(0)
        f.write(content)
        f.truncate()

    # Update cache directory
    xdg_cache_home = workspace_directory / ".cache"
    xdg_cache_home.mkdir(parents=True, exist_ok=True)
    with zshrc_file.open("r+") as f:
        content = f.read()
        content = content.replace(
            'export XDG_CACHE_HOME=""', f'export XDG_CACHE_HOME="{xdg_cache_home}"'
        )
        f.seek(0)
        f.write(content)
        f.truncate()

    # Install Zsh plugins
    zsh_custom = zsh_installation_path / "custom"
    for plugin in config["zsh_plugins"]:
        plugin_path = zsh_custom / "plugins" / plugin["name"]
        if not plugin_path.exists():
            run_command(["git", "clone", plugin["repo"], str(plugin_path)])

    logger.info("Initialized oh-my-zsh plugins!")

    return zshrc_file, zsh_custom


def initialize_pixi(
    workspace_directory: Path, home_dir: Path, config: dict, zshrc_file: Path
):
    """
    Initializes Pixi by creating a symlink to the work directory and installing Pixi.
    Also updates the .zshrc file to include the Pixi bin directory in the PATH.
    Args:
        workspace_directory (Path): The work directory where Pixi will be installed.
        home_dir (Path): The home directory of the user.
        config (dict): The configuration dictionary containing Pixi settings.
        zshrc_file (Path): The path to the .zshrc file to be updated.
    """
    # Remove PIXI-related environment variables
    zsh_env_vars = {
        key: value for key, value in os.environ.items() if key.startswith("PIXI")
    }
    for var in zsh_env_vars:
        del os.environ[var]
        logger.info(f"Removed environment variable: {var}")

    # Install Pixi
    pixi_home = workspace_directory / ".pixi_home"

    pixi_symlink = home_dir / ".pixi"
    if pixi_symlink.is_symlink():
        pixi_symlink.unlink()
    elif pixi_symlink.exists():
        shutil.rmtree(pixi_symlink)
    pixi_home.mkdir(parents=True, exist_ok=True)
    os.symlink(pixi_home, home_dir / ".pixi")

    pixi_bin = home_dir / ".pixi" / "bin"

    run_command("curl -fsSL https://pixi.sh/install.sh | bash", shell=True)
    with zshrc_file.open("r+") as f:
        content = f.read()
        content = content.replace(
            "export PATH=${PIXI_BIN}:$PATH", f"export PATH={pixi_bin}:$PATH"
        )
        f.seek(0)
        f.write(content)
        f.truncate()

    os.environ["PATH"] = f"{pixi_bin}:{os.environ['PATH']}"
    logger.info("Installed pixi")

    # Install useful tools
    for tool in config.get("pixi_packages", []):
        run_command(["pixi", "global", "install", tool])
        run_command(["pixi", "global", "update", tool])


def main():
    # Setup logger
    setup_logger(level="INFO")

    # Use argparse to parse the config file path
    parser = argparse.ArgumentParser(description="Setup Oh My Zsh and related tools.")
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the YAML configuration file.",
    )
    parser.add_argument(
        "-w",
        "--workspace",
        required=True,
        help="Disk location to use as the workspace.",
        default="~/workspace",
    )
    args = parser.parse_args()

    config_file = Path(args.config).resolve()
    if not config_file.exists():
        raise (f"Error: Configuration file {config_file} not found.")

    with config_file.open("r") as f:
        config = yaml.safe_load(f)

    workspace_directory = Path(args.workspace).resolve()
    logger.info(f"Workspace directory set to: {workspace_directory}")
    logger.info(f"Configuration file set to: {config_file}")

    proxy = config.get("proxy", "")
    if proxy:
        os.environ["http_proxy"] = proxy
        os.environ["https_proxy"] = proxy

    home_dir = Path.home()

    zshrc_file, zsh_custom = initialize_oh_my_zsh(
        workspace_directory=workspace_directory, home_dir=home_dir, config=config
    )

    initialize_pixi(
        workspace_directory=workspace_directory,
        home_dir=home_dir,
        config=config,
        zshrc_file=zshrc_file,
    )

    # Setup autocomplete for `just`
    just_path = shutil.which("just")
    logger.info(f"Just path: {just_path}")
    if just_path:
        run_command(f"just --completions zsh >{zsh_custom}/just.zsh", shell=True)
        logger.info(f"Installed just completions for {just_path}")

    # Append additional config to .zshrc
    for additional_config in config.get("additional_configs", []):
        additional_config = Path(additional_config).resolve()
        if not additional_config.exists():
            print(
                f"Error: Additional config file {additional_config} not found.",
                file=sys.stderr,
            )
            sys.exit(1)
        else:
            with additional_config.open("r") as src, zshrc_file.open("a") as dest:
                dest.write(src.read())

    logger.info(f"Final .zshrc file: {zshrc_file}")


if __name__ == "__main__":
    main()
