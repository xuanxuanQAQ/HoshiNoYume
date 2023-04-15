import socket
import subprocess

def socket_init():
    host = '127.0.0.1'
    port = 12345

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)

    print(f"服务端socket地址 {host}:{port}")
    global conn
    conn, addr = server_socket.accept()
    
    print(f"连接到了Live2D客户端: {addr}")
    

def socket_send(message):
    conn.send(message.to_bytes(4, 'big', signed=True))
    
def socket_close():
    conn.close()
    
def live2d_open():
    exe_path = "live2d/Live2D.exe"
    subprocess.Popen(exe_path)