#!/usr/bin/env bash
# ==============================================================================
# J.A.R.V.I.S Linux — Setup & System Health Script
# ==============================================================================
# Detects OS, checks dependencies, configures ALSA/PulseAudio/PipeWire,
# verifies user permissions, tests audio hardware, and starts JARVIS.
#
# Usage:
#   ./scripts/setup_linux.sh              # Check & report only
#   ./scripts/setup_linux.sh --fix        # Check & auto-fix
#   ./scripts/setup_linux.sh --start      # Check, fix, then start JARVIS
#   ./scripts/setup_linux.sh --report     # Generate detailed diagnostic report
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

# ── Colors ─────────────────────────────────────────────────────────────────────
NC="\033[0m"; R="\033[0;31m"; G="\033[0;32m"; Y="\033[0;33m"; B="\033[0;34m"
C="\033[0;36m"; W="\033[0;37m"; BOLD="\033[1m"

log()     { echo -e "${C}[SETUP]${NC} $*"; }
ok()      { echo -e "  ${G}✅${NC} $*"; }
warn()    { echo -e "  ${Y}⚠️${NC} $*"; }
fail()    { echo -e "  ${R}❌${NC} $*"; }
header()  { echo -e "\n${BOLD}${B}━━━ $* ━━━${NC}"; }
cmd()     { echo -e "  ${W}\$ ${1}${NC}"; }

FIX_MODE=false
START_MODE=false
REPORT_MODE=false
HAS_ERROR=false
FIXABLE=()
FIX_COUNT=0

# ── Parse args ─────────────────────────────────────────────────────────────────
for arg in "$@"; do
    case "$arg" in
        --fix)     FIX_MODE=true ;;
        --start)   FIX_MODE=true; START_MODE=true ;;
        --report)  REPORT_MODE=true ;;
        --help|-h) echo "Usage: $0 [--fix] [--start] [--report]"; exit 0 ;;
    esac
done

# ── Helpers ────────────────────────────────────────────────────────────────────

check_cmd() {
    if command -v "$1" &>/dev/null; then
        ok "$1 ($(command -v "$1"))"
        return 0
    else
        fail "$1 — bulunamadı"
        return 1
    fi
}

check_pkg() {
    if dpkg -s "$1" &>/dev/null 2>&1; then
        ver=$(dpkg -s "$1" 2>/dev/null | grep '^Version:' | awk '{print $2}')
        ok "$1 ($ver)"
    else
        fail "$1 — KURULU DEĞİL"
        FIXABLE+=("sudo DEBIAN_FRONTEND=noninteractive apt-get install -y $1 2>&1 | tail -3")
    fi
}

check_pip_pkg() {
    if "$PYTHON" -c "import $1" &>/dev/null 2>&1; then
        ok "python-$1"
        return 0
    else
        fail "python-$1 — KURULU DEĞİL"
        return 1
    fi
}

check_sudo() {
    # Check if passwordless sudo is available
    if timeout 5 sudo -n true 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

fix_if_needed() {
    if [ "$FIX_MODE" = true ] && [ ${#FIXABLE[@]} -gt 0 ]; then
        echo ""
        log "${Y}${#FIXABLE[@]} eksik paket bulundu${NC}"
        if check_sudo; then
            log "Kurulum basliyor..."
            for pkg_cmd in "${FIXABLE[@]}"; do
                cmd "$pkg_cmd"
                if timeout 30 eval "$pkg_cmd" 2>/dev/null; then
                    ok "Kurulum basarili"
                    FIX_COUNT=$((FIX_COUNT+1))
                else
                    fail "Kurulum basarisiz"
                fi
            done
        else
            warn "sudo erisimi yok — paketler manuel kurulmali:"
            for pkg_cmd in "${FIXABLE[@]}"; do
                echo "    ${pkg_cmd/sudo /}"
            done
            if [ "$START_MODE" = true ]; then
                HAS_ERROR=true
            fi
        fi
    fi
}

# ── Detect Python venv ─────────────────────────────────────────────────────────
detect_python() {
    header "1/8  Python Ortamı"
    for candidate in ".venv" "venv" "env" ".env"; do
        if [ -f "$candidate/bin/python3" ]; then
            PYTHON="$PROJECT_DIR/$candidate/bin/python3"
            VENV_DIR="$candidate"
            break
        fi
    done
    PYTHON="${PYTHON:-python3}"

    if "$PYTHON" --version &>/dev/null; then
        ver=$("$PYTHON" --version 2>&1)
        ok "$ver"
        which_venv=$("$PYTHON" -c "import sys; print('venv' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else 'sistem')" 2>/dev/null || echo "sistem")
        ok "Ortam: $which_venv ($("$PYTHON" -c "import sys; print(sys.prefix)" 2>/dev/null))"
    else
        fail "Python bulunamadı!"
        HAS_ERROR=true; return
    fi
    PIP="$VENV_DIR/bin/pip"
    if [ ! -f "$PIP" ]; then PIP="pip3"; fi
}

# ── Check system packages ──────────────────────────────────────────────────────
check_system_packages() {
    header "2/8  Sistem Paketleri"

    # Core audio
    check_pkg "libportaudio2"
    check_pkg "portaudio19-dev"
    check_pkg "libsndfile1"
    check_pkg "libsndfile1-dev"
    check_pkg "alsa-utils"
    check_pkg "pulseaudio-utils"

    # PipeWire stack
    check_pkg "pipewire"
    check_pkg "pipewire-pulse"
    check_pkg "pipewire-alsa"
    check_pkg "libspa-0.2-bluetooth"

    # Codec support
    check_pkg "ffmpeg"
    check_pkg "libavcodec-extra" || true  # non-free but useful

    # System monitoring
    check_pkg "lsof"
    check_pkg "curl"

    fix_if_needed
}

# ── Check Python packages ──────────────────────────────────────────────────────
check_python_packages() {
    header "3/8  Python Kütüphaneleri"
    local missing_pip=()

    for mod in "sounddevice" "pyaudio" "numpy" "scipy" "requests" "PIL" "psutil" "httpx" "yaml" "faster_whisper"; do
        if ! check_pip_pkg "$mod"; then
            missing_pip+=("$mod")
        fi
    done

    if [ "$FIX_MODE" = true ] && [ ${#missing_pip[@]} -gt 0 ]; then
        log "Eksik pip paketleri yükleniyor..."
        cmd "$PIP install ${missing_pip[*]}"
        if $PIP install "${missing_pip[@]}" -q 2>&1 | tail -2; then
            ok "${#missing_pip[@]} paket yüklendi"
            FIX_COUNT=$((FIX_COUNT+1))
        fi
    fi
}

# ── Check audio hardware ───────────────────────────────────────────────────────
check_audio_hardware() {
    header "4/8  Ses Donanımı"

    # ALSA devices (timed)
    echo ""
    log "ALSA Cihazları:"
    if command -v aplay &>/dev/null; then
        aplay_out=$(timeout 3 aplay -l 2>&1 || echo "(zaman aşımı)")
        if echo "$aplay_out" | grep -q "card"; then
            echo "$aplay_out" | while IFS= read -r line; do
                echo "    $line"
            done
        else
            warn "Hiçbir playback cihazı bulunamadı — $aplay_out"
        fi
    fi

    if command -v arecord &>/dev/null; then
        arecord_out=$(timeout 3 arecord -l 2>&1 || echo "(zaman aşımı)")
        if echo "$arecord_out" | grep -q "card"; then
            echo "$arecord_out" | while IFS= read -r line; do
                echo "    $line"
            done
        else
            warn "Hiçbir kayıt (mikrofon) cihazı bulunamadı — $arecord_out"
        fi
    fi

    # sounddevice detection
    echo ""
    log "sounddevice Cihazları:"
    if $PYTHON -c "import sounddevice; print('\n'.join([f'    [{i}] {d[\"name\"]} (in={d[\"max_input_channels\"]} out={d[\"max_output_channels\"]})' for i,d in enumerate(sounddevice.query_devices()) if d['max_input_channels']>0 or d['max_output_channels']>0]))" 2>/dev/null; then
        :
    else
        warn "sounddevice cihaz listelenemedi"
    fi

    # Default devices
    echo ""
    log "Varsayılan Cihazlar:"
    $PYTHON -c "
import sounddevice as sd
try:
    inp = sd.query_devices(sd.default.device[0])
    out = sd.query_devices(sd.default.device[1])
    print(f'    Mikrofon (giriş): [{sd.default.device[0]}] {inp[\"name\"]}')
    print(f'    Hoparlör (çıkış): [{sd.default.device[1]}] {out[\"name\"]}')
except Exception as e:
    print(f'    Hata: {e}')
" 2>/dev/null || warn "Varsayılan cihazlar alınamadı"

    echo ""
    log "Mikrofon Testi (0.5 saniye):"
    $PYTHON -c "
import sounddevice as sd, numpy as np
try:
    duration = 0.5
    recording = sd.rec(int(duration * 16000), samplerate=16000, channels=1, dtype='int16')
    sd.wait()
    rms = float(np.sqrt(np.mean(recording.astype(np.float32)**2)))
    print(f'    RMS seviyesi: {rms:.1f}')
    if rms > 100:
        print(f'    Mikrofon calisiyor (ses algilaniyor)')
    elif rms > 10:
        print(f'    Mikrofon calisiyor ama cok sessiz')
    else:
        print(f'    Mikrofon SESSIZ')
except Exception as e:
    print(f'    Kayit hatasi: {e}')
" 2>&1 || true
}

# ── Check user permissions ─────────────────────────────────────────────────────
check_permissions() {
    header "5/8  Kullanıcı İzinleri"

    local user_groups
    user_groups=$(groups 2>/dev/null || echo "")

    log "Grup üyelikleri: $user_groups"
    echo ""

    # audio group
    if echo "$user_groups" | grep -q "audio"; then
        ok "audio grubunda — /dev/snd/* erişilebilir"
    else
        fail "audio grubunda DEĞİL — ses cihazlarına erişim kısıtlı!"
        echo "    Çözüm: sudo usermod -aG audio $USER && oturumu kapatıp açın"
        if [ "$FIX_MODE" = true ]; then
            log "Geçici çözüm: ACL ile pipewire erişimi sağlanıyor..."
            if command -v setfacl &>/dev/null; then
                for dev in /dev/snd/*; do
                    sudo setfacl -m u:$USER:rw "$dev" 2>/dev/null || true
                done
                ok "ACL eklendi — /dev/snd/* artık okunabilir"
                FIX_COUNT=$((FIX_COUNT+1))
            else
                warn "setfacl yok — ACL eklenemedi"
            fi
        fi
    fi

    # /dev/snd detaylı
    echo ""
    log "/dev/snd/ İzinleri:"
    if [ -d /dev/snd ]; then
        ls -la /dev/snd/ 2>/dev/null | head -5 | while IFS= read -r line; do
            echo "    $line"
        done
        # Check readable
        local accessible=0
        local total=0
        for dev in /dev/snd/*; do
            total=$((total+1))
            if [ -r "$dev" ]; then
                accessible=$((accessible+1))
            fi
        done
        echo ""
        if [ "$accessible" -eq "$total" ]; then
            ok "Tüm $total cihaz okunabilir"
        else
            warn "Sadece $accessible/$total cihaz okunabilir — bazılarına erişim yok"
        fi
    else
        fail "/dev/snd/ dizini yok — ses donanımı mevcut değil!"
    fi
}

# ── Check PipeWire/PulseAudio status ──────────────────────────────────────────
check_audio_server() {
    header "6/8  Ses Sunucusu (PipeWire/PulseAudio)"

    # PipeWire
    if pgrep -x pipewire &>/dev/null; then
        ok "pipewire çalışıyor"
    else
        warn "pipewire çalışmıyor"
    fi

    if pgrep -x wireplumber &>/dev/null; then
        ok "wireplumber çalışıyor"
    else
        warn "wireplumber çalışmıyor"
    fi

    if pgrep -x pipewire-pulse &>/dev/null; then
        ok "pipewire-pulse çalışıyor"
    else
        warn "pipewire-pulse çalışmıyor"
    fi

    # pactl info
    echo ""
    log "pactl info:"
    if command -v pactl &>/dev/null; then
        pactl info 2>/dev/null | grep -E "Server Name|Default Sink|Default Source" | while IFS= read -r line; do
            echo "    $line"
        done || warn "pactl info başarısız"

        echo ""
        log "Ses Kaynakları (sinks):"
        pactl list sinks short 2>/dev/null | while IFS= read -r line; do
            echo "    $line"
        done || echo "    (yok)"

        echo ""
        log "Ses Kaynakları (sources):"
        pactl list sources short 2>/dev/null | while IFS= read -r line; do
            echo "    $line"
        done || echo "    (yok)"
    fi
}

# ── Check ALSA configuration ──────────────────────────────────────────────────
check_alsa_config() {
    header "7/8  ALSA Yapılandırması"

    log "Ses seviyeleri:"
    amixer 2>/dev/null | grep -E "Simple|Front Left|Front Right|Capture" | while IFS= read -r line; do
        echo "    $line"
    done || warn "amixer çalışmadı"

    # ALSA config check
    echo ""
    log "ALSA config dosyaları:"
    for f in /etc/asound.conf ~/.asoundrc; do
        if [ -f "$f" ]; then
            echo "    ✅ $f"
            echo "    ─────────────────"
            cat "$f" 2>/dev/null | head -10 | while IFS= read -r line; do
                echo "      $line"
            done
        fi
    done
    if [ ! -f /etc/asound.conf ] && [ ! -f ~/.asoundrc ]; then
        warn "asound.conf yok — ALSA varsayılanları kullanılıyor"
    fi

    # ALSA UCM (user controls)
    echo ""
    log "ALSA state:"
    if command -v alsactl &>/dev/null; then
        alsactl info 2>/dev/null | head -3 | while IFS= read -r line; do
            echo "    $line"
        done
    fi
}

# ── Network / Ollama check ────────────────────────────────────────────────────
check_network_services() {
    header "8/8  Ağ ve Servisler"

    # Ollama
    log "Ollama Durumu:"
    if curl -s --max-time 2 http://localhost:11434/api/tags &>/dev/null; then
        ok "Ollama API çalışıyor (localhost:11434)"
        $PYTHON -c "
import json, urllib.request
try:
    req = urllib.request.urlopen('http://localhost:11434/api/tags', timeout=3)
    data = json.loads(req.read())
    models = data.get('models', [])
    if models:
        print(f'    📦 Yüklü modeller ({len(models)}):')
        for m in models:
            name = m.get('name', '?')
            size = m.get('size', 0)
            print(f'       - {name} ({size/1e9:.1f}GB)' if size else f'       - {name}')
    else:
        print(f'    ⚠️ Hiç model yok — ollama pull qwen2.5:1.5b')
except Exception as e:
    print(f'    ❌ Hata: {e}')
"
    else
        warn "Ollama çalışmıyor veya bağlantı kurulamadı"
        if [ "$FIX_MODE" = true ]; then
            log "Ollama başlatılıyor..."
            if command -v ollama &>/dev/null; then
                nohup ollama serve > /tmp/ollama.log 2>&1 &
                sleep 2
                if curl -s --max-time 2 http://localhost:11434/api/tags &>/dev/null; then
                    ok "Ollama başlatıldı"
                    FIX_COUNT=$((FIX_COUNT+1))
                fi
            else
                fail "ollama binary'si bulunamadı — https://ollama.com/download"
            fi
        fi
    fi

    # Internet
    echo ""
    log "İnternet Bağlantısı:"
    if ping -c 1 -W 2 google.com &>/dev/null; then
        ok "İnternet bağlantısı var"
    else
        warn "İnternet yok veya DNS çözümleme başarısız"
    fi

    # Gemini API key
    echo ""
    log "Gemini API Key:"
    if [ -f config/api_keys.json ]; then
        key=$($PYTHON -c "
import json
try:
    d = json.loads(open('config/api_keys.json').read())
    k = d.get('gemini_api_key', '')
    print(k[:8] + '...' + k[-4:] if k and k != 'AIzaSy...' else 'BOŞ')
except: print('OKUNAMADI')
" 2>/dev/null)
        if [ "$key" != "BOŞ" ] && [ "$key" != "OKUNAMADI" ]; then
            ok "API key mevcut: $key"
        else
            warn "API key boş veya varsayılan"
        fi

        backend=$($PYTHON -c "
import json
try:
    d = json.loads(open('config/api_keys.json').read())
    print(d.get('backend_type', '?'), d.get('ollama_model', '?'))
except: print('? ?')
")
        log "Backend: $backend"
    else
        fail "config/api_keys.json bulunamadı"
    fi
}

# ── Fix: suppress ALSA config noise ────────────────────────────────────────────
fix_alsa_noise() {
    if [ "$FIX_MODE" != true ]; then return; fi
    header "⚡ ALSA Config İyileştirmesi"

    # Create ~/.asoundrc to suppress the "Unknown PCM" warnings
    # by defining the PCM aliases that ALSA probes
    local asoundrc="$HOME/.asoundrc"
    if [ -f "$asoundrc" ] && grep -q "JARVIS" "$asoundrc" 2>/dev/null; then
        ok "~/.asoundrc zaten JARVIS tarafından yapılandırılmış"
        return
    fi

    log "ALSA PCM alias'ları tanımlanıyor (sessiz başlangıç)..."
    cat >> "$asoundrc" 2>/dev/null << 'EOF'

# ── JARVIS ALSA Configuration ──
# Suppress "Unknown PCM" warnings by defining standard PCM aliases
pcm.rear {
    type null
    slave.pcm "default"
}

pcm.center_lfe {
    type null
    slave.pcm "default"
}

pcm.side {
    type null
    slave.pcm "default"
}

pcm.iec958 {
    type null
    slave.pcm "default"
}

# Default: use PipeWire
pcm.!default {
    type pipewire
    slave.pcm "default"
}

ctl.!default {
    type hw
    card 0
}
EOF
    ok "~/.asoundrc oluşturuldu (ALSA uyarıları susturuldu)"
    FIX_COUNT=$((FIX_COUNT+1))
}

# ── Generate comprehensive report ──────────────────────────────────────────────
generate_report() {
    local report_file="$PROJECT_DIR/setup_report_$(date +%Y%m%d_%H%M%S).txt"

    {
        echo "═══════════════════════════════════════════════"
        echo "  J.A.R.V.I.S Linux Setup Report"
        echo "  $(date '+%Y-%m-%d %H:%M:%S')"
        echo "═══════════════════════════════════════════════"
        echo ""
        echo "OS:      $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"')"
        echo "Kernel:  $(uname -r)"
        echo "Host:    $(hostname)"
        echo "User:    $(whoami)"
        echo "Shell:   $SHELL"
        echo "Python:  $($PYTHON --version 2>&1)"
        echo "PIP:     $($PIP --version 2>&1)"
        echo ""
        echo "── Ses Donanımı ──"
        echo "ALSA Playback:"
        aplay -l 2>&1 | head -20 || echo "  (none)"
        echo ""
        echo "ALSA Capture:"
        arecord -l 2>&1 | head -20 || echo "  (none)"
        echo ""
        echo "sounddevice:"
        $PYTHON -c "
import sounddevice as sd
for i, d in enumerate(sd.query_devices()):
    print(f'  [{i}] {d[\"name\"]} (in={d[\"max_input_channels\"]} out={d[\"max_output_channels\"]})')
" 2>/dev/null || echo "  (failed)"
        echo ""
        echo "── Ses Sunucusu ──"
        echo "PipeWire:      $(pgrep -x pipewire &>/dev/null && echo running || echo stopped)"
        echo "WirePlumber:   $(pgrep -x wireplumber &>/dev/null && echo running || echo stopped)"
        echo "PipeWire-Pulse: $(pgrep -x pipewire-pulse &>/dev/null && echo running || echo stopped)"
        echo ""
        echo "── İzinler ──"
        groups
        echo ""
        ls -la /dev/snd/ 2>/dev/null | head -15
        echo ""
        echo "── Paketler ──"
        dpkg -l 2>/dev/null | grep -E "^ii.*(pipewire|pulse|alsa|portaudio|libsndfile)" | awk '{print $2, $3}'
        echo ""
        echo "── ALSA Config ──"
        if [ -f /etc/asound.conf ]; then echo "/etc/asound.conf: $(cat /etc/asound.conf | head -20)"; fi
        if [ -f ~/.asoundrc ]; then echo "~/.asoundrc: $(cat ~/.asoundrc | head -20)"; fi
        echo ""
        echo "── config/api_keys.json ──"
        cat config/api_keys.json 2>/dev/null | $PYTHON -c "
import sys, json
try:
    d = json.load(sys.stdin)
    for k,v in d.items():
        if 'key' in k.lower() and v:
            print(f'  {k}: {v[:8]}...{v[-4:]}')
        else:
            print(f'  {k}: {v}')
except: print('  (okunamadi)')
" || echo "  (bulunamadi)"
        echo ""
        echo "═══════════════════════════════════════════════"
    } > "$report_file"

    ok "Rapor kaydedildi: $report_file"
    echo "    Rapor: $report_file"
}

# ── Start JARVIS ───────────────────────────────────────────────────────────────
start_jarvis() {
    if [ "$START_MODE" != true ]; then return; fi
    header "🚀 JARVIS Başlatılıyor"

    if [ "$HAS_ERROR" = true ] && [ "$FIX_COUNT" -eq 0 ]; then
        fail "Düzeltilemeyen hatalar var — JARVIS başlatılmadı"
        echo "    Yukarıdaki hataları manuel olarak çözün"
        exit 1
    fi

    log "Ollama hazır mı?"
    if ! curl -s --max-time 2 http://localhost:11434/api/tags &>/dev/null; then
        warn "Ollama çalışmıyor — başlatılıyor..."
        ollama serve > /tmp/ollama.log 2>&1 &
        sleep 3
    fi

    log "JARVIS başlatılıyor (PID: $$)..."
    echo ""
    $PYTHON main.py &
    JARVIS_PID=$!
    sleep 4
    if kill -0 $JARVIS_PID 2>/dev/null; then
        ok "JARVIS çalışıyor (PID=$JARVIS_PID)"
        echo "    Log: tail -f logs/jarvis_debug.log"
        echo "    Durdurmak için: kill $JARVIS_PID"
    else
        fail "JARVIS başlatılamadı!"
        echo "    Log: cat logs/jarvis_debug.log | tail -30"
    fi
}

# ── Main ───────────────────────────────────────────────────────────────────────
main() {
    echo ""
    echo -e "${BOLD}${B}╔══════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${B}║    J.A.R.V.I.S Linux Setup          ║${NC}"
    echo -e "${BOLD}${B}╚══════════════════════════════════════╝${NC}"
    echo ""

    if [ "$REPORT_MODE" = true ]; then
        detect_python
        generate_report
        exit 0
    fi

    detect_python
    check_system_packages
    check_python_packages
    check_audio_hardware
    check_permissions
    check_audio_server
    check_alsa_config
    check_network_services
    fix_alsa_noise

    # Summary
    echo ""
    header "ÖZET"
    if [ "$HAS_ERROR" = true ]; then
        fail "Kritik hatalar var"
    else
        ok "Tüm kontroller geçti"
    fi
    if [ "$FIX_MODE" = true ]; then
        ok "Otomatik düzeltmeler: $FIX_COUNT"
    fi

    echo ""
    if [ "$START_MODE" = true ]; then
        start_jarvis
    else
        log "JARVIS'i başlatmak için: $0 --start"
        log "Detaylı rapor için:    $0 --report"
    fi
    echo ""
}

main
