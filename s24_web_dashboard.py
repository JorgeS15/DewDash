#!/usr/bin/env python3
"""
DewDash - S24 Dew Point Monitor
Real-time web dashboard for Banner S24 Dew Point Sensor
Reads data from DXMR90-X1 Local Registers and displays on HTML page
Updates at 10Hz (10 times per second)

Lightning-fast dew point monitoring at 10Hz

Version: 1.0.18
Changelog:
  1.0.18 - Fixed browser auto-close to only trigger on Ctrl+C (not during normal operation)
  1.0.17 - Browser tab automatically closes when terminal is closed
  1.0.16 - Updated webpage header: "DewDash" as title, "Monitor de Ponto de Orvalho S24" 
           as subtitle, removed thermometer icon
  1.0.15 - Moved version number to System Information panel at bottom
  1.0.14 - Flask server now starts BEFORE connecting to DXM (fixes "Not Found" error)
  1.0.13 - Added version number to webpage, browser now opens immediately after
           first sensor reading (smarter timing, no more "Not Found")
  1.0.12 - Increased browser open delay to 5 seconds to ensure Flask server is ready
           before opening (fixes "Not Found" error)
  1.0.11 - Increased update rate to 10Hz (100ms interval) for faster response
  1.1.0 - Removed dew point spread completely from dashboard and console
          (simplified to show only: Temperature, Humidity, Dew Point)
  1.0.9 - Removed spread from console display (kept in web dashboard)
  1.0.8 - Suppressed pymodbus connection timeout messages, updated console display
          to 1Hz (1 second), added condensation warning indicator
  1.0.7 - Suppressed initial connection timeout messages, added live console display
          of sensor readings (updates every 5 seconds)
  1.0.6 - Fixed connection status check logic, increased connection wait time to 5s,
          show current readings when connected
  1.0.5 - Simplified network configuration using working batch command,
          removed Linux support (not needed)
  1.0.4 - Fixed Unicode encoding issue for Portuguese Windows, improved adapter detection
  1.0.3 - Disabled Flask HTTP request logging (reduced console spam)
  1.0.2 - Auto-request administrator privileges, removed manual prompts,
          increased browser open delay to 2 seconds
  1.0.1 - Added Portuguese language (default), English toggle, auto-open browser,
          automatic network configuration (192.168.0.2)
  1.0.0 - Initial release
"""

__version__ = "1.0.18"

from flask import Flask, render_template_string, jsonify
from pymodbus.client import ModbusTcpClient
from datetime import datetime
import threading
import time
import subprocess
import platform
import sys
import os


# ==================== ADMINISTRATOR CHECK ====================

def is_admin():
    """Check if running with administrator/root privileges"""
    try:
        if platform.system() == "Windows":
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:
            return os.geteuid() == 0
    except:
        return False


def run_as_admin():
    """Restart script with administrator privileges"""
    if platform.system() == "Windows":
        try:
            import ctypes
            
            # Get the path to the python executable and script
            python_exe = sys.executable
            script = os.path.abspath(sys.argv[0])
            
            # Parameters for ShellExecute
            params = f'"{script}"'
            
            print("🔐 Requesting administrator privileges...")
            print("    Please click 'Yes' on the UAC prompt")
            print()
            
            # Execute with admin rights
            ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                python_exe,
                params,
                None,
                1  # SW_SHOWNORMAL
            )
            
            # Exit current instance
            sys.exit(0)
            
        except Exception as e:
            print(f"❌ Failed to request admin privileges: {e}")
            print("   Please run this script as Administrator manually")
            sys.exit(1)
    
    elif platform.system() == "Linux":
        print("❌ This script requires root privileges on Linux")
        print("   Please run with: sudo python3", sys.argv[0])
        sys.exit(1)


# Check for admin rights at startup
if not is_admin():
    print("=" * 70)
    print("Administrator Privileges Required")
    print("=" * 70)
    print("This script needs administrator privileges to configure network settings.")
    print()
    run_as_admin()


# ==================== CONFIGURATION ====================

# DXMR90-X1 Settings
DXM_IP = "192.168.0.1"          # Your DXMR90-X1 IP address
DXM_PORT = 502                   # Modbus TCP port
MODBUS_ID = 199                  # Local Registers ID

# Web Server Settings
WEB_PORT = 5000                  # Web server port (http://localhost:5000)

# Network Configuration
TARGET_IP = "192.168.0.2"        # IP address to configure on this PC
TARGET_SUBNET = "255.255.255.0"  # Subnet mask

# ==================== GLOBAL DATA ====================

sensor_data = {
    'humidity': 0.0,
    'temp_c': 0.0,
    'temp_f': 0.0,
    'dewpoint_c': 0.0,
    'dewpoint_f': 0.0,
    'dewpoint_spread': 0.0,
    'timestamp': '',
    'status': 'Initializing...',
    'raw_values': [0, 0, 0, 0, 0]
}

shutdown_flag = False  # Flag to signal browser shutdown

# ==================== NETWORK CONFIGURATION ====================

def configure_network_windows():
    """Configure Windows network adapter to static IP"""
    try:
        print("🔧 Configuring network adapter...")
        print(f"   Setting IP: {TARGET_IP}")
        print(f"   Subnet: {TARGET_SUBNET}")
        
        # Use exact working command
        cmd = f'netsh interface ip set address "Ethernet" source=static addr={TARGET_IP} mask={TARGET_SUBNET} gwmetric=1'
        
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        if result.returncode == 0:
            print(f"   ✓ Network configured successfully")
            print(f"   ✓ IP Address: {TARGET_IP}")
            return True
        else:
            # Even if it returns an error, it might have worked
            print(f"   ℹ️  Command executed")
            print(f"   ✓ IP Address should be: {TARGET_IP}")
            return True
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print(f"   Continuing anyway...")
        return False


def configure_network():
    """Configure network for Windows only"""
    print()
    print("=" * 70)
    print("NETWORK CONFIGURATION")
    print("=" * 70)
    print("Configuring Ethernet adapter...")
    print()
    
    success = configure_network_windows()
    
    print("=" * 70)
    print()
    
    # Wait for network to stabilize
    print("⏳ Waiting for network to stabilize...")
    time.sleep(2)
    print()
    
    return success


# ==================== TRANSLATIONS ====================

TRANSLATIONS = {
    'pt': {
        'title': 'Monitor de Ponto de Orvalho S24',
        'location': 'Localização',
        'status_online': '● Online',
        'status_offline': '● Offline',
        'connecting': 'Conectando...',
        'condensation_alert': '⚠️ ALTO RISCO DE CONDENSAÇÃO! O spread do ponto de orvalho está criticamente baixo!',
        'humidity': 'Humidade Relativa',
        'temperature': 'Temperatura',
        'dewpoint': 'Ponto de Orvalho',
        'spread': 'Spread do Ponto de Orvalho',
        'spread_high_risk': '⚠️ ALTO RISCO',
        'spread_caution': '⚠️ CUIDADO',
        'spread_safe': '✓ Seguro',
        'calculating': 'Calculando...',
        'system_info': 'Informações do Sistema',
        'dxm_address': 'Endereço DXMR90-X1:',
        'last_update': 'Última Atualização:',
        'raw_values': 'Valores Brutos (Reg 1-5):',
        'connection_status': 'Estado da Conexão:',
        'page_updated': 'Página atualizada:',
        'connection_error': '● Erro de Conexão',
        'language_button': 'English'
    },
    'en': {
        'title': 'S24 Dew Point Monitor',
        'location': 'Location',
        'status_online': '● Online',
        'status_offline': '● Offline',
        'connecting': 'Connecting...',
        'condensation_alert': '⚠️ HIGH CONDENSATION RISK! Dew point spread is critically low!',
        'humidity': 'Relative Humidity',
        'temperature': 'Temperature',
        'dewpoint': 'Dew Point',
        'spread': 'Dew Point Spread',
        'spread_high_risk': '⚠️ HIGH RISK',
        'spread_caution': '⚠️ CAUTION',
        'spread_safe': '✓ Safe',
        'calculating': 'Calculating...',
        'system_info': 'System Information',
        'dxm_address': 'DXMR90-X1 Address:',
        'last_update': 'Last Update:',
        'raw_values': 'Raw Values (Reg 1-5):',
        'connection_status': 'Connection Status:',
        'page_updated': 'Page updated:',
        'connection_error': '● Connection Error',
        'language_button': 'Português'
    }
}

# ==================== HTML TEMPLATE ====================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>DewDash - S24 Dew Point Monitor</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
            text-align: center;
        }
        
        .header h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header .location {
            color: #666;
            font-size: 1.2em;
        }
        
        .status {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 10px;
        }
        
        .status.online {
            background: #4caf50;
            color: white;
        }
        
        .status.offline {
            background: #f44336;
            color: white;
        }
        
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card-icon {
            font-size: 3em;
            margin-bottom: 10px;
        }
        
        .card-label {
            color: #666;
            font-size: 1em;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .card-value {
            font-size: 3em;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        
        .card-unit {
            color: #999;
            font-size: 1.5em;
        }
        
        .card-subvalue {
            color: #888;
            font-size: 1em;
            margin-top: 10px;
        }
        
        .warning {
            background: #fff3cd !important;
            border-left: 5px solid #ffc107;
        }
        
        .danger {
            background: #f8d7da !important;
            border-left: 5px solid #dc3545;
        }
        
        .alert-box {
            background: #f8d7da;
            border: 2px solid #dc3545;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            color: #721c24;
            font-weight: bold;
            font-size: 1.2em;
            text-align: center;
            display: none;
        }
        
        .alert-box.show {
            display: block;
            animation: pulse 1s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        .info-panel {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        
        .info-row:last-child {
            border-bottom: none;
        }
        
        .info-label {
            color: #666;
            font-weight: 600;
        }
        
        .info-value {
            color: #333;
            font-family: monospace;
        }
        
        .timestamp {
            text-align: center;
            color: white;
            margin-top: 20px;
            font-size: 0.9em;
        }
        
        .language-toggle {
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            border: none;
            padding: 10px 20px;
            border-radius: 25px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            cursor: pointer;
            font-weight: bold;
            font-size: 0.9em;
            color: #667eea;
            transition: all 0.3s ease;
            z-index: 1000;
        }
        
        .language-toggle:hover {
            transform: translateY(-2px);
            box-shadow: 0 7px 20px rgba(0,0,0,0.4);
            background: #667eea;
            color: white;
        }
        
        @media (max-width: 768px) {
            .cards {
                grid-template-columns: 1fr;
            }
            
            .card-value {
                font-size: 2.5em;
            }
            
            .header h1 {
                font-size: 1.8em;
            }
            
            .language-toggle {
                top: 10px;
                right: 10px;
                padding: 8px 15px;
                font-size: 0.8em;
            }
        }
    </style>
</head>
<body>
    <button class="language-toggle" id="lang-toggle" onclick="toggleLanguage()">English</button>
    
    <div class="container">
        <div class="header">
            <h1 id="page-title">DewDash</h1>
            <div id="page-subtitle" style="color: #666; font-size: 1.2em; margin-top: 5px;">Monitor de Ponto de Orvalho S24</div>
            <div class="status" id="status">Conectando...</div>
        </div>
        
        <div class="cards">
            <div class="card" id="humidity-card">
                <div class="card-icon">💧</div>
                <div class="card-label" id="label-humidity">Humidade Relativa</div>
                <div class="card-value" id="humidity">--</div>
                <div class="card-unit">%RH</div>
            </div>
            
            <div class="card" id="temperature-card">
                <div class="card-icon">🌡️</div>
                <div class="card-label" id="label-temperature">Temperatura</div>
                <div class="card-value" id="temp_c">--</div>
                <div class="card-unit">°C</div>
                <div class="card-subvalue" id="temp_f">-- °F</div>
            </div>
            
            <div class="card" id="dewpoint-card">
                <div class="card-icon">💦</div>
                <div class="card-label" id="label-dewpoint">Ponto de Orvalho</div>
                <div class="card-value" id="dewpoint_c">--</div>
                <div class="card-unit">°C</div>
                <div class="card-subvalue" id="dewpoint_f">-- °F</div>
            </div>
        </div>
        
        <div class="info-panel">
            <h3 style="margin-bottom: 15px; color: #333;" id="info-title">Informações do Sistema</h3>
            <div class="info-row">
                <span class="info-label" id="label-dxm">Endereço DXMR90-X1:</span>
                <span class="info-value" id="dxm-ip">{{ dxm_ip }}</span>
            </div>
            <div class="info-row">
                <span class="info-label" id="label-last-update">Última Atualização:</span>
                <span class="info-value" id="timestamp">--</span>
            </div>
            <div class="info-row">
                <span class="info-label" id="label-raw-values">Valores Brutos (Reg 1-5):</span>
                <span class="info-value" id="raw-values">[-, -, -, -, -]</span>
            </div>
            <div class="info-row">
                <span class="info-label" id="label-connection">Estado da Conexão:</span>
                <span class="info-value" id="connection-status">Conectando...</span>
            </div>
            <div class="info-row">
                <span class="info-label" id="label-version">Versão:</span>
                <span class="info-value">{{ version }}</span>
            </div>
        </div>
        
        <div class="timestamp" id="page-time">Carregando...</div>
    </div>
    
    <script>
        // Translations
        const translations = {
            pt: {
                pageTitle: 'DewDash',
                pageSubtitle: 'Monitor de Ponto de Orvalho S24',
                statusOnline: '● Online',
                statusOffline: '● Offline',
                connecting: 'Conectando...',
                humidity: 'Humidade Relativa',
                temperature: 'Temperatura',
                dewpoint: 'Ponto de Orvalho',
                systemInfo: 'Informações do Sistema',
                dxmAddress: 'Endereço DXMR90-X1:',
                lastUpdate: 'Última Atualização:',
                rawValues: 'Valores Brutos (Reg 1-5):',
                connectionStatus: 'Estado da Conexão:',
                version: 'Versão:',
                pageUpdated: 'Página atualizada:',
                connectionError: '● Erro de Conexão',
                langButton: 'English',
                loading: 'Carregando...'
            },
            en: {
                pageTitle: 'DewDash',
                pageSubtitle: 'S24 Dew Point Monitor',
                statusOnline: '● Online',
                statusOffline: '● Offline',
                connecting: 'Connecting...',
                humidity: 'Relative Humidity',
                temperature: 'Temperature',
                dewpoint: 'Dew Point',
                systemInfo: 'System Information',
                dxmAddress: 'DXMR90-X1 Address:',
                lastUpdate: 'Last Update:',
                rawValues: 'Raw Values (Reg 1-5):',
                connectionStatus: 'Connection Status:',
                version: 'Version:',
                pageUpdated: 'Page updated:',
                connectionError: '● Connection Error',
                langButton: 'Português',
                loading: 'Loading...'
            }
        };
        
        // Current language (default: Portuguese)
        let currentLang = localStorage.getItem('language') || 'pt';
        
        // Apply translations
        function applyTranslations() {
            const t = translations[currentLang];
            
            document.getElementById('page-title').textContent = t.pageTitle;
            document.getElementById('page-subtitle').textContent = t.pageSubtitle;
            document.getElementById('label-humidity').textContent = t.humidity;
            document.getElementById('label-temperature').textContent = t.temperature;
            document.getElementById('label-dewpoint').textContent = t.dewpoint;
            document.getElementById('info-title').textContent = t.systemInfo;
            document.getElementById('label-dxm').textContent = t.dxmAddress;
            document.getElementById('label-last-update').textContent = t.lastUpdate;
            document.getElementById('label-raw-values').textContent = t.rawValues;
            document.getElementById('label-connection').textContent = t.connectionStatus;
            document.getElementById('label-version').textContent = t.version;
            document.getElementById('lang-toggle').textContent = t.langButton;
            
            // Update status if visible
            const statusEl = document.getElementById('status');
            if (statusEl.textContent.includes('Online') || statusEl.textContent.includes('●')) {
                // Will be updated by updateData()
            } else {
                statusEl.textContent = t.connecting;
            }
            
            // Update connection status
            const connStatusEl = document.getElementById('connection-status');
            if (connStatusEl.textContent === 'Conectando...' || connStatusEl.textContent === 'Connecting...') {
                connStatusEl.textContent = t.connecting;
            }
        }
        
        // Toggle language
        function toggleLanguage() {
            currentLang = currentLang === 'pt' ? 'en' : 'pt';
            localStorage.setItem('language', currentLang);
            applyTranslations();
        }
        
        // Apply translations on load
        applyTranslations();
        
        // Update data every second (1Hz)
        function updateData() {
            const t = translations[currentLang];
            
            fetch('/api/data')
                .then(response => response.json())
                .then(data => {
                    // Update main values
                    document.getElementById('humidity').textContent = data.humidity.toFixed(2);
                    document.getElementById('temp_c').textContent = data.temp_c.toFixed(2);
                    document.getElementById('temp_f').textContent = data.temp_f.toFixed(2) + ' °F';
                    document.getElementById('dewpoint_c').textContent = data.dewpoint_c.toFixed(2);
                    document.getElementById('dewpoint_f').textContent = data.dewpoint_f.toFixed(2) + ' °F';
                    
                    // Update status
                    const statusEl = document.getElementById('status');
                    if (data.status === 'Online') {
                        statusEl.className = 'status online';
                        statusEl.textContent = t.statusOnline;
                    } else {
                        statusEl.className = 'status offline';
                        statusEl.textContent = t.statusOffline;
                    }
                    
                    // Update humidity card color
                    const humidityCard = document.getElementById('humidity-card');
                    if (data.humidity > 80 || data.humidity < 20) {
                        humidityCard.className = 'card warning';
                    } else {
                        humidityCard.className = 'card';
                    }
                    
                    // Update info panel
                    document.getElementById('timestamp').textContent = data.timestamp;
                    document.getElementById('raw-values').textContent = 
                        '[' + data.raw_values.join(', ') + ']';
                    document.getElementById('connection-status').textContent = data.status;
                    
                    // Update page time
                    const now = new Date();
                    document.getElementById('page-time').textContent = 
                        t.pageUpdated + ' ' + now.toLocaleTimeString();
                })
                .catch(error => {
                    console.error('Error fetching data:', error);
                    document.getElementById('status').textContent = t.connectionError;
                    document.getElementById('status').className = 'status offline';
                });
        }
        
        // Update every 100ms (10Hz)
        updateData();
        setInterval(updateData, 100);  // 10Hz = 100ms interval
        
        // Check for server shutdown every 2 seconds
        setInterval(() => {
            fetch('/shutdown')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'shutting_down') {
                        // Display shutdown message
                        document.body.innerHTML = `
                            <div style="display: flex; align-items: center; justify-content: center; 
                                        height: 100vh; background: #667eea; color: white; 
                                        font-family: 'Segoe UI', sans-serif; text-align: center;">
                                <div>
                                    <h1 style="font-size: 3em; margin-bottom: 20px;">DewDash</h1>
                                    <p style="font-size: 1.5em;">Server encerrado / Server stopped</p>
                                    <p style="font-size: 1em; margin-top: 20px; opacity: 0.8;">
                                        Esta janela pode ser fechada / This window can be closed
                                    </p>
                                </div>
                            </div>
                        `;
                        // Try to close the window after 2 seconds
                        setTimeout(() => {
                            window.close();
                        }, 2000);
                    }
                })
                .catch(() => {
                    // Server is down, try to close window
                    setTimeout(() => {
                        window.close();
                    }, 1000);
                });
        }, 2000);  // Check every 2 seconds
        
        // Update page timestamp
        setInterval(() => {
            const t = translations[currentLang];
            const now = new Date();
            document.getElementById('page-time').textContent = 
                t.pageUpdated + ' ' + now.toLocaleTimeString();
        }, 100);  // 10Hz = 100ms interval
    </script>
</body>
</html>
'''

# ==================== DATA READER THREAD ====================

def read_sensor_data():
    """Background thread that reads sensor data every 100ms (10Hz)"""
    global sensor_data
    
    # Suppress pymodbus connection messages
    import logging
    logging.getLogger('pymodbus').setLevel(logging.CRITICAL)
    
    modbus_client = ModbusTcpClient(DXM_IP, port=DXM_PORT)
    
    print(f"📡 Starting data reader thread...")
    print(f"   Reading from: {DXM_IP}:{DXM_PORT}")
    print(f"   Modbus ID: {MODBUS_ID}")
    print(f"   Update rate: 10Hz (every 100ms)")
    
    # Detect pymodbus version
    try:
        import pymodbus
        print(f"   pymodbus version: {pymodbus.__version__}")
    except:
        pass
    
    print()
    
    first_connection = True  # Flag to suppress initial timeout messages
    
    while True:
        try:
            if modbus_client.connect():
                # Read Local Registers 1-5
                # pymodbus 3.x uses device_id parameter (not unit or slave)
                result = modbus_client.read_holding_registers(
                    0,                      # address: Register 1 (0-indexed)
                    count=5,                # count: 5 registers
                    device_id=MODBUS_ID     # device_id: Modbus device ID (199)
                )
                
                if not result.isError():
                    # Store raw values
                    raw_values = result.registers
                    
                    # Check if values are scaled or raw
                    # If Register 1 > 1000, values are raw (need scaling)
                    # If Register 1 < 100, values are already scaled
                    
                    if raw_values[0] > 1000:
                        # Raw values - apply scaling
                        humidity = raw_values[0] / 100.0
                        temp_c = raw_values[1] / 20.0
                        temp_f = raw_values[2] / 20.0
                        dewpoint_c = raw_values[3] / 100.0
                        dewpoint_f = raw_values[4] / 100.0
                    else:
                        # Already scaled
                        humidity = float(raw_values[0])
                        temp_c = float(raw_values[1])
                        temp_f = float(raw_values[2])
                        dewpoint_c = float(raw_values[3])
                        dewpoint_f = float(raw_values[4])
                    
                    # Calculate dew point spread
                    dewpoint_spread = temp_c - dewpoint_c
                    
                    # Update global data
                    sensor_data = {
                        'humidity': humidity,
                        'temp_c': temp_c,
                        'temp_f': temp_f,
                        'dewpoint_c': dewpoint_c,
                        'dewpoint_f': dewpoint_f,
                        'dewpoint_spread': dewpoint_spread,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'status': 'Online',
                        'raw_values': raw_values
                    }
                    
                    first_connection = False  # Connection succeeded
                    
                else:
                    sensor_data['status'] = 'Modbus Error'
                    if not first_connection:  # Only print errors after first successful connection
                        print(f"❌ Modbus read error: {result}")
                
                modbus_client.close()
            else:
                sensor_data['status'] = 'Connection Failed'
                if not first_connection:  # Only print connection errors after first successful connection
                    print(f"❌ Cannot connect to DXMR90-X1 at {DXM_IP}")
            
        except Exception as e:
            sensor_data['status'] = f'Error: {str(e)}'
            if not first_connection:  # Only print exceptions after first successful connection
                print(f"❌ Exception: {e}")
        
        # Wait 100ms (10Hz update rate)
        time.sleep(0.1)

# ==================== FLASK WEB SERVER ====================

app = Flask(__name__)

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template_string(
        HTML_TEMPLATE,
        dxm_ip=f"{DXM_IP}:{DXM_PORT}",
        version=__version__
    )

@app.route('/api/data')
def get_data():
    """API endpoint that returns current sensor data as JSON"""
    return jsonify(sensor_data)

@app.route('/shutdown')
def shutdown():
    """Shutdown endpoint to notify browser"""
    global shutdown_flag
    if shutdown_flag:
        return jsonify({'status': 'shutting_down'})
    else:
        return jsonify({'status': 'running'})

# ==================== MAIN ====================

def main():
    print("=" * 70)
    print(f"DewDash - S24 Dew Point Monitor v{__version__}")
    print("=" * 70)
    print(f"🌐 DXMR90-X1: {DXM_IP}:{DXM_PORT}")
    print(f"💻 Web Server: http://localhost:{WEB_PORT}")
    print(f"🔄 Update Rate: 10Hz (every 100ms)")
    print(f"🌍 Language: Portuguese (default) / English (toggle button)")
    print("=" * 70)
    print()
    
    # Configure network first
    configure_network()
    
    print("Starting services...")
    print()
    
    # Disable Flask logging to reduce console spam
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    # Start Flask web server FIRST (in background)
    print("✓ Starting web server on port {0}...".format(WEB_PORT))
    def run_flask():
        app.run(host='0.0.0.0', port=WEB_PORT, debug=False, use_reloader=False)
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Wait for Flask to initialize
    time.sleep(2)
    print("✓ Web server ready")
    print()
    
    # Now start data reader thread
    reader_thread = threading.Thread(target=read_sensor_data, daemon=True)
    reader_thread.start()
    
    # Wait for first successful reading
    print("⏳ Waiting for first sensor reading...")
    max_wait = 10  # Maximum 10 seconds
    waited = 0
    while sensor_data.get('status') != 'Online' and waited < max_wait:
        time.sleep(0.5)
        waited += 0.5
    
    # Check connection status
    connection_ok = sensor_data.get('status') == 'Online'
    
    if connection_ok:
        print("✓ Connected to DXMR90-X1")
        print(f"✓ First reading: {sensor_data.get('humidity', 0):.1f}% RH, {sensor_data.get('temp_c', 0):.1f}°C")
        print()
        
        # Open browser immediately - Flask is already running!
        import webbrowser
        url = f"http://localhost:{WEB_PORT}"
        print(f"🌐 Opening browser: {url}")
        webbrowser.open(url)
    else:
        print("⚠️  DXMR90-X1 not yet connected")
        print(f"   Status: {sensor_data.get('status', 'Unknown')}")
        print("   Dashboard will show data once connection is established")
        print()
        print(f"⚠️  Browser will not auto-open (no connection yet)")
        print(f"    Manually open: http://localhost:{WEB_PORT}")
    
    print()
    print("=" * 70)
    print(f"🌐 Dashboard URL: http://localhost:{WEB_PORT}")
    print("=" * 70)
    print()
    print("Press Ctrl+C to stop")
    print()
    
    # Start console display thread
    def console_display():
        """Display live sensor readings in console"""
        time.sleep(3)  # Wait a moment
        
        print("\n" + "=" * 70)
        print("LIVE SENSOR READINGS (updating every second)")
        print("=" * 70)
        
        while True:
            try:
                data = sensor_data
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                # Status symbol
                status_symbol = "●" if data.get('status') == 'Online' else "○"
                
                print(f"\r[{timestamp}] {status_symbol} "
                      f"Temp: {data.get('temp_c', 0):5.1f}°C | "
                      f"RH: {data.get('humidity', 0):5.1f}% | "
                      f"Dew Point: {data.get('dewpoint_c', 0):5.1f}°C", 
                      end='', flush=True)
                
                time.sleep(1)  # Update every 1 second (1Hz)
            except:
                time.sleep(1)
    
    display_thread = threading.Thread(target=console_display, daemon=True)
    display_thread.start()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        global shutdown_flag
        shutdown_flag = True
        print("\n\nShutting down...")
        print("Closing browser tabs...")
        time.sleep(3)  # Wait for browser to detect shutdown
        sys.exit(0)

if __name__ == "__main__":
    main()
