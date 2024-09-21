import socket
import threading
import pickle
import sys

# Lista de contatos da agenda
contacts = {}

# Lista de servidores (excluindo o próprio)
servers = [("localhost", 9002), ("localhost", 9003)]


# Função para sincronizar as alterações com outras agendas
def sync_with_other_servers(contact_list):
    for server in servers:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(server)
                s.sendall(pickle.dumps(contact_list))
        except ConnectionRefusedError:
            print(f"Servidor {server} está offline, tentando outro...")


# Função para lidar com os clientes
def handle_client(conn, addr):
    print(f"Conexão estabelecida com {addr}")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break

            # Deserializa os dados recebidos do cliente
            action, name, phone = pickle.loads(data)

            if action == 'add':
                if name not in contacts:
                    contacts[name] = phone
                    response = f"Contato {name} adicionado com sucesso!"
                    print(f"[{addr}] Adicionando contato: Nome={name}, Telefone={phone}")
                    # Sincroniza com as outras agendas
                    sync_with_other_servers(contacts)
                else:
                    response = f"Erro: Contato com o nome '{name}' já existe."
                    print(f"[{addr}] Tentativa de adicionar contato duplicado: Nome={name}")

            elif action == 'remove':
                if name in contacts:
                    del contacts[name]
                    response = f"Contato {name} removido com sucesso!"
                    print(f"[{addr}] Removendo contato: Nome={name}")
                    # Sincroniza com as outras agendas
                    sync_with_other_servers(contacts)
                else:
                    response = "Erro: Contato não encontrado."
                    print(f"[{addr}] Tentativa de remover contato não existente: Nome={name}")

            elif action == 'update':
                if name in contacts:
                    contacts[name] = phone
                    response = f"Contato {name} atualizado com sucesso!"
                    print(f"[{addr}] Atualizando contato: Nome={name}, Novo Telefone={phone}")
                    # Sincroniza com as outras agendas
                    sync_with_other_servers(contacts)
                else:
                    response = "Erro: Contato não encontrado."
                    print(f"[{addr}] Tentativa de atualizar contato não existente: Nome={name}")

            elif action == 'view':
                response = contacts if contacts else "Agenda vazia."
                print(f"[{addr}] Visualizando contatos.")

            # Envia a resposta de volta para o cliente
            conn.sendall(pickle.dumps(response))

    except ConnectionResetError:
        print(f"Conexão com {addr} perdida.")

    finally:
        # Fecha a conexão e informa que o cliente se desconectou
        print(f"Cliente {addr} desconectado.")
        conn.close()


def start_server(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen()
        print(f"Servidor escutando em {host}:{port}...")

        while True:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python server.py <porta>")
        sys.exit(1)

    port = int(sys.argv[1])

    # Modifique a lista de servidores para excluir a própria instância do servidor
    servers = [("localhost", p) for p in [9001, 9002, 9003] if p != port]

    # Inicializa o servidor em localhost na porta especificada
    start_server("localhost", port)
