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
produtos_collection = db["Produto"]  # Supondo que você tenha uma coleção de produtos

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

# Funções de Manipulação de Produtos (exemplo do Mercado Livre)
def create_product(product_id, product_data):
    r.set(product_id, json.dumps(product_data))
    produtos_collection.insert_one(product_data)

def read_product(product_id):
    product_data = r.get(product_id)
    if product_data:
        return json.loads(product_data)
    else:
        return produtos_collection.find_one({"_id": product_id})

def update_product(product_id, updated_data):
    r.set(product_id, json.dumps(updated_data))
    produtos_collection.update_one({"_id": product_id}, {"$set": updated_data})

def delete_product(product_id):
    r.delete(product_id)
    produtos_collection.delete_one({"_id": product_id})

# Exemplo de uso
if __name__ == "__main__":
    # Criar um usuário
    user_id = "user123"
    user_data = {
        "_id": user_id,
        "nome": "João",
        "sobrenome": "Silva",
        "enderecos": [
            {"rua": "Av. Paulista", "num": "1000", "bairro": "Centro", "cidade": "São Paulo", "estado": "SP", "cep": "01310-000"}
        ]
    }
    create_user(user_id, user_data)
    
    # Ler o usuário
    print(read_user(user_id))
    
    # Atualizar o usuário
    updated_user_data = user_data.copy()
    updated_user_data["sobrenome"] = "Santos"
    update_user(user_id, updated_user_data)
    
    # Deletar o usuário
    delete_user(user_id)
    
    # Login temporário
    session_id, session_data = login(user_id)
    print("Sessão ativa:", check_session(session_id))
