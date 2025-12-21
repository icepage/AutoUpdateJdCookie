#!/bin/bash
# AutoUpdateJdCookie_install.sh - 京东Cookie自动更新工具安装脚本

# Author: @sushen339
# update: 2025-10-21
# Description: 自动化安装 AutoUpdateJdCookie 所需的系统依赖、Python 环境及项目代码。

set -euo pipefail

# =====================配置变量=======================

readonly SCRIPT_NAME="AutoUpdateJdCookie Installer"
readonly REPO_URL="https://github.com/icepage/AutoUpdateJdCookie.git"
readonly PROJECT_DIR="AutoUpdateJdCookie"
INSTALL_DIR="$(pwd)"
readonly INSTALL_DIR
PYTHON_CMD=""
if [ "$INSTALL_DIR" = "/" ]; then
    LOG_FILE="/AutoUpdateJdCookie_install_$(date +%Y%m%d_%H%M%S).log"
else
    LOG_FILE="${INSTALL_DIR}/AutoUpdateJdCookie_install_$(date +%Y%m%d_%H%M%S).log"
fi
readonly LOG_FILE
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[1;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_RESET='\033[0m'

# =======================工具函数=======================
log_info() {
    echo -e "${COLOR_BLUE}[INFO]${COLOR_RESET} $(date '+%Y-%m-%d %H:%M:%S') - $*" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${COLOR_GREEN}[SUCCESS]${COLOR_RESET} $(date '+%Y-%m-%d %H:%M:%S') - $*" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${COLOR_YELLOW}[WARNING]${COLOR_RESET} $(date '+%Y-%m-%d %H:%M:%S') - $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $(date '+%Y-%m-%d %H:%M:%S') - $*" | tee -a "$LOG_FILE" >&2
}

run_with_progress() {
    local description=$1
    local command=$2
    local log_file=$3
    
    eval "$command" >> "$log_file" 2>&1 &
    local pid=$!
    
    local spin='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local i=0
    
    echo -n "$description: "
    while kill -0 $pid 2>/dev/null; do
        i=$(( (i+1) % 10 ))
        printf "\r%s: %b%s%b 处理中..." "$description" "${COLOR_BLUE}" "${spin:$i:1}" "${COLOR_RESET}"
        sleep 0.1
    done
    
    wait $pid
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        printf "\r%s: %b✓%b 已完成    \n" "$description" "${COLOR_GREEN}" "${COLOR_RESET}"
    else
        printf "\r%s: %b✗%b 失败      \n" "$description" "${COLOR_RED}" "${COLOR_RESET}"
    fi
    
    return $exit_code
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

check_result() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "$1 失败"
        exit 1
    fi
}

# ====================安装函数========================
detect_python_version() {
    log_info "检测系统 Python 版本..."
    
    local python_candidates=("python3.13" "python3.12" "python3.11" "python3.10" "python3.9" "python3")
    
    for py_cmd in "${python_candidates[@]}"; do
        if command_exists "$py_cmd"; then
            local py_version
            py_version=$($py_cmd --version 2>&1 | grep -oP '\d+\.\d+')
            
            if [[ $(echo "$py_version >= 3.8" | bc -l 2>/dev/null || echo "1") -eq 1 ]]; then
                PYTHON_CMD="$py_cmd"
                log_success "检测到 Python: $py_cmd (版本 $py_version)"
                return 0
            fi
        fi
    done
    
    log_error "未找到可用的 Python 3.8+ 版本"
    exit 1
}

check_system_dependencies() {
    log_info "检查系统依赖..."
    
    if ! command_exists apt; then
        log_error "此脚本仅支持基于 apt 的系统（Debian/Ubuntu）"
        exit 1
    fi
    
    if [ "$EUID" -ne 0 ]; then
        log_warning "建议使用 root 权限运行此脚本"
        read -r -p "是否继续？[y/N] " response
        case "$response" in
            [yY][eE][sS]|[yY]) 
                log_info "继续执行..."
                ;;
            *)
                log_info "已取消安装"
                exit 1
                ;;
        esac
    fi
    
    log_success "系统依赖检查完成"
}

install_system_packages() {
    log_info "开始安装系统包..."
    
    echo ""
    run_with_progress "📦 更新 APT 包列表" "apt update" "$LOG_FILE" || {
        log_error "更新包列表失败"
        exit 1
    }
    
    local base_packages=("git" "python3-pip")
    
    echo ""
    run_with_progress "📦 安装系统包 (${base_packages[*]})" "apt install -y ${base_packages[*]}" "$LOG_FILE"
    check_result "基础系统包安装"
    
    log_success "系统包安装完成"
}

clone_repository() {
    log_info "开始克隆代码仓库..."
    
    if [ -d "$PROJECT_DIR" ]; then
        log_warning "项目目录 $PROJECT_DIR 已存在"
        read -r -p "是否删除并重新克隆？[y/N] " response
        case "$response" in
            [yY][eE][sS]|[yY]) 
                log_info "正在删除旧目录..."
                rm -rf "$PROJECT_DIR"
                ;;
            *)
                log_warning "跳过克隆步骤，使用现有项目目录"
                return 0
                ;;
        esac
    fi
    
    echo ""
    run_with_progress "📥 克隆仓库" "git clone --depth=1 \"$REPO_URL\" \"$PROJECT_DIR\"" "$LOG_FILE"
    check_result "克隆代码仓库"
    log_success "代码仓库克隆完成"
}

install_python_dependencies() {
    log_info "开始安装 Python 依赖..."
    
    cd "$PROJECT_DIR" || {
        log_error "无法进入项目目录: $PROJECT_DIR"
        exit 1
    }
     
    echo ""
    run_with_progress "🔧 升级 pip" "pip install --upgrade pip --break-system-packages -q" "$LOG_FILE"
    check_result "升级 pip"
    
    if [ -f "requirements.txt" ]; then
        echo ""
        run_with_progress "📦 安装 Python 依赖" "pip install -r requirements.txt --break-system-packages -q" "$LOG_FILE"
        check_result "安装 Python 依赖"
    else
        log_warning "未找到 requirements.txt，跳过依赖安装"
    fi
    
    echo ""
    run_with_progress "🔧 安装 OpenCV" "pip install opencv-python --break-system-packages -q" "$LOG_FILE"
    check_result "安装 opencv-python"
    
    log_success "Python 依赖安装完成"
}

install_playwright() {
    log_info "开始安装 Playwright 和浏览器..."
    
    echo ""
    run_with_progress "🌐 安装 Playwright 系统依赖" "playwright install-deps" "$LOG_FILE"
    check_result "安装 Playwright 系统依赖"
    
    echo ""
    run_with_progress "🌐 安装 Chromium 浏览器" "playwright install chromium" "$LOG_FILE"
    check_result "安装 Chromium 浏览器"
    
    log_success "Playwright 安装完成"
}

generate_config() {
    log_info "开始生成配置文件..."
    
    if [ ! -f "make_config.py" ]; then
        log_error "make_config.py 文件不存在"
        exit 1
    fi
    
    if [ -f "config.py" ]; then
        log_warning "配置文件 config.py 已存在"
        read -r -p "是否重新生成配置？[y/N] " response
        case "$response" in
            [yY][eE][sS]|[yY]) 
                log_info "将重新生成配置文件"
                ;;
            *)
                log_warning "跳过配置生成步骤"
                return 0
                ;;
        esac
    fi
    
    echo ""
    echo "===================================="
    echo "⚙️  开始配置向导"
    echo "===================================="
    echo ""
    
    $PYTHON_CMD make_config.py 2>&1 | tee -a "$LOG_FILE"
    
    if [ "${PIPESTATUS[0]}" -eq 0 ]; then
        echo ""
        log_success "配置文件生成完成"
    else
        echo ""
        log_error "生成配置文件失败"
        exit 1
    fi
}

show_post_install_info() {
    echo ""
    echo "===================================="
    log_success "AutoUpdateJdCookie 安装完成！"
    echo "===================================="
    echo ""
    echo "项目目录: $(pwd)"
    echo "Python 版本: $PYTHON_CMD"
    echo "日志文件: $LOG_FILE"
    echo ""
    echo "使用说明："
    echo "1. 进入项目目录: cd $PROJECT_DIR"
    echo "2. 单次运行: $PYTHON_CMD main.py"
    echo "3. 常驻进程: nohup $PYTHON_CMD schedule_main.py &"
    echo "4. 面板定时: 添加 $PYTHON_CMD $(pwd)/main.py 到青龙定时任务"
    echo ""
    echo "=================================="
}

# =====================主函数=======================
main() {
    log_info "开始执行 $SCRIPT_NAME..."
    log_info "日志文件: $LOG_FILE"
    
    check_system_dependencies
    install_system_packages
    detect_python_version
    clone_repository
    install_python_dependencies
    install_playwright
    generate_config
    show_post_install_info
    
    log_success "所有安装步骤完成！"
}

main "$@"
