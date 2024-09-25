# -----------------------------------------------------------------------------
# Copyright 2024 Lucas Fernandes
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# -----------------------------------------------------------------------------


import socket
import pickle
import tkinter as tk
from tkinter import messagebox, simpledialog
import argparse

# Função para conectar ao servidor escolhido pelo cliente
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

        self.contacts_list = tk.Listbox(self.root, height=10, width=50)
        self.contacts_list.grid(row=0, column=0, columnspan=3)

        self.view_button = tk.Button(self.root, text="Visualizar Contatos", command=self.view_contacts)
        self.view_button.grid(row=1, column=0)

        self.add_button = tk.Button(self.root, text="Adicionar Contato", command=self.add_contact)
        self.add_button.grid(row=1, column=1)

        self.remove_button = tk.Button(self.root, text="Remover Contato", command=self.remove_contact)
        self.remove_button.grid(row=1, column=2)

        self.name_label = tk.Label(self.root, text="Nome")
        self.name_label.grid(row=2, column=0)

        self.name_entry = tk.Entry(self.root)
        self.name_entry.grid(row=2, column=1)

        self.phone_label = tk.Label(self.root, text="Telefone")
        self.phone_label.grid(row=3, column=0)

        self.phone_entry = tk.Entry(self.root)
        self.phone_entry.grid(row=3, column=1)

        self.update_button = tk.Button(self.root, text="Atualizar Contato", command=self.update_contact)
        self.update_button.grid(row=4, column=0, columnspan=2)

    def view_contacts(self):
        response = send_request(self.server_socket, 'view')
        self.contacts_list.delete(0, tk.END)  # Limpa a lista atual

        if isinstance(response, dict):
            for name, phone in response.items():
                self.contacts_list.insert(tk.END, f"{name}: {phone}")
        else:
            show_error_message(response)

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
def main():
    root = tk.Tk()

    # Solicitar o IP e a porta do servidor
    host = simpledialog.askstring("Conexão", "Digite o IP do servidor:")
    port = simpledialog.askinteger("Conexão", "Digite a porta do servidor:")

    if not host or not port:
        show_error_message("IP ou porta inválidos. Encerrando o programa.")
        root.quit()
        return

    # Tenta conectar ao servidor fornecido pelo usuário
    server_socket = connect_to_server(host, port)
    if not server_socket:
        show_error_message("Servidor offline ou não disponível.")
        root.quit()
        return

    app = ContactApp(root, server_socket)
    root.mainloop()

if __name__ == "__main__":
    main()
