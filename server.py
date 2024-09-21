import socket
import threading
import pickle
import sys
import argparse
import signal

# Lista de contatos da agenda
contacts = {}

# Lista de servidores (excluindo o próprio)
servers = []


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


# Função que encerra o servidor de forma segura
def shutdown_server(server_socket):
    print("Encerrando o servidor...")
    server_socket.close()
    sys.exit(0)


# Função para iniciar o servidor
def start_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Permite reutilizar a mesma porta imediatamente após o encerramento
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Vincula o servidor ao host e porta fornecidos
    server_socket.bind((host, port))
    server_socket.listen()

    print(f"Servidor escutando em {host}:{port}...")

    # Captura os sinais de interrupção para encerrar o servidor corretamente
    signal.signal(signal.SIGINT, lambda sig, frame: shutdown_server(server_socket))
    signal.signal(signal.SIGTERM, lambda sig, frame: shutdown_server(server_socket))

    try:
        while True:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()

    except Exception as e:
        print(f"Erro no servidor: {e}")

    finally:
        # Encerra o socket ao finalizar o programa
        shutdown_server(server_socket)


if __name__ == "__main__":
    # Configuração para aceitar argumentos de IP e porta via linha de comando
    parser = argparse.ArgumentParser(description="Servidor de Agenda Distribuída")
    parser.add_argument('--host', type=str, required=True, help='IP do servidor')
    parser.add_argument('--port', type=int, required=True, help='Porta do servidor')
    parser.add_argument('--other_servers', nargs='*', help='Outros servidores no formato IP:PORTA')

    args = parser.parse_args()

    # Carrega a lista de outros servidores fornecidos pelo usuário
    if args.other_servers:
        for server in args.other_servers:
            ip, port = server.split(":")
            servers.append((ip, int(port)))

    # Inicializa o servidor com o IP e porta fornecidos pelo usuário
    start_server(args.host, args.port)
