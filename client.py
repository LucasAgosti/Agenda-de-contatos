import socket
import pickle
import tkinter as tk
from tkinter import messagebox, simpledialog
import argparse

# Função para conectar ao servidor
def connect_to_server(host, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        print(f"Conectado ao servidor {host}:{port}")
        return s
    except ConnectionRefusedError:
        print(f"Servidor {host}:{port} offline.")
        return None

# Função para enviar requisições ao servidor
def send_request(server_socket, action, name=None, phone=None):
    request = (action, name, phone)
    server_socket.sendall(pickle.dumps(request))
    response = pickle.loads(server_socket.recv(1024))
    return response

# Função para exibir uma mensagem de erro
def show_error_message(msg):
    messagebox.showerror("Erro", msg)

# Classe principal da GUI
class ContactApp:
    def __init__(self, root, server_socket):
        self.root = root
        self.server_socket = server_socket
        self.root.title("Agenda de Contatos")

        # Lista de contatos (usada no Listbox)
        self.contacts_list = tk.Listbox(self.root, height=10, width=50)
        self.contacts_list.grid(row=0, column=0, columnspan=3)

        # Botão para visualizar os contatos
        self.view_button = tk.Button(self.root, text="Visualizar Contatos", command=self.view_contacts)
        self.view_button.grid(row=1, column=0)

        # Botão para adicionar um novo contato
        self.add_button = tk.Button(self.root, text="Adicionar Contato", command=self.add_contact)
        self.add_button.grid(row=1, column=1)

        # Botão para remover um contato
        self.remove_button = tk.Button(self.root, text="Remover Contato", command=self.remove_contact)
        self.remove_button.grid(row=1, column=2)

        # Campos de entrada para adicionar ou atualizar contatos
        self.name_label = tk.Label(self.root, text="Nome")
        self.name_label.grid(row=2, column=0)

        self.name_entry = tk.Entry(self.root)
        self.name_entry.grid(row=2, column=1)

        self.phone_label = tk.Label(self.root, text="Telefone")
        self.phone_label.grid(row=3, column=0)

        self.phone_entry = tk.Entry(self.root)
        self.phone_entry.grid(row=3, column=1)

        # Botão para atualizar um contato
        self.update_button = tk.Button(self.root, text="Atualizar Contato", command=self.update_contact)
        self.update_button.grid(row=4, column=0, columnspan=2)

    # Função para visualizar os contatos
    def view_contacts(self):
        response = send_request(self.server_socket, 'view')
        self.contacts_list.delete(0, tk.END)  # Limpa a lista atual

        if isinstance(response, dict):
            for name, phone in response.items():
                self.contacts_list.insert(tk.END, f"{name}: {phone}")
        else:
            show_error_message(response)

    # Função para adicionar um novo contato
    def add_contact(self):
        name = self.name_entry.get()
        phone = self.phone_entry.get()

        if not name or not phone:
            show_error_message("Nome e Telefone são obrigatórios!")
            return

        response = send_request(self.server_socket, 'add', name, phone)
        if "sucesso" in response:
            self.view_contacts()  # Atualiza a lista de contatos
        else:
            show_error_message(response)

    # Função para remover um contato selecionado
    def remove_contact(self):
        selected = self.contacts_list.curselection()
        if selected:
            contact = self.contacts_list.get(selected[0])
            name = contact.split(":")[0]

            response = send_request(self.server_socket, 'remove', name)
            if "sucesso" in response:
                self.view_contacts()  # Atualiza a lista de contatos
            else:
                show_error_message(response)
        else:
            show_error_message("Selecione um contato para remover.")

    # Função para atualizar um contato
    def update_contact(self):
        name = self.name_entry.get()
        phone = self.phone_entry.get()

        if not name or not phone:
            show_error_message("Nome e Telefone são obrigatórios!")
            return

        response = send_request(self.server_socket, 'update', name, phone)
        if "sucesso" in response:
            self.view_contacts()  # Atualiza a lista de contatos
        else:
            show_error_message(response)

# Função principal para iniciar o programa
def main(host, port):
    server_socket = connect_to_server(host, port)
    if not server_socket:
        return

    root = tk.Tk()
    app = ContactApp(root, server_socket)
    root.mainloop()

if __name__ == "__main__":
    # Configuração para aceitar argumentos de IP e porta via linha de comando
    parser = argparse.ArgumentParser(description="Cliente de Agenda com Interface Gráfica")
    parser.add_argument('--host', type=str, required=True, help='IP do servidor')
    parser.add_argument('--port', type=int, required=True, help='Porta do servidor')

    args = parser.parse_args()

    # Inicializa o cliente com o IP e porta fornecidos
    main(args.host, args.port)
