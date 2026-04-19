import os
import sys
import time
import csv
import subprocess
import importlib.util

def check_and_install_pyserial():
    """Checks for pyserial and installs it if the user agrees."""
    package_name = "serial"
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        print("--- Library Missing ---")
        choice = input("The 'pyserial' library is required for communication. Install it now? (y/n): ").lower()
        if choice == 'y':
            print("Installing library, please wait...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pyserial"])
                print("Installation successful!\n")
                return True
            except Exception as e:
                print(f"Installation failed: {e}")
                sys.exit()
        else:
            print("Cannot continue without the library. Exiting.")
            sys.exit()
    return True

# Ensure library is present before importing serial
check_and_install_pyserial()
import serial

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def parse_ups_data(raw_data):
    """Parses the raw Megatec Q1 response into a dictionary."""
    try:
        data = raw_data.decode('utf-8').strip()
        if data.startswith('('):
            data = data[1:]
        parts = data.split()
        
        if len(parts) < 8:
            return None

        return {
            "Timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "Input Voltage": parts[0],
            "Fault Voltage": parts[1],
            "Output Voltage": parts[2],
            "Load %": parts[3],
            "Frequency": parts[4],
            "Battery Voltage": parts[5],
            "Temperature": parts[6],
            "Status Bits": parts[7]
        }
    except Exception:
        return None

def main():
    clear_screen()
    print("========================================")
    print("     UNIVERSAL UPS MONITOR & LOGGER     ")
    print("========================================\n")
    
    port = input("Enter COM Port (e.g., COM5): ").upper()
    baud = input("Enter Baud Rate (Default 2400): ") or 2400
    csv_file = "ups_data_log.csv"

    try:
        ser = serial.Serial(port, baudrate=int(baud), timeout=2)
        print(f"\n[OK] Connected to {port}. Logging to {csv_file}...")
        time.sleep(1)

        # Check if CSV exists to write header
        file_exists = os.path.isfile(csv_file)

        while True:
            ser.write(b"Q1\r")
            raw_response = ser.readline()
            
            if raw_response:
                parsed = parse_ups_data(raw_response)
                
                if parsed:
                    # 1. Update Display
                    clear_screen()
                    print(f"--- UPS REAL-TIME DASHBOARD ({port}) ---")
                    print(f"Current Time: {parsed['Timestamp']}")
                    print("-" * 40)
                    for key, value in parsed.items():
                        if key != "Timestamp":
                            print(f"{key:<18}: {value}")
                    print("-" * 40)
                    print(f"Logging to: {os.path.abspath(csv_file)}")
                    print("Press Ctrl+C to stop the program.")

                    # 2. Save to CSV
                    with open(csv_file, mode='a', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=parsed.keys())
                        if not file_exists:
                            writer.writeheader()
                            file_exists = True
                        writer.writerow(parsed)
                else:
                    print("Received invalid data format...")
            else:
                print("WARNING: No response from UPS. Check cables.")
            
            time.sleep(1) # Frequency of updates

    except serial.SerialException as e:
        print(f"\n[ERROR] Could not open port! {e}")
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Port closed safely.")

if __name__ == "__main__":
    main()
