1. **Top Bar Monitor:** A modern bar showing CPU, RAM, GPU, and Network speed.
2. **Tactical Dashboard:** A hidden "Quake-style" terminal that drops down when you press a key (or click an icon), instantly loading your hacking tools.



### **Phase 1: Install Necessary Tools**

First, we need to install the software that makes the magic happen.

**1. Open your terminal and paste this:**

```bash
sudo apt update
sudo apt install xfce4-genmon-plugin tmux xfce4-terminal wmctrl xdotool bc -y

```

**2. Install "Nerd Fonts" (For the cool icons):**

```bash
mkdir -p ~/.local/share/fonts
cd ~/.local/share/fonts
wget https://github.com/ryanoasis/nerd-fonts/releases/download/v3.0.2/FiraCode.zip
unzip FiraCode.zip
rm FiraCode.zip
fc-cache -fv

```

**3. Create your scripts folder:**

```bash
mkdir -p ~/scripts

```



### **Phase 2: The "Brain" (The Dashboard Logic)**

This script manages your "Red Team" (Attack) and "Blue Team" (Defense) layouts.

**1. Create the file:**

```bash
sudo nano /usr/bin/sessions.sh

```

**2. Paste this code:**
*(Use `Ctrl+Shift+V` to paste in terminal)*

```bash
#!/bin/bash
# LOCATION: /usr/bin/sessions.sh

#  CONFIGURATION 
BASE_DIR="$HOME/operations"
SHELL_BIN="/bin/bash"

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "[!] Error: tmux is not installed. Run: sudo apt install tmux"
    exit 1
fi

#  VISUAL SETUP 
setup_visuals() {
    local session=$1
    local color=$2
    tmux set-option -t "$session" status-style "bg=$color,fg=black"
    tmux set-option -t "$session" pane-border-style "fg=colour240"
    tmux set-option -t "$session" pane-active-border-style "fg=$color"
}

#  BLUE TEAM MODE 
start_infra() {
    local SESS="INFRASTRUCTURE"
    if tmux has-session -t "$SESS" 2>/dev/null; then return; fi

    sudo -v
    tmux new-session -d -s "$SESS" -n "Overwatch"
    setup_visuals "$SESS" "colour33" # Blue

    # Split panes for logs and monitoring
    tmux split-window -v -p 30 -t "$SESS":0
    tmux split-window -h -t "$SESS":0.1
    tmux send-keys -t "$SESS":0.0 "sudo journalctl -f" C-m
    tmux send-keys -t "$SESS":0.1 "top" C-m
    tmux send-keys -t "$SESS":0.2 "watch -n 2 'ss -tuln'" C-m

    tmux new-window -t "$SESS" -n "Gateway"
    tmux select-window -t "$SESS":0
}

#  RED TEAM MODE 
start_mission() {
    local SESS="MISSION_Zero"
    if tmux has-session -t "$SESS" 2>/dev/null; then return; fi

    tmux new-session -d -s "$SESS" -n "C2_Comms"
    setup_visuals "$SESS" "colour196" # Red

    # Split panes for VPN, Listener, and Shell
    tmux split-window -h -p 35 -t "$SESS":0
    tmux split-window -v -t "$SESS":0.1
    
    # Safety check for folders
    [ -d "$HOME/ctf_OpenVPN" ] && tmux send-keys -t "$SESS":0.1 "cd ~/ctf_OpenVPN" C-m
    
    tmux send-keys -t "$SESS":0.1 "echo '# VPN Interface'" C-m
    tmux send-keys -t "$SESS":0.2 "echo '# Listener / Handler'" C-m
    tmux send-keys -t "$SESS":0.0 "echo '# Main Command Interface'" C-m

    tmux new-window -t "$SESS" -n "Recon"
    tmux select-window -t "$SESS":0
}

#  SMART RESUME LOGIC 
SESSION_FOUND=""
if tmux has-session -t "INFRASTRUCTURE" 2>/dev/null; then SESSION_FOUND="INFRASTRUCTURE";
elif tmux has-session -t "MISSION_Zero" 2>/dev/null; then SESSION_FOUND="MISSION_Zero"; fi

if [ -n "$SESSION_FOUND" ]; then
    clear
    echo "⚠  ACTIVE SESSION DETECTED: $SESSION_FOUND"
    echo "   [Enter] Resume | [M] Menu | [K] Kill All"
    read -t 3 -n 1 -p "Resuming in 3s... " selection
    echo ""
    case $selection in
        [mM]) ;; 
        [kK]) tmux kill-server; sleep 1 ;;
        *) tmux attach-session -t "$SESSION_FOUND"; exit 0 ;;
    esac
fi

#  MAIN MENU 
clear
echo "==================================="
echo "  TACTICAL OPERATIONS CENTER       "
echo "==================================="
echo "1. Infrastructure (Blue/Admin)"
echo "2. Mission Profile (Red/Tactical)"
echo "3. Full Deployment (Both)"
echo "==================================="
read -p "Select Mode [1-3]: " mode

case $mode in
    1) start_infra; tmux attach-session -t INFRASTRUCTURE ;;
    2) start_mission; tmux attach-session -t MISSION_Zero ;;
    3) start_infra; start_mission; tmux attach-session -t INFRASTRUCTURE ;;
    *) echo "Abort."; exit 1 ;;
esac

```

**3. Save and Exit:**
Press `Ctrl+O`, `Enter`, then `Ctrl+X`.

**4. Make it executable:**

```bash
sudo chmod +x /usr/bin/sessions.sh

```



### **Phase 3: The "Toggle" (The Launcher)**

This script makes the dashboard window appear/disappear when you click the icon or press the hotkey.

**1. Create the file:**

```bash
nano ~/scripts/launch_dashboard.sh

```

**2. Paste this code:**

```bash
#!/bin/bash
# Smart Toggle Script
WIN_TITLE="Tactical Control"

# Check if window exists
TARGET_WIN_ID=$(wmctrl -lGx | grep -i "$WIN_TITLE" | awk '{print $1}')

if [ -n "$TARGET_WIN_ID" ]; then
    # Window Exists: Check if it is currently focused
    ACTIVE_WIN_ID_DEC=$(xdotool getactivewindow 2>/dev/null)
    TARGET_WIN_ID_DEC=$(printf "%d" "$TARGET_WIN_ID")

    if [ "$ACTIVE_WIN_ID_DEC" == "$TARGET_WIN_ID_DEC" ]; then
        # It's open and focused -> Minimize it (Hide)
        xdotool windowminimize "$ACTIVE_WIN_ID_DEC"
    else
        # It's open but hidden -> Bring to front
        wmctrl -ia "$TARGET_WIN_ID"
    fi
else
    # Window does not exist -> Launch new
    xfce4-terminal --maximize --title="$WIN_TITLE" --disable-server --command="/bin/bash -c '/usr/bin/sessions.sh; exec bash'" &
fi

```

**3. Save and Make Executable:**
Press `Ctrl+O`, `Enter`, then `Ctrl+X`.

```bash
chmod +x ~/scripts/launch_dashboard.sh

```



### **Phase 4: The System Monitor Bar**

This script puts the CPU/RAM/Net stats on your panel.

**1. Create the file:**

```bash
nano ~/scripts/sysmon_ultimate.sh

```

**2. Paste this code:**

```bash
#!/bin/bash
INTERFACE="eth0" # CHANGE THIS to wlan0 if using Wi-Fi!

# Icons
ICON_CPU=""
ICON_RAM=""
ICON_NET=""

# CPU Calc
read cpu a b c previdle e f g h < /proc/stat
prevtotal=$((a+b+c+previdle+e+f+g+h))
sleep 0.5
read cpu a b c idle e f g h < /proc/stat
total=$((a+b+c+idle+e+f+g+h))
cpu_usage=$((100*( (total-prevtotal) - (idle-previdle) ) / (total-prevtotal) ))

# RAM Calc
ram_usage=$(free | grep Mem | awk '{print int($3/$2 * 100)}')

# Network Speed
R1=$(cat /sys/class/net/$INTERFACE/statistics/rx_bytes 2>/dev/null || echo 0)
[ -f "/tmp/.net" ] && R0=$(cat "/tmp/.net") || R0=$R1
diff=$((R1 - R0))
speed=$(echo "scale=1; ($diff * 2) / 1024" | bc)
echo "$R1" > "/tmp/.net"

# Color Logic
get_color() {
    if [ "$1" -ge 90 ]; then echo "#FF5555";
    elif [ "$1" -ge 70 ]; then echo "#F1FA8C";
    else echo "#50FA7B"; fi
}
cpu_col=$(get_color $cpu_usage)
ram_col=$(get_color $ram_usage)

# Output
echo "<txt><span weight='bold' fgcolor='${cpu_col}'>${ICON_CPU} ${cpu_usage}%</span> <span weight='bold' fgcolor='${ram_col}'>${ICON_RAM} ${ram_usage}%</span> <span weight='bold' fgcolor='#8BE9FD'>${ICON_NET} ${speed}KB/s</span></txt>"
echo "<tool>CPU: ${cpu_usage}% | RAM: ${ram_usage}%</tool>"

```

**3. Save and Make Executable:**
Press `Ctrl+O`, `Enter`, then `Ctrl+X`.

```bash
chmod +x ~/scripts/sysmon_ultimate.sh

```



### **Phase 5: The Tray Icon**

This script puts the clickable Shield 🛡️ button on your panel.

**1. Create the file:**

```bash
nano ~/scripts/sec_tray.sh

```

**2. Paste this code:**

```bash
#!/bin/bash
ICON="🛡️"
CLICK_CMD="/home/$USER/scripts/launch_dashboard.sh"
echo "<txt>${ICON}</txt>"
echo "<tool>Tactical Dashboard</tool>"
echo "<click>${CLICK_CMD}</click>"

```

**3. Save and Make Executable:**
Press `Ctrl+O`, `Enter`, then `Ctrl+X`.

```bash
chmod +x ~/scripts/sec_tray.sh

```



### **Phase 6: Final Setup (The Visuals)**

Now we put everything onto your screen.

**1. Add the System Monitor:**

* Right-click your top panel -> **Panel** -> **Add New Items**.
* Select **Generic Monitor** -> Click **Add**.
* Right-click the new item -> **Properties**.
* **Command:** `/home/YOUR_USERNAME/scripts/sysmon_ultimate.sh` (Change `YOUR_USERNAME` to your actual user).
* **Uncheck** Label.
* **Period (s):** `1`.
* **Font:** Select "FiraCode Nerd Font Bold".

**2. Add the Tray Icon (Shield):**

* Add another **Generic Monitor** item.
* Right-click it -> **Properties**.
* **Command:** `/home/YOUR_USERNAME/scripts/sec_tray.sh`
* **Uncheck** Label.
* **Period (s):** `10`.
* **Font:** Select "FiraCode Nerd Font" (Size 14).

**3. Set the Keyboard Shortcut (The "Quake" Toggle):**

* Open App Menu -> **Keyboard** -> **Application Shortcuts**.
* Click **Add**.
* **Command:** `/home/YOUR_USERNAME/scripts/launch_dashboard.sh`
* **Shortcut:** Press `Super+S` (Windows Key + S) or `Ctrl+Alt+T`.
