#!/usr/bin/env bash
set -euo pipefail

MEPRAM_VERSION="1.0.0"

usage() {
cat << EOF
This script installs and upgrades the MePRAM API in containers.

Usage : $0 [--dashboard_sql] [--git_revision] [--compose_file] [--install_conf] [--install_conf_map] [--action] [--engine] [--test]
    Optional input data:
    --dashboard_sql      | Path to dashboard.sql to import after migrations
    --git_revision       | Specify the Git revision to install (default: develop, or 'current' to use copied local sources)
    --compose_file       | Compose file to use (overrides default)
    --install_conf       | Settings file consumed during container image build/runtime
    --install_conf_map   | Service-specific settings file: service,path (can be repeated). Valid service: mepram_api
    --action             | install (default) or upgrade, to control bootstrap mode
    --skip_dashboard_sql | Skip dashboard SQL import even if --dashboard_sql is provided
    --engine             | Container engine to use: docker (default) or podman
    --test               | Use development/test compose file and test settings

Examples:
    Install test stack
    bash $0 --test

    Install test stack from current local committed sources without checking out a branch in-container
    bash $0 --test --git_revision current

    Install and import dashboard data
    bash $0 --test --dashboard_sql /path/to/dashboard.sql

    Upgrade an existing deployment using the same database
    bash $0 --install_conf conf/docker_test_settings.txt --action upgrade

EOF
}

reset=true

for arg in "$@"
do
    if [ -n "${reset:-}" ]; then
      unset reset
      set --
    fi
    case "$arg" in
        --dashboard_sql)      set -- "$@" -d ;;
        --git_revision)       set -- "$@" -g ;;
        --compose_file)       set -- "$@" -c ;;
        --install_conf)       set -- "$@" -s ;;
        --install_conf_map)   set -- "$@" -j ;;
        --action)             set -- "$@" -a ;;
        --skip_dashboard_sql) set -- "$@" -n ;;
        --test)               set -- "$@" -p ;;
        --engine)             set -- "$@" -e ;;
        --help)               set -- "$@" -h ;;
        --version)            set -- "$@" -v ;;
        *)                    set -- "$@" "$arg" ;;
    esac
done

dashboard_sql=""
git_revision="develop"
compose_file=""
install_conf=""
install_conf_container=""
install_conf_map_entries=()
skip_dashboard_sql=false
mode="production"
action="install"
engine="docker"

ENGINE_CMD=()
COMPOSE_CMD=()

set_engine() {
    if [ "$engine" = "docker" ]; then
        if ! command -v docker >/dev/null 2>&1; then
            echo "docker not found. Install docker or use --engine podman."
            exit 1
        fi
        ENGINE_CMD=("docker")
        COMPOSE_CMD=("docker" "compose")
    else
        if ! command -v podman >/dev/null 2>&1; then
            echo "podman not found. Install podman or use --engine docker."
            exit 1
        fi
        ENGINE_CMD=("podman")
        if command -v podman-compose >/dev/null 2>&1; then
            COMPOSE_CMD=("podman-compose")
        elif podman compose version >/dev/null 2>&1; then
            COMPOSE_CMD=("podman" "compose")
        else
            echo "podman compose not available. Install podman-compose or use --engine docker."
            exit 1
        fi
    fi
}

engine_exec() {
    "${ENGINE_CMD[@]}" "$@"
}

compose_exec() {
    "${COMPOSE_CMD[@]}" "$@"
}

read_install_conf_value() {
    local key="$1"
    local file="$2"

    bash -c '
        set -a
        . "$1"
        key="$2"
        printf "%s" "${!key-}"
    ' _ "$file" "$key"
}

service_exists() {
    compose_exec --env-file "$install_conf" -f "$compose_file" config --services 2>/dev/null | grep -Fxq "$1"
}

service_container_id() {
    compose_exec --env-file "$install_conf" -f "$compose_file" ps -q "$1" | head -n 1
}

wait_for_service() {
    local service="$1"
    local attempts="${2:-90}"
    local container_id=""
    local running=""
    local health=""

    while [ "$attempts" -gt 0 ]; do
        container_id="$(service_container_id "$service")"
        if [ -n "$container_id" ]; then
            running="$(engine_exec inspect -f '{{.State.Running}}' "$container_id" 2>/dev/null || true)"
            health="$(engine_exec inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}running{{end}}' "$container_id" 2>/dev/null || true)"
            if [ "$running" = "true" ] && { [ "$health" = "healthy" ] || [ "$health" = "running" ]; }; then
                return 0
            fi
        fi
        attempts=$((attempts - 1))
        sleep 2
    done

    echo "Service '$service' did not become ready."
    if [ -n "$container_id" ]; then
        engine_exec logs --tail 200 "$container_id" || true
    fi
    exit 1
}

print_local_source_diagnostics() {
    echo "Local source diagnostics:"
    if command -v git >/dev/null 2>&1 && git -C "$repo_root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "  local HEAD: $(git -C "$repo_root" log -1 --oneline)"
    else
        echo "  local git metadata unavailable"
    fi
}

options=":d:g:c:s:j:a:e:vhnp"
while getopts $options opt; do
    case $opt in
        d) dashboard_sql=$OPTARG ;;
        g) git_revision=$OPTARG ;;
        c) compose_file=$OPTARG ;;
        s) install_conf=$OPTARG ;;
        j) install_conf_map_entries+=("$OPTARG") ;;
        a)
            action=$OPTARG
            if [[ "$action" != "install" && "$action" != "upgrade" ]]; then
                echo "Invalid action '$action'. Use install or upgrade."
                exit 1
            fi
            ;;
        e)
            engine=$OPTARG
            if [[ "$engine" != "docker" && "$engine" != "podman" ]]; then
                echo "Invalid engine '$engine'. Use docker or podman."
                exit 1
            fi
            ;;
        n) skip_dashboard_sql=true ;;
        p) mode="test" ;;
        h)
            usage
            exit 1
            ;;
        v)
            echo $MEPRAM_VERSION
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

if [ "$mode" = "test" ]; then
    compose_file="${compose_file:-docker-compose.test.yml}"
else
    compose_file="${compose_file:-docker-compose.prod.yml}"
fi

app_service="${APP_SERVICE:-mepram_api}"
selected_install_conf="$install_conf"
for map_entry in "${install_conf_map_entries[@]}"; do
    svc_name="${map_entry%%,*}"
    conf_name="${map_entry#*,}"
    if [ -z "$svc_name" ] || [ -z "$conf_name" ] || [ "$svc_name" = "$map_entry" ]; then
        echo "Invalid --install_conf_map value '$map_entry'. Expected format: service,path"
        exit 1
    fi
    if [ "$svc_name" != "mepram_api" ] && [ "$svc_name" != "app" ]; then
        echo "Unknown service '$svc_name' in --install_conf_map. Valid service: mepram_api"
        exit 1
    fi
    selected_install_conf="$conf_name"
done

if [ "$mode" = "test" ] && [ -z "$selected_install_conf" ]; then
    selected_install_conf="conf/docker_test_settings.txt"
fi
install_conf="$selected_install_conf"

if [ "$mode" = "production" ] && [ -z "$install_conf" ]; then
    echo "Production deployments require --install_conf or --install_conf_map mepram_api,<path>."
    exit 1
fi

if [ ! -f "$compose_file" ]; then
    echo "Compose file '$compose_file' not found"
    exit 1
fi

if [ ! -f "$install_conf" ]; then
    echo "Install configuration '$install_conf' not found"
    exit 1
fi

if [ -n "$dashboard_sql" ] && [ ! -f "$dashboard_sql" ]; then
    echo "Dashboard SQL file '$dashboard_sql' not found"
    exit 1
fi

repo_root="$(pwd)"
build_context_dir="$repo_root"
temp_install_conf=""

cleanup_temp_conf() {
    if [ -n "$temp_install_conf" ] && [ -f "$temp_install_conf" ]; then
        rm -f "$temp_install_conf"
    fi
}
trap cleanup_temp_conf EXIT

if [[ "$install_conf" = /* ]] && [[ "$install_conf" != "$build_context_dir/"* ]]; then
    temp_install_conf="$build_context_dir/.tmp_docker_install_conf_mepram_$$.txt"
    echo "Copying $install_conf into temporary file $temp_install_conf for Docker build/runtime."
    cp "$install_conf" "$temp_install_conf"
    install_conf="$temp_install_conf"
fi

if [[ "$install_conf" = "$build_context_dir/"* ]]; then
    install_conf_container="${install_conf#$build_context_dir/}"
else
    install_conf_container="$install_conf"
fi

host_install_conf_path="$install_conf"
if [[ "$host_install_conf_path" != /* ]]; then
    host_install_conf_path="$repo_root/$host_install_conf_path"
fi

set_engine

app_repo_path="${APP_REPO_PATH:-/srv/mepram-omop-api}"
config_install_path="$(read_install_conf_value "INSTALL_PATH" "$host_install_conf_path")"
config_app_install_path="$(read_install_conf_value "APP_INSTALL_PATH" "$host_install_conf_path")"
app_install_path="${APP_INSTALL_PATH:-${config_app_install_path:-${config_install_path:-/srv/mepram-omop-api}}}"
db_service="${DB_SERVICE:-mepram_db}"
dashboard_sql_container_path="${DASHBOARD_SQL_CONTAINER_PATH:-/data/dashboard.sql}"
api_port="$(read_install_conf_value "MEPRAM_API_PORT" "$host_install_conf_path")"
api_port="${MEPRAM_API_PORT:-${api_port:-8100}}"

print_local_source_diagnostics
echo "Deploying MePRAM API containers (compose file: $compose_file) with GIT_REVISION=$git_revision..."
compose_exec --env-file "$install_conf" -f "$compose_file" build
compose_exec --env-file "$install_conf" -f "$compose_file" up -d

if service_exists "$db_service"; then
    echo "Waiting for database service: $db_service"
    wait_for_service "$db_service" 90
fi

echo "Waiting for application service: $app_service"
wait_for_service "$app_service" 90

app_container="$(service_container_id "$app_service")"
if [ -z "$app_container" ]; then
    echo "Unable to resolve container for service '$app_service'."
    exit 1
fi

container_install_conf_path="$install_conf_container"
if [[ "$container_install_conf_path" != /* ]]; then
    container_install_conf_path="$app_repo_path/$container_install_conf_path"
fi

if ! engine_exec exec "$app_container" test -f "$container_install_conf_path"; then
    echo "Copying install configuration into container at $container_install_conf_path"
    engine_exec cp "$host_install_conf_path" "${app_container}:$container_install_conf_path"
fi

if [ -n "$dashboard_sql" ] && [ "$skip_dashboard_sql" = false ]; then
    echo "Copying dashboard SQL into the API container"
    engine_exec exec "$app_container" mkdir -p "$(dirname "$dashboard_sql_container_path")"
    engine_exec cp "$dashboard_sql" "${app_container}:$dashboard_sql_container_path"
fi

if [ "$action" = "upgrade" ]; then
    echo "Running install.sh bootstrap inside the container (upgrade mode)"
    engine_exec exec "$app_container" bash -c "cd '$app_repo_path' && APP_INSTALL_PATH='$app_install_path' bash install.sh --bootstrap upgrade --git_revision '$git_revision' --conf '$install_conf_container' --skip_apache_restart"
else
    echo "Running install.sh bootstrap inside the container (install mode)"
    engine_exec exec "$app_container" bash -c "cd '$app_repo_path' && APP_INSTALL_PATH='$app_install_path' bash install.sh --bootstrap install --git_revision '$git_revision' --conf '$install_conf_container' --skip_apache_restart"
fi

if [ -n "$dashboard_sql" ] && [ "$skip_dashboard_sql" = false ]; then
    echo "Importing dashboard SQL"
    engine_exec exec "$app_container" bash -c "cd '$app_install_path' && python manage.py import_dashboard_sql '$dashboard_sql_container_path' --truncate"
else
    echo "Skipping dashboard SQL import"
fi

engine_exec exec "$app_container" test -f "$app_install_path/manage.py" || {
    echo "Error: $app_install_path/manage.py not found after bootstrap. Showing logs:"
    engine_exec logs --tail 200 "$app_container"
    exit 1
}

echo "Marking container installation as ready"
engine_exec exec "$app_container" sh -c "touch '$app_install_path/.container_install_ready'"

echo "You can now access MePRAM API via:"
echo "  Health:  http://localhost:${api_port}/v1/health"
echo "  Swagger: http://localhost:${api_port}/swagger/"
