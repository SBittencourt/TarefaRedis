import redis
import pymongo
import json
from pymongo.server_api import ServerApi
from datetime import datetime, timedelta

# Conexão com o Redis
r = redis.Redis(
    host='redis-17733.c11.us-east-1-2.ec2.redns.redis-cloud.com',
    port=17733,
    password='FX4HKWXiS1lTASjrm1SE7nWKhqJtW55s'
)

# Conexão com o MongoDB
client = pymongo.MongoClient(
    "mongodb+srv://silmara:123@cluster0.05p7qyc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0", 
    server_api=ServerApi('1')
)
db = client.RedisMercadoLivre
usuarios_collection = db["Usuário"]

# Funções CRUD
def create_user(user_id, user_data):
    r.set(user_id, json.dumps(user_data))
    usuarios_collection.insert_one(user_data)

def read_user(user_id):
    user_data = r.get(user_id)
    if user_data:
        return json.loads(user_data)
    else:
        return usuarios_collection.find_one({"_id": user_id})

def update_user(user_id, updated_data):
    r.set(user_id, json.dumps(updated_data))
    usuarios_collection.update_one({"_id": user_id}, {"$set": updated_data})

def delete_user(user_id):
    r.delete(user_id)
    usuarios_collection.delete_one({"_id": user_id})

# Função de Login Temporário
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

# Função de login de usuário
def user_login():
    while True:
        user_id = input("Digite seu ID de usuário: ")
        senha = input("Digite sua senha: ")

        # Verifica usuário e senha no MongoDB
        user = usuarios_collection.find_one({"_id": user_id, "senha": senha})
        if user:
            session_id, session_data = login(user_id)
            print("Login bem-sucedido!")
            return session_id, user_id
        else:
            print("Usuário ou senha incorretos. Tente novamente.")

# Função para criar um novo usuário
def create_new_user():
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
    create_user(user_id, usuario)
    print("Usuário criado com sucesso!")

if __name__ == "__main__":
    while True:
        print("Bem-vindo! Por favor, escolha uma opção:")
        print("1 - Criar nova conta")
        print("2 - Fazer login")
        opcao = input("Digite a opção desejada: ")

        if opcao == '1':
            create_new_user()
            
        elif opcao == '2':
            session_id, user_id = user_login()
            if session_id:
                print(f"Sessão ativa para o usuário {user_id}. Bem-vindo!")





                break

        else:
            print("Opção inválida. Por favor, tente novamente.")
