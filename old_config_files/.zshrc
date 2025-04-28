# Load Antigen for managing Zsh plugins
# source $HOME/.antigen/antigen.zsh
source $HOME/.antigen/antigen.zsh

# Plugins can be added here
antigen use oh-my-zsh

antigen bundle git
antigen bundle zsh-users/zsh-autosuggestions  # Autocomplete plugin
antigen bundle zsh-users/zsh-syntax-highlighting  # Syntax highlighting plugin

# Load the theme.
antigen theme robbyrussell

# Load the plugins
antigen apply

# Add custom scripts directory to fpath
fpath=($HOME/.zsh/custom-scripts $fpath)

# Initialize completion system
autoload -Uz compinit
compinit
