import redis
import pymongo
import json
from pymongo.server_api import ServerApi
from datetime import datetime, timedelta
from pymongo.mongo_client import MongoClient

import crud_usuario
import crud_produto
import crud_vendedor
import crud_compras
import crud_favoritos

# Conexão com o Redis
r = redis.Redis(
    host='redis-17733.c11.us-east-1-2.ec2.redns.redis-cloud.com',
    port=17733,
    password='FX4HKWXiS1lTASjrm1SE7nWKhqJtW55s'
)

# Substitua '<password>' pela sua senha real.
uri = "mongodb+srv://silmara:<password>@cluster0.05p7qyc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.mercadolivre

# Função de Login Temporário
def login(user_id):
    session_id = f"session_{user_id}"
    session_data = {
        "user_id": user_id,
        "login_time": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(minutes=30)).isoformat()
    }
    r.set(session_id, json.dumps(session_data), ex=1800)  # 30 minutos de expiração
    return session_id, session_data

def check_session(session_id):
    session_data = r.get(session_id)
    if session_data:
        session_data = json.loads(session_data)
        if datetime.fromisoformat(session_data['expires_at']) > datetime.now():
            return True
    return False

def user_login():
    while True:
        user_id = input("Digite seu ID de usuário: ")
        senha = input("Digite sua senha: ")  # Simplificação, considerar hash/sal na produção
        # Verifica usuário e senha no MongoDB
        user = db.Usuário.find_one({"_id": user_id, "senha": senha})  # Certifique-se de que a senha está armazenada
        if user:
            session_id, session_data = login(user_id)
            print("Login bem-sucedido!")
            return session_id, user_id
        else:
            print("Usuário ou senha incorretos. Tente novamente.")

def create_user():
    user_id = input("Digite seu ID de usuário: ")
    senha = input("Digite sua senha: ")  # Simplificação, considerar hash/sal na produção
    nome = input("Nome: ")
    sobrenome = input("Sobrenome: ")
    enderecos = []
    add_more = 'S'
    while add_more.upper() == 'S':
        rua = input("Rua: ")
        num = input("Número: ")
        bairro = input("Bairro: ")
        cidade = input("Cidade: ")
        estado = input("Estado: ")
        cep = input("CEP: ")
        endereco = {
            "rua": rua,
            "num": num,
            "bairro": bairro,
            "cidade": cidade,
            "estado": estado,
            "cep": cep
        }
        enderecos.append(endereco)
        add_more = input("Deseja adicionar outro endereço? (S/N) ")

    usuario = {
        "_id": user_id,
        "senha": senha,
        "nome": nome,
        "sobrenome": sobrenome,
        "enderecos": enderecos
    }
    db.Usuário.insert_one(usuario)
    print("Usuário criado com sucesso!")

# Menu Principal
key = 0
while key != 'S':
    print("Bem-vindo! Por favor, faça login ou crie uma nova conta.")
    print("1 - Criar nova conta")
    print("2 - Fazer login")
    key = input("Digite a opção desejada: ")

    if key == '1':
        create_user()
    elif key == '2':
        session_id, user_id = user_login()
        if session_id:
            key = 0  # Reset key to enter the main menu

            while key != 'S':
                if not check_session(session_id):
                    print("Sua sessão expirou. Por favor, faça login novamente.")
                    session_id, user_id = user_login()

                print("1 - CRUD Usuário")
                print("2 - CRUD Vendedor")
                print("3 - CRUD Produto")
                print("4 - Compras")
                print("5 - Favoritos")
                key = input("Digite a opção desejada? (S para sair) ")

                if key == '1':
                    print("Menu do Usuário")
                    print("1 - Criar Usuário")
                    print("2 - Visualizar Usuário")
                    print("3 - Atualizar Usuário")
                    print("4 - Deletar Usuário")
                    sub = input("Digite a opção desejada? (V para voltar) ")
                    if sub == '1':
                        crud_usuario.create_usuario()
                    elif sub == '2':
                        nomeUsuario = input("Visualizar usuário, deseja algum nome especifico? ")
                        crud_usuario.read_usuario(nomeUsuario)
                    elif sub == '3':
                        nomeUsuario = input("Atualizar usuário, deseja algum nome especifico? ")
                        crud_usuario.update_usuario(nomeUsuario)
                    elif sub == '4':
                        nomeUsuario = input("Nome a ser deletado: ")
                        sobrenome = input("Sobrenome a ser deletado: ")
                        crud_usuario.delete_usuario(nomeUsuario, sobrenome)

                elif key == '2':
                    print("Menu do Vendedor")
                    print("1 - Criar Vendedor")
                    print("2 - Ler Vendedor")
                    print("3 - Atualizar Vendedor")
                    print("4 - Deletar Vendedor")
                    sub = input("Digite a opção desejada? (V para voltar) ")
                    if sub == '1':
                        crud_vendedor.create_vendedor()
                    elif sub == '2':
                        nomeVendedor = input("Ler vendedor, deseja algum nome especifico? ")
                        crud_vendedor.read_vendedor(nomeVendedor)
                    elif sub == '3':
                        nomeVendedor = input("Atualizar vendedor, deseja algum nome especifico? ")
                        crud_vendedor.update_vendedor(nomeVendedor)
                    elif sub == '4':
                        nomeVendedor = input("Nome do vendedor a ser deletado: ")
                        cpfVendedor = input("CPF do vendedor a ser deletado: ")
                        crud_vendedor.delete_vendedor(nomeVendedor, cpfVendedor)

                elif key == '3':
                    print("Menu do Produto")
                    print("1 - Criar Produto")
                    print("2 - Ver Produto")
                    print("3 - Atualizar Produto")
                    print("4 - Deletar Produto")
                    sub = input("Digite a opção desejada? (V para voltar) ")
                    if sub == '1':
                        crud_produto.create_produto()
                    elif sub == '2':
                        nomeProduto = input("Visualizar produtos, deseja algum nome especifico? Caso não, pressione enter")
                        crud_produto.read_produto(nomeProduto)
                    elif sub == '3':
                        nomeProduto = input("Atualizar produtos, deseja algum nome especifico? ")
                        crud_produto.update_produto(nomeProduto)
                    elif sub == '4':
                        nomeProduto = input("Nome a ser deletado: ")
                        crud_produto.delete_produto(nomeProduto)

                elif key == '4':
                    print("Compras")
                    print("1 - Realizar compra")
                    print("2 - Ver compras realizadas")
                    sub = input("Digite a opção desejada? (V para voltar) ")
                    if sub == '1':
                        cpf_usuario = input("Digite o CPF do usuário: ")
                        carrinho_usuario = crud_compras.realizar_compra(cpf_usuario)
                    elif sub == '2':
                        cpf_usuario = input("Digite o CPF do usuário: ")
                        crud_compras.ver_compras_realizadas(cpf_usuario)

                elif key == '5':
                    print("Favoritos")
                    print("1 - Adicionar favoritos")
                    print("2 - Visualizar favoritos")
                    print("3 - Deletar favoritos")
                    sub = input("Digite a opção desejada? (V para voltar) ")
                    if sub == '1':
                        crud_favoritos.adicionarnovo_favorito()
                    elif sub == '2':
                        cpf_usuario = input("Digite o CPF do usuário: ")
                        crud_favoritos.visualizar_favoritos(cpf_usuario)
                    elif sub == '3':
                        cpf_usuario = input("Digite o CPF do usuário: ")
                        id_produto = input("Digite o ID do produto que deseja remover dos favoritos: ")
                        crud_favoritos.excluir_favorito(cpf_usuario, id_produto)
                else:
                    print("Opção inválida. Por favor, digite uma opção válida.")

print("Tchau, tchau! Volte sempre!")
import redis
import pymongo
import json
from pymongo.server_api import ServerApi
from datetime import datetime, timedelta
from pymongo.mongo_client import MongoClient

import crud_usuario
import crud_produto
import crud_vendedor
import crud_compras
import crud_favoritos

# Conexão com o Redis
r = redis.Redis(
    host='redis-17733.c11.us-east-1-2.ec2.redns.redis-cloud.com',
    port=17733,
    password='FX4HKWXiS1lTASjrm1SE7nWKhqJtW55s'
)

# Substitua '<password>' pela sua senha real.
client = pymongo.MongoClient(
    "mongodb+srv://silmara:123@cluster0.05p7qyc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0", 
    server_api=ServerApi('1')
)
db = client.mercadolivre

def login(user_id):
    session_id = f"session_{user_id}"
    session_data = {
        "user_id": user_id,
        "login_time": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(minutes=30)).isoformat()
    }
    r.set(session_id, json.dumps(session_data), ex=1800)  
    return session_id, session_data

def check_session(session_id):
    session_data = r.get(session_id)
    if session_data:
        session_data = json.loads(session_data)
        if datetime.fromisoformat(session_data['expires_at']) > datetime.now():
            return True
    return False

def user_login():
    while True:
        user_id = input("Digite seu ID de usuário: ")
        senha = input("Digite sua senha: ")  

        user = db.Usuário.find_one({"_id": user_id, "senha": senha})  
        if user:
            session_id, session_data = login(user_id)
            print("Login bem-sucedido!")
            return session_id, user_id
        else:
            print("Usuário ou senha incorretos. Tente novamente.")

def create_user():
    user_id = input("Digite seu ID de usuário: ")
    senha = input("Digite sua senha: ")  
    nome = input("Nome: ")
    sobrenome = input("Sobrenome: ")
    enderecos = []
    add_more = 'S'
    while add_more.upper() == 'S':
        rua = input("Rua: ")
        num = input("Número: ")
        bairro = input("Bairro: ")
        cidade = input("Cidade: ")
        estado = input("Estado: ")
        cep = input("CEP: ")
        endereco = {
            "rua": rua,
            "num": num,
            "bairro": bairro,
            "cidade": cidade,
            "estado": estado,
            "cep": cep
        }
        enderecos.append(endereco)
        add_more = input("Deseja adicionar outro endereço? (S/N) ")

    usuario = {
        "_id": user_id,
        "senha": senha,
        "nome": nome,
        "sobrenome": sobrenome,
        "enderecos": enderecos
    }
    db.Usuário.insert_one(usuario)
    print("Usuário criado com sucesso!")


key = 0
while key != 'S':
    print("Bem-vindo! Por favor, faça login ou crie uma nova conta.")
    print("1 - Criar nova conta")
    print("2 - Fazer login")
    key = input("Digite a opção desejada: ")

    if key == '1':
        create_user()
    elif key == '2':
        session_id, user_id = user_login()
        if session_id:
            key = 0  

            while key != 'S':
                if not check_session(session_id):
                    print("Sua sessão expirou. Por favor, faça login novamente.")
                    session_id, user_id = user_login()

                print("1 - CRUD Usuário")
                print("2 - CRUD Vendedor")
                print("3 - CRUD Produto")
                print("4 - Compras")
                print("5 - Favoritos")
                key = input("Digite a opção desejada? (S para sair) ")

                if key == '1':
                    print("Menu do Usuário")
                    print("1 - Criar Usuário")
                    print("2 - Visualizar Usuário")
                    print("3 - Atualizar Usuário")
                    print("4 - Deletar Usuário")
                    sub = input("Digite a opção desejada? (V para voltar) ")
                    if sub == '1':
                        crud_usuario.create_usuario()
                    elif sub == '2':
                        nomeUsuario = input("Visualizar usuário, deseja algum nome especifico? ")
                        crud_usuario.read_usuario(nomeUsuario)
                    elif sub == '3':
                        nomeUsuario = input("Atualizar usuário, deseja algum nome especifico? ")
                        crud_usuario.update_usuario(nomeUsuario)
                    elif sub == '4':
                        nomeUsuario = input("Nome a ser deletado: ")
                        sobrenome = input("Sobrenome a ser deletado: ")
                        crud_usuario.delete_usuario(nomeUsuario, sobrenome)

                elif key == '2':
                    print("Menu do Vendedor")
                    print("1 - Criar Vendedor")
                    print("2 - Ler Vendedor")
                    print("3 - Atualizar Vendedor")
                    print("4 - Deletar Vendedor")
                    sub = input("Digite a opção desejada? (V para voltar) ")
                    if sub == '1':
                        crud_vendedor.create_vendedor()
                    elif sub == '2':
                        nomeVendedor = input("Ler vendedor, deseja algum nome especifico? ")
                        crud_vendedor.read_vendedor(nomeVendedor)
                    elif sub == '3':
                        nomeVendedor = input("Atualizar vendedor, deseja algum nome especifico? ")
                        crud_vendedor.update_vendedor(nomeVendedor)
                    elif sub == '4':
                        nomeVendedor = input("Nome do vendedor a ser deletado: ")
                        cpfVendedor = input("CPF do vendedor a ser deletado: ")
                        crud_vendedor.delete_vendedor(nomeVendedor, cpfVendedor)

                elif key == '3':
                    print("Menu do Produto")
                    print("1 - Criar Produto")
                    print("2 - Ver Produto")
                    print("3 - Atualizar Produto")
                    print("4 - Deletar Produto")
                    sub = input("Digite a opção desejada? (V para voltar) ")
                    if sub == '1':
                        crud_produto.create_produto()
                    elif sub == '2':
                        nomeProduto = input("Visualizar produtos, deseja algum nome especifico? Caso não, pressione enter")
                        crud_produto.read_produto(nomeProduto)
                    elif sub == '3':
                        nomeProduto = input("Atualizar produtos, deseja algum nome especifico? ")
                        crud_produto.update_produto(nomeProduto)
                    elif sub == '4':
                        nomeProduto = input("Nome a ser deletado: ")
                        crud_produto.delete_produto(nomeProduto)

                elif key == '4':
                    print("Compras")
                    print("1 - Realizar compra")
                    print("2 - Ver compras realizadas")
                    sub = input("Digite a opção desejada? (V para voltar) ")
                    if sub == '1':
                        cpf_usuario = input("Digite o CPF do usuário: ")
                        carrinho_usuario = crud_compras.realizar_compra(cpf_usuario)
                    elif sub == '2':
                        cpf_usuario = input("Digite o CPF do usuário: ")
                        crud_compras.ver_compras_realizadas(cpf_usuario)

                elif key == '5':
                    print("Favoritos")
                    print("1 - Adicionar favoritos")
                    print("2 - Visualizar favoritos")
                    print("3 - Deletar favoritos")
                    sub = input("Digite a opção desejada? (V para voltar) ")
                    if sub == '1':
                        crud_favoritos.adicionarnovo_favorito()
                    elif sub == '2':
                        cpf_usuario = input("Digite o CPF do usuário: ")
                        crud_favoritos.visualizar_favoritos(cpf_usuario)
                    elif sub == '3':
                        cpf_usuario = input("Digite o CPF do usuário: ")
                        id_produto = input("Digite o ID do produto que deseja remover dos favoritos: ")
                        crud_favoritos.excluir_favorito(cpf_usuario, id_produto)
                else:
                    print("Opção inválida. Por favor, digite uma opção válida.")

print("Tchau, tchau! Volte sempre!")
