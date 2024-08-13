import json

json_path = "config.json"
def Load_Config():
    try:
        with open(json_path, 'r') as file:
            return json.load(file)
        
    except json.JSONDecodeError:
        print("Lỗi: File JSON không đúng định dạng.")
    except FileNotFoundError:
        print("Lỗi: File JSON không tồn tại.")
    except IOError:
        print(f"Lỗi: Không thể đọc file {json_path}.")       

def Write_Config(data):
    try:
        with open(json_path, 'w') as file:
            json.dump(data, file, indent = 4)
        
    except FileNotFoundError:
        print("Lỗi: File không tồn tại hoặc đường dẫn không hợp lệ.")
    except PermissionError:
        print("Lỗi: Không có quyền ghi file JSON.")
    except IOError:
        print(f"Lỗi: Không thể đọc file {json_path}.")       
        

