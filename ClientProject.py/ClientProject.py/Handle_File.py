import base64
from genericpath import getsize
import os
from JSON_Function import *
from re import *
from POP3_Function import *


#Phần quan trọng nhất ở đây là phải thiết lập data của cái mail sao cho nó phù hợp với tiêu chuẩn smtp
def Encode_File(file_path):
    file_size = os.path.getsize(file_path)
    filename = os.path.basename(file_path)
    if file_size > 3145728:  # 3 MB
        print(f"File {filename} vượt quá kích thước cho phép!")
        return None

    encoded_chunks = []
    with open(file_path, "rb") as file:
        while True:
            chunk = file.read(72)  # Đọc từng phần của file
            if not chunk:
                break
            encoded_chunks.append(base64.b64encode(chunk).decode())

    return "\r\n".join(encoded_chunks)

def SEND_EMAIL_FILE(Client_Socket, sender_mail, receiver_list, CC_list, BCC_list, Subject, mail_body, File_list):
    if File_list and len(File_list) == 1:
        if Encode_File(File_list[0]) == None:
           print('Dung lượng file quá lớn nên không thể gửi kèm file!\nTiến trình gửi không thành công!')
           return
    #Mail người gửi
    Client_Socket.send(f'MAIL FROM: <{sender_mail}>\r\n'.encode())
    server_response = Client_Socket.recv(1024).decode()
    print("RCPT TO response: ", server_response)

    #Mail người nhận
    for person in receiver_list:
        Client_Socket.send(f'RCPT TO: <{person}>\r\n'.encode())
        server_response = Client_Socket.recv(1024).decode()
        print("RCPT TO response: ", server_response)

    #Gửi bản sao của cái mail tới người nhận chính ở trên tới một nay nhiều người gì đó
    for cc in CC_list:
        Client_Socket.send(f'RCPT TO: <{cc}>\r\n'.encode())
        server_response = Client_Socket.recv(1024).decode()
        print("RCPT TO response: ", server_response)

    for bcc in BCC_list:
        Client_Socket.send(f'RCPT TO: <{bcc}>\r\n'.encode())
        server_response = Client_Socket.recv(1024).decode()
        print("RCPT TO response: ", server_response)

    Client_Socket.send(f'DATA\r\n'.encode())
    server_response = Client_Socket.recv(1024).decode()
    print("Data response: ", server_response)
    
    if File_list:             
        boundary = "----=_Part_Boundary_YuSato"  # Tạo một chuỗi boundary hợp lý
        mail_content = f"From: {sender_mail}\r\nTo: {','.join(receiver_list)}\r\nCC: {','.join(CC_list)}\r\nSubject: {Subject}\r\n"
        mail_content += f"Content-Type: multipart/mixed; boundary=\"{boundary}\"\r\n"

        # Thêm phần thân của email
        mail_body = mail_body.replace("\n", "\r\n")
        mail_content += f"--{boundary}\r\nContent-Type: text/plain\r\n{mail_body}\r\n"

        # Thêm file đính kèm
        for file in File_list:
            encoded_file = Encode_File(file)
            if encoded_file:
                filename = os.path.basename(file)
                mail_content += f"--{boundary}\r\n"
                mail_content += f"Content-Type: application/octet-stream; name=\"{filename}\"\r\n"
                mail_content += f"Content-Transfer-Encoding: base64\r\n"
                mail_content += f"Content-Disposition: attachment; filename=\"{filename}\"\r\n\r\n"
                mail_content += encoded_file + "\r\n"
        # Kết thúc MIME
        mail_content += f"--{boundary}--\r\n"
    else:  
        mail_content = f"From: {sender_mail}\r\nTo: {','.join(receiver_list)}\r\nCC: {','.join(CC_list)}\r\nSubject: {Subject}\r\n"
        mail_content += "Content-Type: text/plain\r\n" 
        mail_content += f"{mail_body}\r\n"  # Kết thúc nội dung email và thêm dấu chấm trên dòng mới  
        
    #Gửi file
    server_response = Client_Socket.send(mail_content.encode())
    print("Email send response: ", server_response)
    Client_Socket.send(f'.\r\n'.encode())

    server_response = Client_Socket.recv(1024).decode()
    print("Email send response: ", server_response)
    Client_Socket.send('QUIT\r\n'.encode())
    Client_Socket.close()
    print("Gửi mail thành công!")
  
def Files_Folder(folder_path):
    file_paths = []  
    for root,_, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_paths.append(file_path)

    return file_paths

def Main_Content(mail_content):
    lines = mail_content.split('\n')
    main_content = '\n---------------------------------------------------\n'
    for line in lines:
        if 'Content-Type: application' in line:
            break       
        elif '+OK' in line:
            main_content += ''
        elif 'Content-Type' in line:
            main_content += ''
        elif '------=_Part_Boundary_YuSato' in line:
            main_content += ''
        elif not line.strip():
            main_content += ''
        elif "Subject" in line:
            main_content += line + '\n---------------------------------------------------\n'
        else:
            main_content += line + '\n'
    return main_content + '\n---------------------------------------------------\n'

def Read_Mail(Client_Socket,key, checkmail, mail_index):
    data = Load_Config()
    folder_path = data['Filter'][checkmail]
    Files = Files_Folder(folder_path)

    for file in Files:
        with open(file, 'r') as f:
            mail_content = f.read()

        sender = Find_Sender_FromFILE(mail_content)
        subject = Find_Subject_FromFILE(mail_content)
        state = 'attachment' if Find_MailType(mail_content) else 'no attachment'
        email = f"<{sender}><{subject}><{state}>"
        if not email in data[f'{key}'][mail_index]:
            continue
        else:
            main_content = Main_Content(mail_content)
            print(main_content)

            # Đánh dấu là đã đọc
            data[f'{key}'][mail_index] = email
            Write_Config(data)

            if state == 'attachment':
                save_demand = input('Trong email này có attached file, bạn có muốn save không(1: có - 0: không): ')
                if save_demand == '1':
                    path = input('Cho biết đường dẫn bạn muốn lưu: ')
                    receiver = Find_Receiver(mail_content)
                    filename = os.path.basename(file)
                    match = re.search(r'email_(\d+\.msg)\.txt', filename)
                    if match:
                        uidl = match.group(1)
                        Save_file(Client_Socket, receiver, '', True, path, uidl)
                        return
                        
def Print_MailList(Client_Socket, key,checkmail, mail_index):
    data = Load_Config()
    # In danh sách email
    emails = data.get(key, [])
    for index, mail in enumerate(emails, start=1):
        print(f'{index}. {mail}')

    try:
        mail_index = input('Bạn muốn đọc Email thứ mấy (hoặc nhấn enter để thoát ra ngoài, hoặc nhấn 0 để xem lại danh sách email): ')
        while mail_index == '0':
            for index, mail in enumerate(emails, start=1):
                print(f'{index}. {mail}')
            mail_index = input('Bạn muốn đọc Email thứ mấy (hoặc nhấn enter để thoát ra ngoài, hoặc nhấn 0 để xem lại danh sách email): ')

        if mail_index:
            while 0 >= int(mail_index) or int(mail_index) > len(emails):
                print("Chỉ số email không hợp lệ.")
                mail_index = input('Bạn muốn đọc Email thứ mấy (hoặc nhấn enter để thoát ra ngoài, hoặc nhấn 0 để xem lại danh sách email): ')
            Read_Mail(Client_Socket, key, int(checkmail)-1, int(mail_index)-1)
        else:
            return  # Thoát khỏi hàm nếu người dùng nhấn Enter
    except ValueError:
        print("Vui lòng nhập một số hợp lệ.")     

