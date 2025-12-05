#!/bin/bash

# Ensure script is run with bash
if [ -z "$BASH_VERSION" ]; then
    echo "[ERROR] Please run this script using bash:  bash install.sh"
    exit 1
fi

# Configuration variables
MINICONDA_INSTALL_DIR="$HOME/miniconda3"
MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
ENVIRONMENT_FILE="environment.yml"
ENV_NAME="opifex"

SYSTEM_DEPS=(
    "wget"
    "libxcb-xinerama0"
    "libxcb-cursor0"
    "libxkbcommon-x11-0"
    "libxcb-icccm4"
    "libxcb-image0"
    "libxcb-keysyms1"
    "libxcb-render-util0"
    "libxcb-shape0"
)

ARCHIVE_URL="https://pub-1fc150304f4047f387be7b92d6b089a9.r2.dev/source.tar.gz"
PIPER_PATH="source/piper/piper"

NEW_DIRS=(
    "generated"
    "generated/voice"
    "generated/video"
    "temp"
)

FILES_CHECK=(
    "$ENVIRONMENT_FILE"
    "main.py"
    "README.md"
    "basemodule.py"
)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

conda_env_exists() {
    conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"
}

check_system_deps() {
    local missing=()
    for dep in "${SYSTEM_DEPS[@]}"; do
        if ! dpkg -l | grep -q "^ii  ${dep}"; then
            missing+=("$dep")
        fi
    done
    if [ ${#missing[@]} -eq 0 ]; then
        return 0
    else
        echo "${missing[@]}"
        return 1
    fi
}

install_system_deps() {
    print_info "Updating package list..."
    sudo apt update || {
        print_error "Failed to update package list"
        return 1
    }

    print_info "Installing missing system dependencies..."
    sudo apt install -y "${SYSTEM_DEPS[@]}" || {
        print_error "Failed to install system dependencies"
        return 1
    }
}

install_miniconda() {
    print_info "Installing Miniconda3 to $MINICONDA_INSTALL_DIR..."

    mkdir -p "$MINICONDA_INSTALL_DIR" || {
        print_error "Failed to create directory $MINICONDA_INSTALL_DIR"
        return 1
    }

    wget "$MINICONDA_URL" -O "$MINICONDA_INSTALL_DIR/miniconda.sh" || {
        print_error "Failed to download Miniconda"
        return 1
    }

    bash "$MINICONDA_INSTALL_DIR/miniconda.sh" -b -u -p "$MINICONDA_INSTALL_DIR" || {
        print_error "Failed to install Miniconda"
        return 1
    }

    rm -f "$MINICONDA_INSTALL_DIR/miniconda.sh"

    source "$MINICONDA_INSTALL_DIR/etc/profile.d/conda.sh"
    conda init bash >/dev/null 2>&1

    print_info "Miniconda installed successfully"
}

setup_conda_env() {
    if conda_env_exists; then
        print_warn "Conda environment '$ENV_NAME' already exists"
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            conda env remove -n "$ENV_NAME"
            conda env create -f "$ENVIRONMENT_FILE" || {
                print_error "Failed to create conda environment"
                return 1
            }
        fi
    else
        print_info "Creating conda environment from $ENVIRONMENT_FILE..."
        conda env create -f "$ENVIRONMENT_FILE" || {
            print_error "Failed to create conda environment"
            return 1
        }
    fi

    print_info "Conda environment setup completed"
}

download_and_extract() {
    local archive_name
    archive_name=$(basename "$ARCHIVE_URL")
    local temp_dir
    temp_dir=$(mktemp -d)

    print_info "Downloading program archive..."
    wget -O "$temp_dir/$archive_name" "$ARCHIVE_URL" || {
        print_error "Failed to download archive"
        rm -rf "$temp_dir"
        return 1
    }

    print_info "Extracting archive to source/..."
    mkdir -p source
    tar -xzf "$temp_dir/$archive_name" -C source || {
        print_error "Failed to extract archive"
        rm -rf "$temp_dir"
        return 1
    }

    rm -rf "$temp_dir"
    print_info "Archive extracted successfully"
}

create_launcher() {
    print_info "Creating main.sh launcher..."

    cat > main.sh << EOF
#!/usr/bin/env bash

SCRIPT_DIR=\$( cd -- "\$( dirname -- "\${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "\$SCRIPT_DIR"

source "$MINICONDA_INSTALL_DIR/bin/activate"
conda activate "$ENV_NAME"

python3 main.py single gui
EOF

    chmod +x main.sh
    print_info "Launcher created successfully"
}

main() {
    print_info "Starting installation process..."

    print_info "Verifying installation directory..."
    for file in "${FILES_CHECK[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "Required file '$file' not found."
            exit 1
        fi
    done

    print_info "Installation directory verification passed."
    echo
    print_info "The following will be installed/configured:"
    echo "  - Miniconda3 (if missing)"
    echo "  - Conda environment: $ENV_NAME"
    echo "  - System dependencies"
    echo "  - Program source files"
    echo

    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    [[ ! $REPLY =~ ^[Yy]$ ]] && {
        print_info "Installation cancelled."
        exit 0
    }

    if command_exists conda; then
        print_info "Conda found: $(which conda)"
        eval "$(conda shell.bash hook)"
    else
        print_warn "Conda not found — installing Miniconda."
        install_miniconda || exit 1
        source "$MINICONDA_INSTALL_DIR/etc/profile.d/conda.sh"
    fi

    setup_conda_env || exit 1

    print_info "Checking system dependencies..."
    missing_deps=$(check_system_deps)

    if [ $? -ne 0 ]; then
        print_warn "Missing dependencies: $missing_deps"
        sudo true || { print_error "sudo failed"; exit 1; }
        install_system_deps || exit 1
    else
        print_info "All system dependencies installed."
    fi

    download_and_extract || exit 1

    if [ -f "$PIPER_PATH" ]; then
        chmod +x "$PIPER_PATH"
    fi

    create_launcher || exit 1

    print_info "Creating runtime directories..."
    for dir in "${NEW_DIRS[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
        fi
    done

    echo
    print_info "Installation completed successfully!"
    echo "Run with:  bash main.sh"
    echo
}

main "$@"

