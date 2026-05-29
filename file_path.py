import json
import win32com.client
import winreg
import os
import pythoncom
import concurrent.futures
import difflib
import psutil

def registry():
    apps = {}
    paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    ]

    for path in paths:
        try:
            main_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
            num_subkeys = winreg.QueryInfoKey(main_key)[0]
            
            for i in range(num_subkeys):
                try:
                    subkey_name = winreg.EnumKey(main_key, i)
                    subkey = winreg.OpenKey(main_key, subkey_name)
                    
                    display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                    display_icon, _ = winreg.QueryValueEx(subkey, "DisplayIcon")
                    
                    app_name = display_name.lower().strip()
                    exe_path = display_icon.split(',')[0].strip('"')
                    
                    if exe_path.endswith('.exe') and os.path.exists(exe_path):
                        apps[app_name] = exe_path
                        
                    winreg.CloseKey(subkey)
                except OSError:
                    continue
            winreg.CloseKey(main_key)
        except Exception:
            pass 
            
    return apps

def start_menu():
    pythoncom.CoInitialize()
    
    apps = {}
    shell = win32com.client.Dispatch("WScript.Shell")
    
    paths = [
        os.path.join(os.environ["ProgramData"], r"Microsoft\Windows\Start Menu\Programs"),
        os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs")
    ]
    
    for path in paths:
        if not os.path.exists(path):
            continue
            
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".lnk"):
                    shortcut_path = os.path.join(root, file)
                    try:
                        shortcut = shell.CreateShortCut(shortcut_path)
                        target_path = shortcut.Targetpath
                        
                        if target_path.endswith('.exe') and os.path.exists(target_path):
                            app_name = file.replace(".lnk", "").lower().strip()
                            apps[app_name] = target_path
                    except Exception:
                        continue
                        
    pythoncom.CoUninitialize() 
    return apps

def build_memory_layer(output_file="apps.json"):    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_registry = executor.submit(registry)
        future_start_menu = executor.submit(start_menu)
        
        registry_apps = future_registry.result()
        start_menu_apps = future_start_menu.result()


    system_apps = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "file explorer": "explorer.exe",
        "paint": "mspaint.exe",
        "settings": "ms-settings:"
    }

    final_database = system_apps.copy()    

    for app_name, target_path in registry_apps.items():
        if app_name not in final_database:
            final_database[app_name] = target_path

    collision_report = []

    for app_name, target_path in start_menu_apps.items():
        original_app_name = app_name
        counter = 2
        
        while app_name in final_database and final_database[app_name].lower() != target_path.lower():
            app_name = f"{original_app_name} {counter}"
            counter += 1
            
        if app_name != original_app_name:
            collision_report.append(f"Saved duplicate '{original_app_name}' as '{app_name}'")
            
        final_database[app_name] = target_path
    
    with open(output_file, 'w') as f:
        json.dump(final_database, f, indent=4)
        
    if collision_report:
        for report in collision_report:
            print(f"  -> {report}")
    return final_database

def get_siblings(base_name, apps_dict):
    siblings = []
    for key in apps_dict.keys():
        if key == base_name or (key.startswith(base_name + " ") and key[len(base_name)+1:].isdigit()):
            siblings.append(key)
    return siblings

def execute_app(target_path, app_name):
    try:
        os.startfile(target_path)
    except Exception as e:
        print(f"[Luna System Error] Could not launch {app_name}: {e}")

def close_app(target_path, app_name):
    try:
        target_name = os.path.basename(target_path).lower()
        for app in psutil.process_iter(['pid', 'name']):
            try:
                if app.info.get('name') and app.info['name'].lower() == target_name:
                    app.kill()
            except Exception as e:
                print(f"Error: {e}")
                continue        
    except Exception as e:
        print(f"Unable to close {app_name}: {e}")        

def handle_voice_command(command, apps_dict, cutoff_score=0.6):
    target_app = command.lower().replace("open ", "").strip()
    
    base_match = None
    if target_app in apps_dict:
        base_match = target_app
    else:
        possible_matches = difflib.get_close_matches(target_app, apps_dict.keys(), n=1, cutoff=cutoff_score)
        if possible_matches:
            base_match = possible_matches[0]            
            words = base_match.split()
            if len(words) > 1 and words[-1].isdigit():
                base_match = " ".join(words[:-1])
    
    if base_match:
        siblings = get_siblings(base_match, apps_dict)
        
        if len(siblings) == 1:
            execute_app(apps_dict[siblings[0]], siblings[0])
            
        else:
            print(f"\nFound multiple versions of '{base_match}':")
            for i, sibling in enumerate(siblings):
                print(f"  [{i + 1}] {sibling}")
                
            choice = input(f"Please type the number of the one you want (1-{len(siblings)}), or 'cancel': ")
            
            if choice.isdigit() and 1 <= int(choice) <= len(siblings):
                selected_app = siblings[int(choice) - 1]
                execute_app(apps_dict[selected_app], selected_app)
            else:
                print("Launch cancelled.")
    else:
        print(f"Cannot find any installed application sounding like '{target_app}'.")

def handle_closing(command, apps_dict, cutoff_score=0.6):
    target_app = command.lower().replace("close ", "").strip()      
    base_match = None
    if target_app in apps_dict:
        base_match = target_app
    else:
        possible_matches = difflib.get_close_matches(target_app, apps_dict.keys(), n=1, cutoff=cutoff_score)
        if possible_matches:
            base_match = possible_matches[0]
    if base_match:
        close_app(apps_dict[base_match], base_match)
    else:
        print(f"Cannot find any running application sounding like '{target_app}' to close.")        

def run(user_input):
    json_path = "apps.json"
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            apps_database = json.load(f)
    else:
        apps_database = build_memory_layer(json_path)
    if "open" in user_input:
        handle_voice_command(user_input, apps_database) 
    else:
        handle_closing(user_input,apps_database)                