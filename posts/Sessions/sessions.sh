#!/bin/bash

# ==========================================
#  TACTICAL WORKSPACE ORCHESTRATOR
#  Location: /usr/bin/sessions.sh
# ==========================================

# --- CONFIGURATION ---
BASE_DIR="$HOME/operations"
SHELL_BIN="/bin/bash"

# --- DEPENDENCY CHECK ---
if ! command -v tmux &> /dev/null; then
    echo "[!] Error: tmux is not installed."
    exit 1
fi

# --- UTILS ---
setup_visuals() {
    local session=$1
    local color=$2
    
    # Visual cues for context switching (Safety Mechanism)
    # Status bar background/foreground
    tmux set-option -t "$session" status-style "bg=$color,fg=black"
    
    # Active pane borders
    tmux set-option -t "$session" pane-border-style "fg=colour240"
    tmux set-option -t "$session" pane-active-border-style "fg=$color"
    
    # Message styling
    tmux set-option -t "$session" message-style "bg=$color,fg=black"
}

# ==========================================
#  SESSION 1: INFRASTRUCTURE (Blue/Admin)
# ==========================================
start_infra() {
    local SESS="INFRASTRUCTURE"
    
    # Idempotency check: If session exists, do nothing
    if tmux has-session -t "$SESS" 2>/dev/null; then
        echo "[!] Session $SESS already active."
        return
    fi

    echo "[*] Booting Infrastructure Grid..."
    sudo -v # Auth token refresh

    # Window 1: OVERWATCH (System Health)
    # Create detached session
    tmux new-session -d -s "$SESS" -n "Overwatch"
    setup_visuals "$SESS" "colour33" # Cobalt Blue

    # Layout: Top (Logs), Bottom Left (Process), Bottom Right (Netstat)
    tmux split-window -v -p 30 -t "$SESS":0
    tmux split-window -h -t "$SESS":0.1
    
    tmux send-keys -t "$SESS":0.0 "sudo journalctl -f" C-m
    tmux send-keys -t "$SESS":0.1 "top" C-m
    tmux send-keys -t "$SESS":0.2 "watch -n 2 'ss -tuln'" C-m

    # Window 2: GATEWAY
    tmux new-window -t "$SESS" -n "Gateway"
    tmux split-window -h -t "$SESS":1
    tmux send-keys -t "$SESS":1.0 "echo '# SSH Jump / Remote Mgmt'" C-m

    # Window 3: LAB
    tmux new-window -t "$SESS" -n "Lab_Control"
    tmux send-keys -t "$SESS":2 "echo '# VM / Docker Management'" C-m

    # Window 4: CONFIG
    tmux new-window -t "$SESS" -n "Config"
    tmux send-keys -t "$SESS":3 "cd ~/" C-m

    # Return focus to first window
    tmux select-window -t "$SESS":0
}

# ==========================================
#  SESSION 2: ENGAGEMENT (Red/Tactical)
# ==========================================
start_mission() {
    local SESS="MISSION_Zero"
    
    if tmux has-session -t "$SESS" 2>/dev/null; then
        echo "[!] Session $SESS already active."
        return
    fi

    echo "[*] Initializing Killchain Workspace..."

    # Window 1: C2 & COMMS
    tmux new-session -d -s "$SESS" -n "C2_Comms"
    setup_visuals "$SESS" "colour196" # Red (Alert Status)

    # Layout: Main Shell (Left), Tunnel/VPN (Top Right), Listener (Bottom Right)
    tmux split-window -h -p 35 -t "$SESS":0
    tmux split-window -v -t "$SESS":0.1
    
    # Check if dirs exist before cd, else echo warning
    if [ -d "$HOME/ctf_OpenVPN" ]; then
        tmux send-keys -t "$SESS":0.1 "cd ~/ctf_OpenVPN" C-m
    fi
    tmux send-keys -t "$SESS":0.1 "echo '# VPN Interface'" C-m
    tmux send-keys -t "$SESS":0.2 "echo '# Listener / Handler'" C-m
    tmux send-keys -t "$SESS":0.0 "echo '# Main Command Interface'" C-m

    # Window 2: RECON
    tmux new-window -t "$SESS" -n "Recon"
    tmux split-window -v -t "$SESS":1 
    tmux send-keys -t "$SESS":1.0 "echo '# Active Scanning'" C-m
    tmux send-keys -t "$SESS":1.1 "echo '# Passive Intel / Notes'" C-m

    # Window 3: WEAPONIZATION (Forge)
    tmux new-window -t "$SESS" -n "Forge"
    
    # Complex Split: Top (Main), Bottom Left, Bottom Right
    tmux split-window -v -p 40 -t "$SESS":2
    tmux split-window -h -t "$SESS":2.1
    
    # Environment Activation Helper
    local ENV_CMD="[ -f ~/myenv/bin/activate ] && source ~/myenv/bin/activate"

    # Pane 2.0: Top
    tmux send-keys -t "$SESS":2.0 "$ENV_CMD; clear; echo '# Exploit Dev'" C-m
    # Pane 2.1: Bot Left
    tmux send-keys -t "$SESS":2.1 "$ENV_CMD; clear; echo '# Auxiliary'" C-m
    # Pane 2.2: Bot Right
    tmux send-keys -t "$SESS":2.2 "$ENV_CMD; clear; echo '# Debug/Output'" C-m

    # Window 4: STAGING
    tmux new-window -t "$SESS" -n "Staging"
    tmux split-window -v -p 50 -t "$SESS":3
    tmux send-keys -t "$SESS":3.0 "echo '# Python Server / FTP'" C-m
    tmux send-keys -t "$SESS":3.1 "echo '# Payload Directory'" C-m

    # Window 5: EXFIL
    tmux new-window -t "$SESS" -n "Exfil_Data"
    tmux send-keys -t "$SESS":4 "echo '# Loot Storage'" C-m

    tmux select-window -t "$SESS":0
}

# --- SMART LAUNCHER ---

# 1. Check for existing sessions
SESSION_FOUND=""
if tmux has-session -t "INFRASTRUCTURE" 2>/dev/null; then
    SESSION_FOUND="INFRASTRUCTURE"
elif tmux has-session -t "MISSION_Zero" 2>/dev/null; then
    SESSION_FOUND="MISSION_Zero"
fi

# 2. Logic: If session exists, ask user briefly, otherwise auto-resume
if [ -n "$SESSION_FOUND" ]; then
    clear
    echo "========================================="
    echo "  ⚠️  ACTIVE SESSION DETECTED: $SESSION_FOUND"
    echo "========================================="
    echo "  [Enter] Resume Session (Default)"
    echo "  [M]     Open Main Menu (New Context)"
    echo "  [K]     Kill All & Restart"
    echo "========================================="
    
    # Wait 3 seconds for input. If none, auto-resume.
    read -t 3 -n 1 -p "Resuming in 3 seconds... (Press key to interrupt): " selection
    echo "" # Newline

    case $selection in
        [mM]) 
            # Fall through to Main Menu below
            ;;
        [kK])
            echo "[!] Killing all sessions..."
            tmux kill-server
            sleep 1
            # Fall through to Main Menu
            ;;
        *)
            # Default: Attach to the found session
            echo "[*] Resuming $SESSION_FOUND..."
            tmux attach-session -t "$SESSION_FOUND"
            exit 0
            ;;
    esac
fi

# --- MAIN MENU (Only reached if no session or user pressed 'M') ---
clear
echo "==================================="
echo "  OPERATIONAL CONTEXT SWITCHER     "
echo "==================================="
echo "1. Infrastructure (Blue/Admin)"
echo "2. Mission Profile (Red/Tactical)"
echo "3. Full Deployment (Both)"
echo "==================================="
read -p "Select Mode [1-3]: " mode

case $mode in
    1) 
        start_infra
        tmux attach-session -t INFRASTRUCTURE 
        ;;
    2) 
        start_mission
        tmux attach-session -t MISSION_Zero 
        ;;
    3) 
        start_infra
        start_mission
        echo "[*] Both grids active."
        echo "[*] Attaching to INFRASTRUCTURE."
        echo "[*] Use (Ctrl+B then s) to switch sessions."
        sleep 2
        tmux attach-session -t INFRASTRUCTURE 
        ;;
    *) 
        echo "Abort." 
        exit 1 
        ;;
esac
