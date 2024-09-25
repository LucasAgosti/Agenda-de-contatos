# Agenda-de-contatos-compartilhada
 
# Sistema de uma agenda de contatos compartilhada entre usuários

Este projeto implementa uma Agenda de Contatos Compartilhada Distribuída tolerante a falhas, utilizando Python e comunicação por Sockets. O sistema consiste em vários servidores (agendas) e clientes, onde os clientes podem se conectar a um servidor para realizar operações como:

## Funcionalidades

- **Arquitetura distribuída**: O sistema conta com múltiplas agendas distribuídas que se comunicam para manter a consistência dos dados.
- **Tolerância a falhas**: Se uma agenda ficar offline e voltar a se conectar, ela se atualiza automaticamente com as mudanças feitas em outras agendas.
- **Sincronização de dados**: Qualquer alteração feita em uma agenda é propagada para as demais.
- **Operações de cliente**:
    Adicionar contatos.
    Remover contatos.
    Atualizar contatos.
    Visualizar todos os contatos.

## Estrutura do projeto

O projeto está dividido em servidores e clientes:

- Servidores: Cada servidor (agenda) escuta em duas portas:

- Porta de Cliente: Usada para operações de clientes.
- Porta de Sincronização: Usada para sincronizar dados com outros servidores.
- Clientes: Clientes se conectam a um dos servidores para realizar as operações de gerenciamento de contatos.

## Requisitos

- Python 3.x
- Bibliotecas Python:
  - `socket`
  - `threading`
  - `pickle`
  - `tkinter`
 
## Arquitetura

O sistema é baseado em uma arquitetura cliente-servidor distribuída, com três instâncias de agenda (servidores) que se comunicam para manter os dados consistentes. Cada servidor possui uma porta para interação com clientes e outra porta para sincronização de dados com outros servidores.

### Comunicação

**Cliente -> Servidor**: O cliente realiza operações de CRUD (Criar, Ler, Atualizar, Deletar) em um servidor.
**Servidor -> Servidor**: Os servidores sincronizam as operações realizadas para manter a consistência entre as agendas.


## Instalação e uso

### 1. Clonar o Repositório

git clone https://github.com/LucasAgosti/Agenda-de-contatos.git
cd Agenda-de-contatos (ou local do arquivo)

### 2. Executar servidor

python3 agenda1.py --host XX.XXX.X.XX --port YYYY --sync_port ZZZZ --other_servers XX.XXX.X.XX:YYYZ XX.XXX.X.XX:YYYX

exemplo de execução das 3 agendas:

python3 agenda1.py --host 190.172.0.99 --port 9010 --sync_port 9005 --other_servers 190.172.0.99:9006 190.172.0.99:9007

python3 agenda2.py --host 190.172.0.99 --port 9011 --sync_port 9006 --other_servers 190.172.0.99:9005 190.172.0.99:9007

python3 agenda3.py --host 190.172.0.99 --port 9012 --sync_port 9007 --other_servers 190.172.0.99:9005 190.172.0.99:9006

- (ou agenda2.py/agenda3.py, uma para cada agenda)
- host: seu endereço de IP
- port: uma porta para o cliente
- sync_port: uma porta de sincronização para o servidor se conectar a outro

### 3. Executar instância(s) do(s) cliente(s)

python3 client.py
(para cada instância)

Ao executar o cliente, você será solicitado a fornecer o IP e a porta do servidor ao qual deseja se conectar.

Exemplo de Interação:
O cliente escolhe o IP e porta do servidor:

IP: 192.168.0.11
Porta: 9010
O cliente pode então realizar as seguintes operações:

Visualizar contatos: Lista todos os contatos na agenda.
Adicionar contato: Insere um novo contato com nome e número de telefone.
Remover contato: Remove um contato existente.
Atualizar contato: Atualiza o número de telefone de um contato existente.

**Exemplo de Sincronização**:
- O cliente se conecta ao agenda1 e adiciona um contato.
- O agenda1 propaga essa adição para os outros servidores (agenda2 e agenda3).
- Se a agenda2 estiver offline no momento da adição, quando ela voltar a ficar online, ele buscará as atualizações dos outros servidores para se sincronizar.

