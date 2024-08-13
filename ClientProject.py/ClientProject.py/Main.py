from Handle_File import *
import socket
from POP3_Function import *
from JSON_Function import Load_Config
from JSON_Function import Write_Config
from re import *

is_running = True
serverPort = 465 
SMTP_server = "127.0.0.1"
Client_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
Client_Socket = socket.create_connection((SMTP_server, serverPort))


def Load_Mail_Config(Client_Socket):
    USER = JSON_Function.Load_Config()
    Time = USER['Autoload']
    for user in USER['Receiver']:
        password = ''
        Save_Mail_AutoMode(Client_Socket, user, password)
    if is_running:
        threading.Timer(Time, Load_Mail_Config, args=(Client_Socket,)).start()

Load_Mail_Config(Client_Socket)


#   MENU
user_demand = '1'
while user_demand != '0':
    print('\t<Mail Menu>:\n\t1. Để gửi email\n\t2. Để xem danh sách các email đã nhận\n\t3. Kết thúc chương trình')
    user_demand = input('Bạn chọn: ')
    if user_demand == '1':     
            #Các lệnh SMTP thường được kết thúc bằng ký tự xuống dòng và ký tự nguồn cấp dòng \r\n.
            #Điều này báo hiệu sự kết thúc của lệnh tới máy chủ SMTP.
            Client_Socket = socket.create_connection((SMTP_server, serverPort))
            server_response = Client_Socket.recv(1024).decode()
            print("Server response: ", server_response)
    
            Client_Socket.send(f'EHLO mydomain.com\r\n'.encode())
            server_response = Client_Socket.recv(1024).decode()
            print("EHLO response: ", server_response)

            #From
            sender_mail = input('Your email: ')
        
            #Đưa địa chỉ người gửi vào file config
            data = Load_Config()
            if not sender_mail in data.get('Sender',[]):
                data['Sender'].append(sender_mail)

            #To
            receiver_input = input('To (Các địa chỉ ngăn cách nhau bởi dấu ,): ')
            receiver_list = [email.strip()
                             for email in receiver_input.split(',')] if receiver_input else []
            #Đưa địa chỉ người nhận vào file config
            for receiver in receiver_list:
                if not receiver in data.get('Receiver',[]):
                    data['Receiver'].append(receiver)
        
            #CC
            CC_input = input('CC (Các địa chỉ ngăn cách nhau bởi dấu ,): ')
            CC_list = [email.strip()
                       for email in CC_input.split(',')] if CC_input else []
            #Đưa địa chỉ người nhận vào file config
            for receiver in CC_list:
                if not receiver in data.get('Receiver',[]):
                    data['Receiver'].append(receiver)
                   
            #BCC
            BCC_input = input('BCC (Các địa chỉ ngăn cách nhau bởi dấu ,): ')
            BCC_list = [email.strip()
                        for email in BCC_input.split(',')] if BCC_input else []
            #Đưa địa chỉ người nhận vào file config
            for receiver in BCC_list:
                if not receiver in data.get('Receiver',[]):
                    data['Receiver'].append(receiver)
            #Viết vào file    
            Write_Config(data)
            
            Subject = input('Subject: ')
            
            print("Nhập văn bản (nhập 'END' để kết thúc): ")
            lines = []
            while True:
                line = input()
                if line == 'END':
                    break
                lines.append(line)
            mail_body = '\n'.join(lines)
    
            file_demand = input("Có gửi kèm file (1. có, 0. không): ") 
            File_list = []
            if file_demand == '1' :
                file_number = int(input("Số file muốn gửi: "))
                file = 0
                while file != file_number:
                    File_path = input(f'Đường dẫn file {file+1}: ')
                    if os.path.exists(File_path):
                        file += 1
                        File_list.append(File_path)
                    else:
                        print("Đường dẫn không hợp lệ")
                SEND_EMAIL_FILE(Client_Socket, sender_mail, receiver_list, CC_list, BCC_list, Subject, mail_body, File_list)

            else:
                SEND_EMAIL_FILE(Client_Socket, sender_mail, receiver_list, CC_list, BCC_list, Subject, mail_body, File_list)


    if user_demand == '2':
        data = Load_Config()
        
        checkmail = 1
        while checkmail != 0:
            print('\tĐây là danh sách các folder trong mailbox của bạn:')
            print('\t1. Inbox\n\t2. Work\n\t3. Project\n\t4. Important\n\t5. Spam')
            checkmail = input('Bạn muốn xem email trong folder nào (Nhấn 0 để thoát ra ngoài): ')
            key = ''
            mail_index = 0
            if checkmail == '0' or checkmail == '':
               break
            if checkmail == '1':
                key = 'Inbox'
                Print_MailList(Client_Socket, key,checkmail,mail_index)
            elif checkmail == '2':
                key = 'Work'
                Print_MailList(Client_Socket, key,checkmail,mail_index)
            elif checkmail == '3':
                key = 'Project'
                Print_MailList(Client_Socket, key,checkmail,mail_index)
            elif checkmail == '4':
                key = 'Important'
                Print_MailList(Client_Socket, key,checkmail,mail_index)
            elif checkmail == '5':
                key = 'Spam'
                Print_MailList(Client_Socket, key,checkmail,mail_index)
            else:
                print('Vui lòng nhập một số hợp lệ.')

    if user_demand == '3':
       print('Kết thúc chương trình')
       is_running = False
       break

