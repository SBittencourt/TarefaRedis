import uuid
import json
from datetime import datetime, timedelta
from bson import ObjectId
from pymongo import MongoClient
import redis
import hashlib

# Configurar conexão com MongoDB
uri = "mongodb+srv://silmara:123@cluster0.05p7qyc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client.RedisMercadoLivre  
usuarios_collection = db['usuarios']
produtos_collection = db['produtos']
lixeira_collection = db['lixeira']
compras_collection = db['compras']
favoritos_collection = db['favoritos']

# Configurar conexão com Redis
redis_client = redis.Redis(
    host='redis-17733.c11.us-east-1-2.ec2.redns.redis-cloud.com',
    port=17733,
    password='FX4HKWXiS1lTASjrm1SE7nWKhqJtW55s'
)

SESSION_TIMEOUT = 15 * 60  # 15 minutos
TRASH_TIMEOUT = 30 * 60    # 30 minutos

def main_menu():
    session_id = None
    user_id = None

    while True:
        if not session_id:
            print("\nMenu Principal:")
            print("1 - Criar nova conta")
            print("2 - Fazer login")
            print("S - Sair do Menu")
            key = input("Digite a opção desejada: ")

            if key == '1':
                user_id = create_new_user()
                if user_id:
                    session_id = create_session(user_id)
                    print("Usuário criado e logado com sucesso!")
            elif key == '2':
                user_id = user_login()
                if user_id:
                    session_id = create_session(user_id)
                    print("Login bem-sucedido!")
            elif key.upper() == 'S':
                print("Saindo do menu. Até logo!")
                break
            else:
                print("Opção inválida. Por favor, digite uma opção válida.")
        else:
            if not check_session(session_id):
                print("Sessão expirada. Por favor, faça login novamente.")
                session_id = None
                user_id = None
                continue

            print("\nMenu Principal:")
            print("1 - Criar produto")
            print("2 - Listar meus produtos")
            print("3 - Realizar compra")
            print("4 - Ver perfil")
            print("5 - Lixeira")
            print("6 - Favoritos")
            print("7 - Excluir produto")
            print("8 - Editar produto")
            print("9 - Editar usuário")
            print("10 - Excluir conta")
            print("L - Logout")
            print("S - Sair do Menu")
            key = input("Digite a opção desejada: ")

            if key == '1':
                create_product_menu(user_id)
            elif key == '2':
                list_my_products(user_id)
            elif key == '3':
                make_purchase(user_id)
            elif key == '4':
                view_profile(user_id)
            elif key == '5':
                trash_menu(user_id)
            elif key == '6':
                favorites_menu(user_id)
            elif key == '7':
                delete_product_menu(user_id)
            elif key == '8':
                edit_product_menu(user_id)
            elif key == '9':
                edit_user_profile(user_id)
            elif key == '10':
                if delete_user_account(user_id):
                    end_session(session_id)
                    session_id = None
                    user_id = None
            elif key.upper() == 'L':
                end_session(session_id)
                session_id = None
                user_id = None
                print("Logout realizado com sucesso.")
            elif key.upper() == 'S':
                print("Saindo do menu. Até logo!")
                break
            else:
                print("Opção inválida. Por favor, digite uma opção válida.")

def create_new_user():
    print("\nCriar novo usuário:")
    user_data = {
        "nome": input("Digite o nome: "),
        "sobrenome": input("Digite o sobrenome: "),
        "cpf": input("Digite o CPF: "),
        "endereco": input("Digite o endereço: "),
        "email": input("Digite o email: "),
        "telefone": input("Digite o telefone: "),
        "senha": hash_password(input("Digite a senha: "))
    }
    try:
        user_id = create_user(user_data)
        return user_id
    except Exception as e:
        print(f"Erro ao criar usuário: {e}")
        return None

def user_login():
    print("\nLogin de usuário:")
    cpf = input("Digite o CPF: ")
    senha = input("Digite a senha: ")
    user = usuarios_collection.find_one({"cpf": cpf})
    if user and user["senha"] == senha:
        print("Login bem-sucedido!")
        return str(user["_id"])
    else:
        print("Usuário ou senha incorretos.")
        return None

def create_session(user_id):
    session_id = str(uuid.uuid4())
    redis_client.setex(f"session:{session_id}", SESSION_TIMEOUT, user_id)
    return session_id

def check_session(session_id):
    return redis_client.exists(f"session:{session_id}")

def end_session(session_id):
    redis_client.delete(f"session:{session_id}")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(user_data):
    if usuarios_collection.find_one({"cpf": user_data["cpf"]}):
        raise Exception("CPF já cadastrado.")
    result = usuarios_collection.insert_one(user_data)
    return str(result.inserted_id)

def read_user(user_id):
    user = usuarios_collection.find_one({"_id": ObjectId(user_id)})
    return user

def update_user(user_id, updated_data):
    result = usuarios_collection.update_one({"_id": ObjectId(user_id)}, {"$set": updated_data})
    return result.modified_count

def delete_user(user_id):
    result = usuarios_collection.delete_one({"_id": ObjectId(user_id)})
    return result.deleted_count > 0

def create_product(product_data):
    result = produtos_collection.insert_one(product_data)
    return str(result.inserted_id)

def read_product(product_id):
    product = produtos_collection.find_one({"_id": ObjectId(product_id)})
    return product

def update_product(product_id, updated_data):
    result = produtos_collection.update_one({"_id": ObjectId(product_id)}, {"$set": updated_data})
    return result.modified_count

def delete_product(product_id):
    try:
        product_id = ObjectId(product_id)
        product = read_product(product_id)
        if product:

            lixeira_collection.insert_one(product)

            result = produtos_collection.delete_one({"_id": product_id})

            if result.deleted_count > 0:
                product['_id'] = str(product['_id'])
                trash_key = f"trash:{product['user_id']}:{product['_id']}"
                redis_client.setex(trash_key, TRASH_TIMEOUT, json.dumps(product))

                redis_client.setex(f"delete_later:{product['_id']}", TRASH_TIMEOUT, product['_id'])

            return result.deleted_count > 0
        return False
    except Exception as e:
        print(f"Erro ao excluir o produto: {e}")
        return False

def list_user_products(user_id):
    products = produtos_collection.find({"user_id": user_id})
    return list(products)

def list_all_products(exclude_user_id):
    products = produtos_collection.find({"user_id": {"$ne": exclude_user_id}})
    return list(products)

def list_favorites(user_id):
    favorites = favoritos_collection.find({"user_id": user_id})
    return list(favorites)

def add_favorite(user_id, product_id):
    if not favoritos_collection.find_one({"user_id": user_id, "product_id": product_id}):
        favoritos_collection.insert_one({"user_id": user_id, "product_id": product_id})

def remove_favorite(user_id, product_id):
    favoritos_collection.delete_one({"user_id": user_id, "product_id": product_id})

def create_product_menu(user_id):
    while True:
        print("\nCriar produto:")
        product_data = {
            "user_id": user_id,
            "nome": input("Digite o nome do produto: "),
            "preco": float(input("Digite o preço: ")),
            "quantia": int(input("Digite a quantidade no estoque: ")),
            "marca": input("Digite a marca: ")
        }
        try:
            create_product(product_data)
            print("Produto criado com sucesso!")
        except Exception as e:
            print(f"Erro ao criar produto: {e}")

        back_to_menu = input("Deseja voltar ao menu principal? (S/N): ")
        if back_to_menu.upper() == 'S':
            break

def list_my_products(user_id):
    while True:
        products = list_user_products(user_id)
        if products:
            for product in products:
                print(f"ID: {product['_id']}, Nome: {product['nome']}, Preço: {product['preco']}, Quantia: {product['quantia']}, Marca: {product['marca']}")
        else:
            print("Nenhum produto encontrado.")

        back_to_menu = input("Deseja voltar ao menu principal? (S/N): ")
        if back_to_menu.upper() == 'S':
            break

def make_purchase(user_id):
    while True:
        products = list_all_products(user_id)
        if products:
            for product in products:
                print(f"ID: {product['_id']}, Nome: {product['nome']}, Preço: {product['preco']}, Quantia: {product['quantia']}, Marca: {product['marca']}")

            product_id = input("Digite o ID do produto que deseja comprar: ")
            product = read_product(product_id)
            if product:
                if product["quantia"] > 0:
                    product["quantia"] -= 1
                    update_product(product_id, {"quantia": product["quantia"]})
                    compras_collection.insert_one({"user_id": user_id, "product_id": product_id, "data": datetime.now()})
                    print("Compra realizada com sucesso!")
                else:
                    print("Produto fora de estoque.")
            else:
                print("Produto não encontrado.")
        else:
            print("Nenhum produto disponível para compra.")

        back_to_menu = input("Deseja voltar ao menu principal? (S/N): ")
        if back_to_menu.upper() == 'S':
            break

def view_profile(user_id):
    user = read_user(user_id)
    if user:
        print("\nPerfil do Usuário:")
        print(f"Nome: {user['nome']}")
        print(f"Sobrenome: {user['sobrenome']}")
        print(f"CPF: {user['cpf']}")
        print(f"Endereço: {user['endereco']}")
        print(f"Email: {user['email']}")
        print(f"Telefone: {user['telefone']}")

def trash_menu(user_id):
    while True:
        print("\nLixeira:")
        trash_items = lixeira_collection.find({"user_id": user_id})
        if trash_items:
            for item in trash_items:
                print(f"ID: {item['_id']}, Nome: {item['nome']}, Preço: {item['preco']}, Quantia: {item['quantia']}, Marca: {item['marca']}")

            product_id = input("Digite o ID do produto que deseja restaurar ou deletar permanentemente (R/D): ")
            product = lixeira_collection.find_one({"_id": ObjectId(product_id)})
            if product:
                action = input("Digite 'R' para restaurar ou 'D' para deletar permanentemente: ").upper()
                if action == 'R':
                    produtos_collection.insert_one(product)
                    lixeira_collection.delete_one({"_id": ObjectId(product_id)})
                    redis_client.delete(f"trash:{user_id}:{product_id}")
                    redis_client.delete(f"delete_later:{product_id}")
                    print("Produto restaurado com sucesso!")
                elif action == 'D':
                    lixeira_collection.delete_one({"_id": ObjectId(product_id)})
                    redis_client.delete(f"trash:{user_id}:{product_id}")
                    redis_client.delete(f"delete_later:{product_id}")
                    print("Produto deletado permanentemente com sucesso!")
                else:
                    print("Ação inválida.")
            else:
                print("Produto não encontrado na lixeira.")
        else:
            print("Lixeira vazia.")

        back_to_menu = input("Deseja voltar ao menu principal? (S/N): ")
        if back_to_menu.upper() == 'S':
            break

def delete_product_menu(user_id):
    while True:
        products = list_user_products(user_id)
        if products:
            for product in products:
                print(f"ID: {product['_id']}, Nome: {product['nome']}, Preço: {product['preco']}, Quantia: {product['quantia']}, Marca: {product['marca']}")

            product_id = input("Digite o ID do produto que deseja excluir: ")
            if delete_product(product_id):
                print("Produto movido para a lixeira com sucesso!")
            else:
                print("Falha ao mover o produto para a lixeira.")
        else:
            print("Nenhum produto encontrado.")

        back_to_menu = input("Deseja voltar ao menu principal? (S/N): ")
        if back_to_menu.upper() == 'S':
            break

def edit_product_menu(user_id):
    while True:
        products = list_user_products(user_id)
        if products:
            for product in products:
                print(f"ID: {product['_id']}, Nome: {product['nome']}, Preço: {product['preco']}, Quantia: {product['quantia']}, Marca: {product['marca']}")

            product_id = input("Digite o ID do produto que deseja editar: ")
            product = read_product(product_id)
            if product:
                updated_data = {}
                nome = input(f"Nome ({product['nome']}): ")
                if nome:
                    updated_data["nome"] = nome
                preco = input(f"Preço ({product['preco']}): ")
                if preco:
                    updated_data["preco"] = float(preco)
                quantia = input(f"Quantia ({product['quantia']}): ")
                if quantia:
                    updated_data["quantia"] = int(quantia)
                marca = input(f"Marca ({product['marca']}): ")
                if marca:
                    updated_data["marca"] = marca

                if updated_data:
                    update_product(product_id, updated_data)
                    print("Produto atualizado com sucesso!")
                else:
                    print("Nenhuma atualização feita.")
            else:
                print("Produto não encontrado.")
        else:
            print("Nenhum produto encontrado.")

        back_to_menu = input("Deseja voltar ao menu principal? (S/N): ")
        if back_to_menu.upper() == 'S':
            break

def edit_user_profile(user_id):
    while True:
        user = read_user(user_id)
        if user:
            updated_data = {}
            nome = input(f"Nome ({user['nome']}): ")
            if nome:
                updated_data["nome"] = nome
            sobrenome = input(f"Sobrenome ({user['sobrenome']}): ")
            if sobrenome:
                updated_data["sobrenome"] = sobrenome
            endereco = input(f"Endereço ({user['endereco']}): ")
            if endereco:
                updated_data["endereco"] = endereco
            email = input(f"Email ({user['email']}): ")
            if email:
                updated_data["email"] = email
            telefone = input(f"Telefone ({user['telefone']}): ")
            if telefone:
                updated_data["telefone"] = telefone
            senha = input("Nova senha (deixe em branco para manter a senha atual): ")
            if senha:
                updated_data["senha"] = hash_password(senha)

            if updated_data:
                update_user(user_id, updated_data)
                print("Perfil atualizado com sucesso!")
            else:
                print("Nenhuma atualização feita.")

        back_to_menu = input("Deseja voltar ao menu principal? (S/N): ")
        if back_to_menu.upper() == 'S':
            break

def delete_user_account(user_id):
    confirm = input("Tem certeza que deseja excluir sua conta? (S/N): ")
    if confirm.upper() == 'S':
        if delete_user(user_id):
            print("Conta excluída com sucesso.")
            return True
        else:
            print("Falha ao excluir a conta.")
            return False
    return False

def favorites_menu(user_id):
    while True:
        print("\nFavoritos:")
        favorites = list_favorites(user_id)
        if favorites:
            for favorite in favorites:
                product = read_product(favorite["product_id"])
                if product:
                    print(f"ID: {product['_id']}, Nome: {product['nome']}, Preço: {product['preco']}, Quantia: {product['quantia']}, Marca: {product['marca']}")

            action = input("Digite 'A' para adicionar, 'R' para remover um favorito ou 'S' para sair: ").upper()
            if action == 'A':
                product_id = input("Digite o ID do produto que deseja adicionar aos favoritos: ")
                add_favorite(user_id, product_id)
                print("Produto adicionado aos favoritos com sucesso!")
            elif action == 'R':
                product_id = input("Digite o ID do produto que deseja remover dos favoritos: ")
                remove_favorite(user_id, product_id)
                print("Produto removido dos favoritos com sucesso!")
            elif action == 'S':
                break
            else:
                print("Ação inválida.")
        else:
            print("Nenhum favorito encontrado.")

        back_to_menu = input("Deseja voltar ao menu principal? (S/N): ")
        if back_to_menu.upper() == 'S':
            break

def auto_delete_expired_products():
    current_time = datetime.now()
    expired_keys = redis_client.keys("delete_later:*")
    for key in expired_keys:
        product_id = redis_client.get(key)
        if product_id:
            lixeira_collection.delete_one({"_id": ObjectId(product_id)})
            redis_client.delete(key)
            print(f"Produto {product_id} excluído permanentemente.")

if __name__ == "__main__":
    main_menu()
    auto_delete_expired_products()

