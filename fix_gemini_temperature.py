import os
import sys
import glob

def find_files_with_temperature_param():
    """Find all Python files that use the temperature parameter with Gemini"""
    python_files = glob.glob("**/*.py", recursive=True)
    files_with_temperature = []
    
    for file_path in python_files:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            try:
                content = file.read()
                if "generate_content" in content and "temperature" in content:
                    files_with_temperature.append(file_path)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    return files_with_temperature

def fix_files(files):
    """Fix files that use the temperature parameter with Gemini"""
    print(f"Found {len(files)} files to fix:")
    for file_path in files:
        print(f"  - {file_path}")
    
    print("\nWould you like to fix these files? (y/n)")
    choice = input().lower()
    
    if choice != 'y':
        print("Aborted.")
        return
    
    for file_path in files:
        fix_file(file_path)

def fix_file(file_path):
    """Fix a specific file by adding generation_config"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        lines = file.readlines()
    
    new_lines = []
    changes_made = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check if this line contains a generate_content call with temperature
        if "generate_content" in line and "temperature" in line:
            # Simple one-line replacement
            if ".generate_content(" in line and '"generation_config":{"temperature":' in line:
                # Split the line parts
                pre_part = line.split(".generate_content(")[0]
                params = line.split(".generate_content(")[1]
                
                # Extract temperature value
                temp_parts = params.split("temperature=")[1]
                temp_value = ""
                for char in temp_parts:
                    if char.isdigit() or char == '.':
                        temp_value += char
                    else:
                        break
                
                # Replace with generation_config
                new_line = f"{pre_part}.generate_content({params.replace(f'generation_config={"temperature": }{temp_value}', f'generation_config={{\"temperature\": {temp_value}}}')}"
                new_lines.append(new_line)
                changes_made = True
                print(f"Fixed single-line temperature parameter in {file_path}")
            else:
                # More complex multi-line fix
                next_lines = []
                brackets_depth = line.count('(') - line.count(')')
                next_lines.append(line)
                
                temp_value = None
                temp_line_index = -1
                
                # Collect all lines of the function call and find temperature
                j = i + 1
                while j < len(lines) and brackets_depth > 0:
                    next_line = lines[j]
                    next_lines.append(next_line)
                    brackets_depth += next_line.count('(') - next_line.count(')')
                    
                    if "temperature=" in next_line:
                        temp_line_index = len(next_lines) - 1
                        temp_parts = next_line.split("temperature=")[1]
                        temp_value = ""
                        for char in temp_parts:
                            if char.isdigit() or char == '.':
                                temp_value += char
                            else:
                                break
                    
                    j += 1
                
                # If we found temperature, replace it with generation_config
                if temp_value is not None and temp_line_index >= 0:
                    temp_line = next_lines[temp_line_index]
                    if "," in temp_line:
                        # If the line has other parameters
                        new_temp_line = temp_line.replace(f"temperature={temp_value},", f"generation_config={{\"temperature\": {temp_value}}},")
                        new_temp_line = new_temp_line.replace(f"temperature={temp_value}", f"generation_config={{\"temperature\": {temp_value}}}")
                        next_lines[temp_line_index] = new_temp_line
                    else:
                        # If temperature is the only parameter on this line
                        next_lines[temp_line_index] = temp_line.replace(f"temperature={temp_value}", f"generation_config={{\"temperature\": {temp_value}}}")
                    
                    new_lines.extend(next_lines)
                    i = j - 1  # Skip the lines we've already processed
                    changes_made = True
                    print(f"Fixed multi-line temperature parameter in {file_path}")
                else:
                    # No temperature found in the multi-line call
                    new_lines.extend(next_lines)
                    i = j - 1
        else:
            new_lines.append(line)
        
        i += 1
    
    if changes_made:
        # Create backup of the original file
        backup_path = f"{file_path}.bak"
        with open(backup_path, 'w', encoding='utf-8') as backup_file:
            backup_file.writelines(lines)
        
        # Write the fixed file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(new_lines)
        
        print(f"Fixed {file_path} (original backed up to {backup_path})")
    else:
        print(f"No changes needed in {file_path}")

def main():
    print("Gemini Temperature Parameter Fix")
    print("==============================\n")
    
    print("This script finds and fixes uses of the 'temperature' parameter in Gemini API calls.")
    print("The temperature parameter syntax has changed and now requires generation_config.")
    
    # Find files to fix
    files = find_files_with_temperature_param()
    
    if not files:
        print("\nNo files found that need fixing.")
        return
    
    fix_files(files)
    
    print("\nDone! Remember to test your application after these changes.")

if __name__ == "__main__":
    main() 