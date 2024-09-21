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
def sync_with_other_servers(action, name, phone=None):
    update = (action, name, phone)
    for server in servers:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(server)
                s.sendall(pickle.dumps(update))
                print(f"Sincronizando {action} para {server}: Nome={name}, Telefone={phone}")
        except ConnectionRefusedError:
            print(f"Servidor {server} está offline. Não foi possível sincronizar.")


# Função para receber e aplicar atualizações de outros servidores
def handle_server_sync(conn):
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break

            # Deserializa a atualização recebida de outro servidor
            action, name, phone = pickle.loads(data)

            if action == 'add':
                if name not in contacts:
                    contacts[name] = phone
                    print(f"[Sincronizado] Adicionando contato de outro servidor: Nome={name}, Telefone={phone}")

            elif action == 'remove':
                if name in contacts:
                    del contacts[name]
                    print(f"[Sincronizado] Removendo contato de outro servidor: Nome={name}")

            elif action == 'update':
                if name in contacts:
                    contacts[name] = phone
                    print(f"[Sincronizado] Atualizando contato de outro servidor: Nome={name}, Novo Telefone={phone}")
    except ConnectionResetError:
        print("Conexão com outro servidor foi perdida.")
    finally:
        conn.close()


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
                    sync_with_other_servers('add', name, phone)
                else:
                    response = f"Erro: Contato com o nome '{name}' já existe."
                    print(f"[{addr}] Tentativa de adicionar contato duplicado: Nome={name}")

            elif action == 'remove':
                if name in contacts:
                    del contacts[name]
                    response = f"Contato {name} removido com sucesso!"
                    print(f"[{addr}] Removendo contato: Nome={name}")
                    # Sincroniza com as outras agendas
                    sync_with_other_servers('remove', name)
                else:
                    response = "Erro: Contato não encontrado."
                    print(f"[{addr}] Tentativa de remover contato não existente: Nome={name}")

            elif action == 'update':
                if name in contacts:
                    contacts[name] = phone
                    response = f"Contato {name} atualizado com sucesso!"
                    print(f"[{addr}] Atualizando contato: Nome={name}, Novo Telefone={phone}")
                    # Sincroniza com as outras agendas
                    sync_with_other_servers('update', name, phone)
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


# Função para iniciar o servidor cliente
def start_client_server(host, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Permite reutilizar a mesma porta imediatamente após o encerramento
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Vincula o servidor ao host e porta fornecidos
    client_socket.bind((host, port))
    client_socket.listen()

    print(f"Servidor cliente escutando em {host}:{port}...")

    # Captura os sinais de interrupção para encerrar o servidor corretamente
    signal.signal(signal.SIGINT, lambda sig, frame: shutdown_server(client_socket))
    signal.signal(signal.SIGTERM, lambda sig, frame: shutdown_server(client_socket))

    try:
        while True:
            conn, addr = client_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()

    except Exception as e:
        print(f"Erro no servidor de clientes: {e}")

    finally:
        # Encerra o socket ao finalizar o programa
        shutdown_server(client_socket)


# Função para iniciar o servidor de sincronização
def start_sync_server(sync_port):
    sync_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Permite reutilizar a mesma porta imediatamente após o encerramento
    sync_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Vincula o servidor de sincronização à porta específica
    sync_socket.bind(('0.0.0.0', sync_port))
    sync_socket.listen()

    print(f"Servidor de sincronização escutando na porta {sync_port}...")

    try:
        while True:
            conn, addr = sync_socket.accept()
            sync_thread = threading.Thread(target=handle_server_sync, args=(conn,))
            sync_thread.start()

    except Exception as e:
        print(f"Erro no servidor de sincronização: {e}")

    finally:
        # Encerra o socket de sincronização
        sync_socket.close()


if __name__ == "__main__":
    # Configuração para aceitar argumentos de IP e porta via linha de comando
    parser = argparse.ArgumentParser(description="Servidor de Agenda Distribuída")
    parser.add_argument('--host', type=str, required=True, help='IP do servidor')
    parser.add_argument('--port', type=int, required=True, help='Porta do servidor')
    parser.add_argument('--sync_port', type=int, required=True, help='Porta para sincronização entre servidores')
    parser.add_argument('--other_servers', nargs='*', help='Outros servidores no formato IP:SYNC_PORT')

    args = parser.parse_args()

    # Carrega a lista de outros servidores fornecidos pelo usuário
    if args.other_servers:
        for server in args.other_servers:
            ip, port = server.split(":")
            servers.append((ip, int(port)))

    # Inicializa os servidores para clientes e sincronização
    threading.Thread(target=start_sync_server, args=(args.sync_port,), daemon=True).start()
    start_client_server(args.host, args.port)
