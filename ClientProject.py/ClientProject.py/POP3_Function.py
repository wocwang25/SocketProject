import json
import socket
import re
import base64
import os
import JSON_Function
import threading

POP3_port = 1100
SMTP_server = '127.0.0.1'
uidl_file_path = 'downloaded_uidls.txt'

# Hàm đọc uidl từ file và kiểm tra xem uidl cụ thể có tồn tại hay không
def check_uidl_exists(filepath, uidl):
    try:
        with open(filepath, 'r') as file:
            if uidl not in file.read():
                return True
    except FileNotFoundError:
        pass
    return False
    
# Hàm lưu UIDL vào file
def save_downloaded_uidl( uidl):
    with open(uidl_file_path, 'a+') as file:
        file.seek(0)  # Di chuyển con trỏ về đầu file
        if uidl not in file.read():
            file.write(uidl + '\n')
         
# Vòng lặp lấy full nội dung mail cho đến khi gặp kí tự kết thúc
def receive_full_message(Client_Socket):
    CHUNK = []
    while True:
        chunk = Client_Socket.recv(1024).decode('utf-8')  
        if not chunk:  # Nếu không nhận được thêm dữ liệu, kết thúc vòng lặp
            break
        CHUNK.append(chunk)
        if chunk.endswith('.\r\n'):  # Kiểm tra ký tự kết thúc của email trong POP3
            break
    return ''.join(CHUNK)

def find_boundary(mail_content):
    # Tách header từ body
    header, _ = mail_content.split('\r\n\r\n', 1)

    # Tìm dòng Content-Type trong header
    for line in header.split('\r\n'):
        if line.startswith('Content-Type:'):
            # Tìm boundary trong dòng Content-Type
            boundary_match = re.search(r'boundary="([^"]+)"', line)
            if boundary_match:
                # Trả về giá trị boundary
                return boundary_match.group(1)
    # Nếu không tìm thấy boundary, trả về None
    return None

def Save_file(Client_Socket, username, password, save, folder_path, uidl):
    # Kết nối tới máy chủ POP3
    Client_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    Client_Socket.connect((SMTP_server, POP3_port))
    server_response = Client_Socket.recv(1024).decode()

    # Gửi lệnh USER và nhận phản hồi    
    Client_Socket.send(f'USER {username}\r\n'.encode())
    server_response = Client_Socket.recv(1024).decode()

    # Gửi lệnh PASS và nhận phản hồi
    Client_Socket.send(f'PASS {password}\r\n'.encode())
    server_response = Client_Socket.recv(1024).decode()
    
    # Cài đặt mã uidl để định danh từng mail
    Client_Socket.send('UIDL\r\n'.encode())
    server_response = Client_Socket.recv(4096).decode()
    
    # Lưu trữ uidl của từng mail
    mail_ID = {}    #mail_ID được định nghĩa như một từ điển vì thứ tự các uidl được tính từ 1
    ID = server_response.split('\r\n')
    for line in ID:
        part = line.split(' ')
        if len(part) == 2:
            save_downloaded_uidl(part[1])
            mail_ID[part[0]] = part[1]
            
    # Gửi lệnh STAT và nhận phản hồi
    Client_Socket.send('STAT\r\n'.encode())
    server_response = Client_Socket.recv(4096).decode()

    #Gửi lệnh LIST lấy danh sách các email trong hộp thư
    Client_Socket.send('LIST\r\n'.encode())
    server_response = Client_Socket.recv(4096).decode()
    
    #Ngăn cách thông tin trả về từ hộp thư bằng kí tự xuống dòng
    list_part = server_response.split('\r\n')    
    mail_index = []
    for line in list_part[1:]:
        part = line.split(' ')
        if (len(part) >= 2):
            mail_index.append(part[0])   #Lấy phần tử đầu tiên của line 
    
    for index in mail_index:
        current_uidl = mail_ID[index]
        if current_uidl == uidl:  # Kiểm tra nếu UIDL khớp
            Client_Socket.send(f'RETR {index}\r\n'.encode())
            mail_content = receive_full_message(Client_Socket)
            if save:
                #Khai báo boundary đã được dùng để ngăn cách các phần của mail được gửi
                boundary = find_boundary(mail_content)
                email_parts = mail_content.split(f"--{boundary}")
            
                # tìm nội dung file trong mail
                for part in email_parts:
                    if 'Content-Disposition: attachment;' in part:
                        # Tìm tên file
                        FILE_NAME = re.compile(r"filename=\"(.*?)\"")
                        filename = FILE_NAME.search(part).group(1)

                        # Tìm nội dung base64 của file
                        file_content_encoded = part.split('\r\n\r\n')[1].split('\r\n--')[0]

                        # Giải mã và lưu file
                        file_content_encoded = file_content_encoded.replace('\r', '').replace('\n', '').replace(' ', '')
                        file_content_decoded = base64.b64decode(file_content_encoded)
                        attachment_path = os.path.join(folder_path, filename)
                        with open(attachment_path, 'wb') as file:
                            file.write(file_content_decoded)
        else:
            continue

    Client_Socket.send('QUIT\r\n'.encode())
    Client_Socket.close()
    print('Tải FILE thành công!')

def Save_Mail_AutoMode(Client_Socket, username, password):
    # Kết nối tới máy chủ POP3
    Client_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    Client_Socket.connect((SMTP_server, POP3_port))
    server_response = Client_Socket.recv(1024).decode()

    # Gửi lệnh USER và nhận phản hồi    
    Client_Socket.send(f'USER {username}\r\n'.encode())
    server_response = Client_Socket.recv(1024).decode()

    # Gửi lệnh PASS và nhận phản hồi
    Client_Socket.send(f'PASS {password}\r\n'.encode())
    server_response = Client_Socket.recv(1024).decode()
    
    # Cài đặt mã uidl để định danh từng mail
    Client_Socket.send('UIDL\r\n'.encode())
    server_response = Client_Socket.recv(4096).decode()
    
    # Lưu trữ uidl của từng mail
    mail_ID = {}    #mail_ID được định nghĩa như một từ điển vì thứ tự các uidl được tính từ 1
    ID = server_response.split('\r\n')
    for line in ID:
        part = line.split(' ')
        if len(part) == 2:
            save_downloaded_uidl(part[1])
            mail_ID[part[0]] = part[1]
            
    # Gửi lệnh STAT và nhận phản hồi
    Client_Socket.send('STAT\r\n'.encode())
    server_response = Client_Socket.recv(4096).decode()

    #Gửi lệnh LIST lấy danh sách các email trong hộp thư
    Client_Socket.send('LIST\r\n'.encode())
    server_response = Client_Socket.recv(4096).decode()
    
    #Ngăn cách thông tin trả về từ hộp thư bằng kí tự xuống dòng
    list_part = server_response.split('\r\n')    
    mail_index = []
    for line in list_part[1:]:
        part = line.split(' ')
        if (len(part) >= 2):
            mail_index.append(part[0])   #Lấy phần tử đầu tiên của line 

    for index in mail_index:
        if check_uidl_exists(uidl_file_path, mail_ID[index]) == False:
            Client_Socket.send(f'RETR {index}\r\n'.encode())
            mail_content = receive_full_message(Client_Socket)
            folder_path = Filter(mail_content)
            mail_filename = f'email_{mail_ID[index]}.txt' 
            with open(os.path.join(folder_path, mail_filename), 'w') as file:
                file.write(mail_content)
                            
            #Khai báo boundary đã được dùng để ngăn cách các phần của mail được gửi
            #boundary = find_boundary(mail_content)
            #email_parts = mail_content.split(f"--{boundary}")
            
            # tìm nội dung file trong mail
            #for part in email_parts:
            #   if 'Content-Disposition: attachment;' in part:
            #       # Tìm tên file
            #       FILE_NAME = re.compile(r"filename=\"(.*?)\"")
            #       filename = FILE_NAME.search(part).group(1)
            #
            #       # Tìm nội dung base64 của file
            #       file_content_encoded = part.split('\r\n\r\n')[1].split('\r\n--')[0]
            #
            #       # Giải mã và lưu file
            #       file_content_encoded = file_content_encoded.replace('\r', '').replace('\n', '').replace(' ', '')
            #       file_content_decoded = base64.b64decode(file_content_encoded)
            #       attachment_path = os.path.join(folder_path, filename)
            #       with open(attachment_path, 'wb') as file:
            #           file.write(file_content_decoded)
        else:
            continue

    Client_Socket.send('QUIT\r\n'.encode())
    Client_Socket.close()
    
def Find_Receiver(mail_content):
    start_index = mail_content.find("To:") + len("To:")
    end_index = mail_content.find("\n", start_index)
    Receiver = mail_content[start_index:end_index].strip()
    return Receiver

def Find_Sender(mail_content):
    start_index = mail_content.find("From:") + len("From:")
    end_index = mail_content.find("\r\n", start_index)
    sender_email = mail_content[start_index:end_index].strip()
    return sender_email

def Find_Sender_FromFILE(mail_content):
    start_index = mail_content.find("From:") + len("From:")
    end_index = mail_content.find("\n", start_index)
    sender_email = mail_content[start_index:end_index].strip()
    return sender_email

def Find_Subject(mail_content):
    start_index = mail_content.find("Subject:") + len("Subject:")
    end_index = mail_content.find("\r\n", start_index)
    subject = mail_content[start_index:end_index].strip()
    return subject

def Find_Subject_FromFILE(mail_content):
    start_index = mail_content.find("Subject:") + len("Subject:")
    end_index = mail_content.find("\n", start_index)
    subject = mail_content[start_index:end_index].strip()
    return subject

def Find_Body(mail_content):
    start_index = mail_content.find("Content-Type: text/plain\r\n\r\n") + len("Content-Type: text/plain\r\n\r\n")
    end_index = mail_content.find("END", start_index)
    body = mail_content[start_index:end_index].strip()
    return body

def Find_MailType(mail_content):
    if mail_content.find("multipart/mixed") != -1:
        return True
    return False

def Filter(mail_content):
    sender = Find_Sender(mail_content)
    subject = Find_Subject(mail_content)
    content = Find_Body(mail_content)
    data = JSON_Function.Load_Config()

    state = 'attachment' if Find_MailType(mail_content) else 'no attachment'
    email_without_status = f"<{sender}><{subject}><{state}>"
    email = f"(chưa đọc){email_without_status}"
    
    # Kiểm tra xem email đã tồn tại trong bất kỳ danh mục nào chưa
    if any(email_without_status in data[key] for key in ['Project', 'Important', 'Work', 'Spam', 'Inbox']):
        email = email_without_status

    # Áp dụng các tiêu chí phân loại
    if any(sub in subject for sub in data.get('Subject',[])):
        category = 'Important'
        folder_path = data['Filter'][3]
    elif any(body in content for body in data.get('Content',[])):
        category = 'Work'
        folder_path = data['Filter'][1]
    elif any(spam_keyword in content for spam_keyword in data.get('Spam_Keywords',[])):
        category = 'Spam'
        folder_path = data['Filter'][4]
    elif any(spam_keyword in subject for spam_keyword in data.get('Spam_Keywords',[])):
        category = 'Spam'
        folder_path = data['Filter'][4]
    elif sender in data.get('Sender_Project',[]):
        category = 'Project'
        folder_path = data['Filter'][2]
    else:
        category = 'Inbox'
        folder_path = data['Filter'][0]
        
    if email not in data.get(f'{category}', []):
        data[f'{category}'].append(email)
    JSON_Function.Write_Config(data)
    return folder_path
    
           
    


    
    

    