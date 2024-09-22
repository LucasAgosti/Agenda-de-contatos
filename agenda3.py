import socket
import threading
import pickle
import sys
import argparse
import signal
import time

# Lista de contatos da agenda
contacts = {}

# Função para sincronizar as alterações com outras agendas
def sync_with_other_servers(action, name, phone=None, servers=[]):
    update = (action, name, phone)
    for server in servers:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(server)
                s.sendall(pickle.dumps(update))
                print(f"Sincronizando {action} para {server}: Nome={name}, Telefone={phone}")
        except ConnectionRefusedError:
            print(f"Servidor {server} está offline. Não foi possível sincronizar.")

# Função para receber atualizações de outros servidores
def handle_server_sync(conn):
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break

            action, name, phone = pickle.loads(data)
            if action == 'add':
                contacts[name] = phone
                print(f"Adicionando contato de outro servidor: {name} - {phone}")
            elif action == 'remove':
                contacts.pop(name, None)
                print(f"Removendo contato de outro servidor: {name}")
            elif action == 'update':
                contacts[name] = phone
                print(f"Atualizando contato de outro servidor: {name} - {phone}")
            elif action == 'fetch_data':
                conn.sendall(pickle.dumps(contacts))  # Envia a cópia completa da agenda
    except ConnectionResetError:
        print("Conexão com outro servidor foi perdida.")
    finally:
        conn.close()

# Função para lidar com os clientes
def handle_client(conn, addr, servers):
    print(f"Conexão estabelecida com {addr}")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break

            action, name, phone = pickle.loads(data)

            if action == 'add':
                if name not in contacts:
                    contacts[name] = phone
                    print(f"Adicionando contato: {name} - {phone}")
                    sync_with_other_servers('add', name, phone, servers)
                    response = f"Contato {name} adicionado com sucesso!"
                else:
                    response = f"Erro: Contato {name} já existe."
            elif action == 'remove':
                if name in contacts:
                    del contacts[name]
                    print(f"Removendo contato: {name}")
                    sync_with_other_servers('remove', name, servers=servers)
                    response = f"Contato {name} removido com sucesso!"
                else:
                    response = f"Erro: Contato {name} não encontrado."
            elif action == 'update':
                if name in contacts:
                    contacts[name] = phone
                    print(f"Atualizando contato: {name} - {phone}")
                    sync_with_other_servers('update', name, phone, servers=servers)
                    response = f"Contato {name} atualizado com sucesso!"
                else:
                    response = f"Erro: Contato {name} não encontrado."
            elif action == 'view':
                response = contacts if contacts else "Agenda vazia."

            conn.sendall(pickle.dumps(response))
    except ConnectionResetError:
        print(f"Conexão com {addr} perdida.")
    finally:
        print(f"Cliente {addr} desconectado.")
        conn.close()

# Função para sincronizar dados ao iniciar se a agenda estava offline
def fetch_data_from_other_servers(servers):
    print("Sincronizando dados ao iniciar...")
    for server in servers:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(server)
                s.sendall(pickle.dumps(('fetch_data', None, None)))
                data = pickle.loads(s.recv(1024))
                contacts.update(data)
                print(f"Sincronização inicial com {server} completa.")
                break  # Conecta e sincroniza de apenas um servidor ativo
        except ConnectionRefusedError:
            print(f"Servidor {server} não está disponível para sincronização inicial.")

# Função para iniciar o servidor de sincronização
def start_sync_server(sync_port):
    sync_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sync_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
        sync_socket.close()

# Função para iniciar o servidor para clientes
def start_client_server(host, port, servers):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_socket.bind((host, port))
    client_socket.listen()

    print(f"Servidor cliente escutando em {host}:{port}...")

    try:
        while True:
            conn, addr = client_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr, servers))
            client_thread.start()
    except Exception as e:
        print(f"Erro no servidor de clientes: {e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Servidor de Agenda Distribuída")
    parser.add_argument('--host', type=str, required=True, help='IP do servidor')
    parser.add_argument('--port', type=int, required=True, help='Porta do servidor para clientes')
    parser.add_argument('--sync_port', type=int, required=True, help='Porta para sincronização entre servidores')
    parser.add_argument('--other_servers', nargs='*', help='Outros servidores no formato IP:SYNC_PORT')

    args = parser.parse_args()

    # Carrega a lista de outros servidores fornecidos pelo usuário
    servers = []
    if args.other_servers:
        for server in args.other_servers:
            ip, port = server.split(":")
            servers.append((ip, int(port)))

    # Sincroniza com os outros servidores ao iniciar (caso estivesse offline)
    fetch_data_from_other_servers(servers)

    # Inicializa os servidores de clientes e sincronização
    threading.Thread(target=start_sync_server, args=(args.sync_port,), daemon=True).start()
    start_client_server(args.host, args.port, servers)
