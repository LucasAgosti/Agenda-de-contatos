import socket
import pickle

# Lista de servidores (agendas)
servers = [("localhost", 9000), ("localhost", 9002), ("localhost", 9003)]


# Função para tentar conectar a um dos servidores
def connect_to_server():
    for server in servers:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(server)
            print(f"Conectado ao servidor {server}")
            return s
        except ConnectionRefusedError:
            print(f"Servidor {server} offline. Tentando outro...")

    print("Nenhum servidor disponível.")
    return None


def send_request(server_socket, action, name=None, phone=None):
    request = (action, name, phone)
    server_socket.sendall(pickle.dumps(request))
    response = pickle.loads(server_socket.recv(1024))
    print(response)


def client_program():
    server_socket = connect_to_server()
    if not server_socket:
        return

    while True:
        print("\nEscolha uma ação: add, remove, update, view ou quit")
        action = input("Ação: ")

        if action == 'quit':
            server_socket.close()
            break

        if action in ['add', 'update']:
            name = input("Nome do contato: ")
            phone = input("Telefone: ")
            send_request(server_socket, action, name, phone)

        elif action == 'remove':
            name = input("Nome do contato: ")
            send_request(server_socket, action, name)

        elif action == 'view':
            send_request(server_socket, action)

        else:
            print("Ação inválida, tente novamente.")


if __name__ == "__main__":
    client_program()
