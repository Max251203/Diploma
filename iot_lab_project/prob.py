import os

def print_directory_structure(path, indent=''):
    print(f"{indent}├── {os.path.basename(path)}")
    
    if os.path.isdir(path):
        indent += '│   '
        items = sorted(os.listdir(path))
        
        for i, item in enumerate(items):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                print_directory_structure(item_path, indent)
            else:
                print(f"{indent}├── {item}")

# Укажите путь к папке проекта
project_path = 'iot_lab_project'
print_directory_structure(project_path)