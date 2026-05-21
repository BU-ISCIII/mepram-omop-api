#!/bin/bash
set -euo pipefail

APP_VERSION="1.0.0"

usage() {
cat << EOF
This script installs and upgrades the MePRAM API application.

usage : $0 --upgrade --git_revision --conf
    Optional input data:
    --install             | Install MePRAM API full/dep/app
    --upgrade             | Upgrade MePRAM API full/dep/app
    --stage               | Stage app files only (install/upgrade) without DB work. Internal/container use.
    --bootstrap           | Run DB/bootstrap steps only (install/upgrade) against an existing staged app. Internal/container use.
    --git_revision        | Git revision name to run (branch, tag, commit SHA, or 'current' to use copied local sources as-is)
    --conf                | Select custom configuration file. Default: ./install_settings.txt
    --dashboard_sql       | Import dashboard.sql after migrations
    --skip_dashboard_sql  | Skip dashboard.sql import
    --docker              | Deprecated. Use --skip_apache_restart to avoid Apache checks/restart.

Examples:
    Install only software dependencies for MePRAM API
    sudo $0 --install dep

    Install only MePRAM API app
    $0 --install app

    Upgrade using develop code
    $0 --upgrade full --git_revision develop

    Stage application files during a container image build
    $0 --stage install --git_revision develop --conf conf/docker_test_settings.txt

    Bootstrap database/static using an already staged container image
    $0 --bootstrap upgrade --git_revision develop --conf conf/docker_test_settings.txt

    Bootstrap and import dashboard data
    $0 --bootstrap install --conf conf/docker_test_settings.txt --dashboard_sql /data/dashboard.sql
EOF
}

_log_compose_entry() {
    local level="$1"; shift
    local message="$*"
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    printf "%s [%s] %s" "$timestamp" "$level" "$message"
}

log() {
    local level="$1"; shift
    printf "%s\n" "$(_log_compose_entry "$level" "$*")"
}

log_section() {
    local message="$1"
    log "INFO" "$message"
    printf "\n\n%s\n" "${YELLOW}------------------${NC}"
    printf "%b\n" "${YELLOW}${message}${NC}"
    printf "%s\n\n" "${YELLOW}------------------${NC}"
}

log_info() {
    printf "%b\n" "${BLUE}$(_log_compose_entry "INFO" "$1")${NC}"
}

log_warn() {
    printf "%b\n" "${CYAN}$(_log_compose_entry "WARN" "$1")${NC}"
}

log_error() {
    printf "%b\n" "${RED}$(_log_compose_entry "ERROR" "$1")${NC}"
}

abort_install() {
    log_error "$1"
    exit "${2:-1}"
}

ensure_file_exists() {
    local file_path="$1"
    local friendly_name="${2:-$1}"
    if [ ! -f "$file_path" ]; then
        abort_install "Required file '$friendly_name' not found."
    fi
}

python_check() {
    local python_version
    python_version=$($PYTHON_BIN_PATH --version 2>&1 || true)
    if [[ $python_version == "" ]]; then
        abort_install "Python3 is not found in your system"
    fi
    local major minor
    major=$(echo "$python_version" | awk '{print $2}' | cut -d"." -f1)
    minor=$(echo "$python_version" | awk '{print $2}' | cut -d"." -f2)
    if (( major < 3 || (major == 3 && minor < 10) )); then
        abort_install "MePRAM API requires at least Python 3.10. Found: $python_version"
    fi
}

root_check() {
    if [[ $EUID -ne 0 ]]; then
        abort_install "Exiting installation. This script must be run as root for dependency installation"
    fi
}

db_check() {
    log "INFO" "Checking database connectivity against ${MEPRAM_DB_HOST:-localhost}:${MEPRAM_DB_PORT:-3306}"
    $PYTHON_BIN_PATH - << PY
import os
import MySQLdb

conn = MySQLdb.connect(
    host=os.environ.get("MEPRAM_DB_HOST", "localhost"),
    port=int(os.environ.get("MEPRAM_DB_PORT", "3306")),
    user=os.environ.get("MEPRAM_DB_USER", "mepram"),
    passwd=os.environ.get("MEPRAM_DB_PASSWORD", "mepram_password"),
    db=os.environ.get("MEPRAM_DB_NAME", "mepram_api"),
)
conn.close()
PY
}

install_system_packages() {
    if [ "${SKIP_SYSTEM_PACKAGES:-}" = "1" ]; then
        echo "Skipping system package installation (SKIP_SYSTEM_PACKAGES=1)"
        return
    fi

    if command -v apt-get >/dev/null 2>&1; then
        echo "Software installation for Debian/Ubuntu"
        apt-get update
        apt-get install -y \
            build-essential \
            default-libmysqlclient-dev \
            pkg-config \
            python3-dev \
            python3-pip \
            python3-venv
    elif command -v yum >/dev/null 2>&1; then
        echo "Software installation for CentOS/RedHat"
        yum groupinstall -y "Development tools"
        yum install -y \
            mariadb-devel \
            pkgconf-pkg-config \
            python3-devel \
            python3-pip
    else
        log_warn "No supported system package manager found. Skipping system package installation."
    fi
}

ensure_git_safe_directory() {
    local repo_dir
    repo_dir="$(pwd -P)"

    if ! command -v git >/dev/null 2>&1; then
        return 0
    fi

    if [ -d "$repo_dir/.git" ] || [ -f "$repo_dir/.git" ]; then
        git config --global --add safe.directory "$repo_dir" >/dev/null 2>&1 || true
        git config --system --add safe.directory "$repo_dir" >/dev/null 2>&1 || true
    fi
}

restore_git_ref() {
    if ! command -v git >/dev/null 2>&1; then
        return 0
    fi
    if [ "${did_checkout_git_ref:-false}" = true ] && [ -n "${initial_git_ref:-}" ] && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "Restoring to initial git reference: $initial_git_ref"
        git checkout "$initial_git_ref" --quiet || true
    fi
}

checkout_git_revision() {
    if [[ "$git_branch" == "current" ]]; then
        printf "${YELLOW}Using copied local working tree without git checkout.${NC}\n"
        return 0
    fi
    if ! command -v git >/dev/null 2>&1; then
        printf "${YELLOW}Git is not installed. Using copied source tree as-is.${NC}\n"
        return 0
    fi
    if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        printf "${YELLOW}No git metadata found. Using copied source tree as-is.${NC}\n"
        return 0
    fi
    if git rev-parse --verify "$git_branch" >/dev/null 2>&1; then
        if [[ $git_branch != $initial_git_ref ]]; then
            local local_changes
            local_changes=$(git status --porcelain)
            if [[ -n $local_changes ]]; then
                abort_install "Unable to switch to $git_branch. Commit or stash local changes first."
            fi
            printf "${YELLOW}Switching to revision %s.${NC}\n" "$git_branch"
            git checkout "$git_branch" --quiet
            did_checkout_git_ref=true
        else
            printf "${YELLOW}Using current revision: '%s'.${NC}\n" "$git_branch"
        fi
    else
        abort_install "Git reference $git_branch is not defined in ${PWD}."
    fi
}

load_install_config() {
    ensure_file_exists "$conf" "$conf"
    set -a
    # shellcheck disable=SC1090
    . "$conf"
    set +a

    PYTHON_BIN_PATH="${PYTHON_BIN_PATH:-python3}"
    INSTALL_PATH="${APP_INSTALL_PATH:-${INSTALL_PATH:-/opt/mepram-api}}"
    PROJECT_NAME="${PROJECT_NAME:-conf}"
    REQUIRED_MODULES="${REQUIRED_MODULES:-conf core manage.py}"
    MEPRAM_DASHBOARD_SQL="${MEPRAM_DASHBOARD_SQL:-}"
}

sync_requirements_file() {
    mkdir -p "$INSTALL_PATH/conf"
    cp conf/requirements.txt "$INSTALL_PATH/conf/requirements.txt"
}

setup_virtualenv() {
    local mode="$1"
    cd "$INSTALL_PATH"
    if [ "$mode" = "install" ]; then
        if [ ! -d virtualenv ]; then
            "$PYTHON_BIN_PATH" -m venv virtualenv
        else
            echo "virtualenv already defined. Skipping."
        fi
    else
        if [ ! -d virtualenv ]; then
            "$PYTHON_BIN_PATH" -m venv virtualenv
        fi
    fi
    cd -
}

install_python_requirements() {
    cd "$INSTALL_PATH"
    echo "activate the virtualenv"
    source virtualenv/bin/activate
    echo "Installing required python packages"
    python -m pip install --upgrade pip
    python -m pip install wheel
    python -m pip install -r conf/requirements.txt
    cd -
}

ensure_virtualenv_ready() {
    if [ "$docker" = true ] && [ "$INSTALL_PATH" = "/app" ]; then
        return 0
    fi
    if [ ! -d "$INSTALL_PATH/virtualenv" ]; then
        abort_install "Virtualenv not found at $INSTALL_PATH/virtualenv. Run --install dep first."
    fi
}

activate_python_environment() {
    if [ -d "$INSTALL_PATH/virtualenv" ]; then
        echo "activate the virtualenv"
        source "$INSTALL_PATH/virtualenv/bin/activate"
    fi
}

write_runtime_env_file() {
    local env_file="$INSTALL_PATH/.env"
    {
        echo "# Generated by install.sh. Runtime environment overrides these values."
        env | grep -E '^MEPRAM_' | sort || true
    } > "$env_file"
    chmod 644 "$env_file"
}

stage_application_files() {
    local mode="$1"
    log_section "Starting MePRAM API stage ${mode} version: ${APP_VERSION}"

    mkdir -p "$INSTALL_PATH"
    if [ "$INSTALL_PATH" != "$(pwd -P)" ]; then
        cp -R conf core "$INSTALL_PATH/"
        cp README.md LICENSE manage.py "$INSTALL_PATH/"
        cp -f Dockerfile pyproject.toml "$INSTALL_PATH/" 2>/dev/null || true
    fi
    write_runtime_env_file
}

run_django_deploy() {
    local mode="${1:-install}"

    cd "$INSTALL_PATH"
    activate_python_environment

    echo "Running Django system checks"
    python manage.py check

    if [ "$mode" = "upgrade" ]; then
        echo "Applying migrations in fake-initial mode"
        python manage.py migrate --noinput --fake-initial
        echo "Applying migrations"
        python manage.py migrate --noinput
    else
        echo "Applying migrations"
        python manage.py migrate --noinput
    fi

    local dashboard_sql_path="${dashboard_sql:-${MEPRAM_DASHBOARD_SQL:-}}"
    if [ -n "$dashboard_sql_path" ] && [ "$skip_dashboard_sql" = false ]; then
        ensure_file_exists "$dashboard_sql_path" "$dashboard_sql_path"
        echo "Importing dashboard SQL: $dashboard_sql_path"
        python manage.py import_dashboard_sql "$dashboard_sql_path" --truncate
    fi

    cd -
}

bootstrap_application_runtime() {
    local mode="$1"

    if [ ! -d "$INSTALL_PATH" ]; then
        abort_install "Unable to bootstrap application. Folder $INSTALL_PATH does not exist."
    fi

    if [ ! -f "$INSTALL_PATH/manage.py" ]; then
        abort_install "manage.py not found at $INSTALL_PATH/manage.py. Stage application files first."
    fi

    write_runtime_env_file
    run_django_deploy "$mode"
}

run_dependency_stage() {
    local mode="$1"

    if [ "$mode" = "install" ]; then
        log_section "Preparing dependency environment for installation"
        mkdir -p "$INSTALL_PATH"
    else
        log_section "Preparing dependency environment for upgrade"
        if [ ! -d "$INSTALL_PATH" ]; then
            abort_install "Unable to start the upgrade. Folder $INSTALL_PATH does not exist."
        fi
    fi

    install_system_packages
    sync_requirements_file
    setup_virtualenv "$mode"
    install_python_requirements
}

install_application_files() {
    stage_application_files "install"
    bootstrap_application_runtime "install"
    log_section "Successfuly MePRAM API Installation version: ${APP_VERSION}"
    echo "Installation completed"
}

upgrade_application_files() {
    if [ ! -d "$INSTALL_PATH" ]; then
        abort_install "Unable to start the upgrade. Folder $INSTALL_PATH does not exist."
    fi
    stage_application_files "upgrade"
    bootstrap_application_runtime "upgrade"
    log_section "Successfuly upgrade of MePRAM API version: ${APP_VERSION}"
}

check_requirements() {
    log_section "Checking main requirements"
    python_check
    log_info "Valid version of Python"
    if [[ "$operation_scope" == "full" || "$operation_scope" == "app" ]]; then
        db_check
        log_info "Successful check for database"
    fi

    if [ "$install_type" == "full" ] || [ "$install_type" == "dep" ] || [ "$upgrade_type" == "full" ] || [ "$upgrade_type" == "dep" ]; then
        log_warn "Checking requirement of root user when installation is full or dep"
        root_check
        log_info "Successful checking of root user"
    fi
}

check_stage_requirements() {
    log_section "Checking requirements for staged app preparation"
    python_check
    log_info "Valid version of Python"
}

check_bootstrap_requirements() {
    log_section "Checking requirements for application bootstrap"
    python_check
    log_info "Valid version of Python"
    db_check
    log_info "Successful check for database"
}

ensure_git_safe_directory
if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    initial_git_ref=$(git rev-parse --abbrev-ref HEAD || git rev-parse HEAD)
else
    initial_git_ref=""
fi
did_checkout_git_ref=false
trap restore_git_ref EXIT

YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

reset=true
for arg in "$@"
do
    if [ -n "${reset:-}" ]; then
      unset reset
      set --
    fi
    case "$arg" in
        --install)             set -- "$@" -i ;;
        --upgrade)             set -- "$@" -u ;;
        --stage)               set -- "$@" -j ;;
        --bootstrap)           set -- "$@" -l ;;
        --dashboard_sql)       set -- "$@" -d ;;
        --skip_dashboard_sql)  set -- "$@" -b ;;
        --git_revision)        set -- "$@" -g ;;
        --conf)                set -- "$@" -c ;;
        --docker)              set -- "$@" -k ;;
        --skip_apache_restart) set -- "$@" -a ;;
        --help)                set -- "$@" -h ;;
        --version)             set -- "$@" -v ;;
        *)                     set -- "$@" "$arg" ;;
    esac
done

git_branch=$initial_git_ref
conf="./install_settings.txt"
install=true
install_type="full"
upgrade=false
upgrade_type="full"
workflow="standard"
workflow_mode=""
docker=false
dashboard_sql=""
skip_dashboard_sql=false

options=":c:i:u:j:l:g:d:bkvha"
while getopts $options opt; do
    case $opt in
        i)
            workflow="standard"
            install=true
            upgrade=false
            if [[ "$OPTARG" == "full" || "$OPTARG" == "dep" || "$OPTARG" == "app" ]]; then
                install_type=$OPTARG
                upgrade_type=$OPTARG
            else
                echo "Install is not set to one valid option. Use: --install full/app/dep"
                exit 1
            fi
            ;;
        u)
            workflow="standard"
            install=false
            upgrade=true
            if [[ "$OPTARG" == "full" || "$OPTARG" == "dep" || "$OPTARG" == "app" ]]; then
                upgrade_type=$OPTARG
                install_type=$OPTARG
            else
                echo "Upgrade is not set to one valid option. Use: --upgrade full/app/dep"
                exit 1
            fi
            ;;
        j)
            workflow="stage"
            workflow_mode=$OPTARG
            if [[ "$workflow_mode" != "install" && "$workflow_mode" != "upgrade" ]]; then
                echo "Stage is not set to one valid option. Use: --stage install/upgrade"
                exit 1
            fi
            ;;
        l)
            workflow="bootstrap"
            workflow_mode=$OPTARG
            if [[ "$workflow_mode" != "install" && "$workflow_mode" != "upgrade" ]]; then
                echo "Bootstrap is not set to one valid option. Use: --bootstrap install/upgrade"
                exit 1
            fi
            ;;
        d) dashboard_sql=$OPTARG ;;
        b) skip_dashboard_sql=true ;;
        g) git_branch=$OPTARG ;;
        c) conf=$OPTARG ;;
        k) docker=true ;;
        a) ;;
        h)
            usage
            exit 1
            ;;
        v)
            echo $APP_VERSION
            exit 1
            ;;
        \?)
            echo "Invalid Option: -$OPTARG" 1>&2
            usage
            exit 1
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            exit 1
            ;;
        *)
            echo "Unimplemented option: -$OPTARG" >&2
            exit 1
            ;;
    esac
done
shift $((OPTIND-1))

operation="install"
operation_scope="$install_type"
if [ $upgrade == true ]; then
    operation="upgrade"
    operation_scope="$upgrade_type"
fi
if [ "$workflow" != "standard" ]; then
    operation="$workflow_mode"
    operation_scope="app"
fi

load_install_config
checkout_git_revision

if [ "$workflow" = "stage" ]; then
    check_stage_requirements
    stage_application_files "$workflow_mode"
    exit 0
fi

if [ "$workflow" = "bootstrap" ]; then
    check_bootstrap_requirements
    bootstrap_application_runtime "$workflow_mode"
    exit 0
fi

check_requirements

if [[ "$operation_scope" == "full" || "$operation_scope" == "dep" ]]; then
    run_dependency_stage "$operation"
    if [ "$operation_scope" = "dep" ]; then
        log_info "Dependency stage completed."
        exit 0
    fi
fi

if [[ "$operation_scope" == "full" || "$operation_scope" == "app" ]]; then
    if [ "$operation" = "install" ]; then
        install_application_files
    else
        upgrade_application_files
    fi
    exit 0
fi

printf "\n\n%s"
printf "${RED}------------------${NC}\n"
printf "%s"
printf "${RED}Invalid installation parameters${NC}\n"
printf "%s"
printf "${RED}------------------${NC}\n\n"
echo "See the usage examples"
usage
exit 1
