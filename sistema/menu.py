import uuid
import json
from datetime import datetime, timedelta
from bson import ObjectId
from pymongo import MongoClient
import redis

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
ACCOUNT_DELETION_TIMEOUT = 2 * 60  # 2 minutos

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
                end_session(session_id)
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
        "senha": input("Digite a senha: ")
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
        
        if redis_client.exists(f"delete_account:{user['_id']}"):
            redis_client.delete(f"delete_account:{user['_id']}")
            print("Exclusão da conta cancelada com sucesso!")
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
    user_id = redis_client.get(f"session:{session_id}")
    if user_id:
        user_id = user_id.decode('utf-8')  
        trash_keys = redis_client.keys(f"trash:{user_id}:*")
        for key in trash_keys:
            product_id = key.decode('utf-8').split(':')[-1]
            lixeira_collection.delete_one({"_id": ObjectId(product_id)})
            redis_client.delete(key)
            redis_client.delete(f"delete_later:{product_id}")
        print("Todos os itens da lixeira foram excluídos.")
    redis_client.delete(f"session:{session_id}")


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
    if not isinstance(product_id, ObjectId):
        try:
            product_id = ObjectId(product_id)
        except errors.InvalidId:
            return None
    return produtos_collection.find_one({"_id": product_id})


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
            break
        except Exception as e:
            print(f"Erro ao criar produto: {e}")

def list_my_products(user_id):
    print("\nMeus produtos:")
    products = list_user_products(user_id)
    for product in products:
        print(f"ID: {product['_id']}, Nome: {product['nome']}, Preço: {product['preco']}, Quantidade: {product['quantia']}, Marca: {product['marca']}")

from bson import ObjectId, errors

def make_purchase(user_id):
    print("\nProdutos disponíveis para compra:")
    products = list_all_products(user_id)
    for product in products:
        print(f"ID: {product['_id']}, Nome: {product['nome']}, Preço: {product['preco']}, Quantidade: {product['quantia']}, Marca: {product['marca']}")
    
    product_ids = input("Digite os IDs dos produtos que deseja comprar (separados por vírgula): ").split(",")
    purchase = {
        "user_id": user_id,
        "products": [],
        "total": 0.0
    }

    for product_id in product_ids:
        try:
            product_id = ObjectId(product_id.strip())
            product = read_product(product_id)
            if product:
                quantity = int(input(f"Digite a quantidade para {product['nome']} (em estoque: {product['quantia']}): "))
                if quantity <= product['quantia']:
                    subtotal = quantity * product['preco']
                    purchase["products"].append({"product_id": product_id, "quantity": quantity, "price": product['preco'], "subtotal": subtotal})
                    purchase["total"] += subtotal
                else:
                    print(f"Quantidade solicitada para {product['nome']} excede o estoque disponível.")
            else:
                print(f"Produto com ID {product_id} não encontrado.")
        except (errors.InvalidId, ValueError) as e:
            print(f"ID do produto inválido: {product_id}")

    if purchase["products"]:
        print(f"\nValor total da compra: {purchase['total']:.2f}")
        confirm = input("Deseja confirmar a compra? (S/N): ").strip().upper()
        if confirm == 'S':
            compras_collection.insert_one(purchase)
            for item in purchase["products"]:
                produtos_collection.update_one({"_id": item["product_id"]}, {"$inc": {"quantia": -item["quantity"]}})
            print("Compra realizada com sucesso!")
        else:
            print("Compra cancelada.")
    else:
        print("Nenhum produto selecionado.")


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

        print("\nCompras Realizadas:")
        purchases = compras_collection.find({"user_id": user_id})
        total_spent = 0.0
        if purchases:
            for purchase in purchases:
                total = purchase.get('total', 0.0)
                print(f"Compra ID: {purchase['_id']}, Valor Total: {total:.2f}")
                total_spent += total
                for item in purchase['products']:
                    product = read_product(item['product_id'])
                    if product:
                        subtotal = item.get('subtotal', item['quantity'] * item['price'])
                        print(f" - Produto: {product['nome']}, Quantidade: {item['quantity']}, Preço: {item['price']}, Subtotal: {subtotal:.2f}")
        else:
            print("Nenhuma compra realizada.")
    else:
        print("Usuário não encontrado.")




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

def favorites_menu(user_id):
    print("\nFavoritos:")
    favorites = list_favorites(user_id)
    for favorite in favorites:
        product = read_product(favorite['product_id'])
        if product:
            print(f"ID: {product['_id']}, Nome: {product['nome']}, Preço: {product['preco']}, Quantidade: {product['quantia']}, Marca: {product['marca']}")
    
    print("1 - Adicionar favorito")
    print("2 - Remover favorito")
    print("3 - Voltar")
    choice = input("Digite a opção desejada: ").strip()

    if choice == '1':
        product_id = input("Digite o ID do produto que deseja adicionar aos favoritos: ").strip()
        add_favorite(user_id, product_id)
        print("Produto adicionado aos favoritos com sucesso!")
    elif choice == '2':
        product_id = input("Digite o ID do produto que deseja remover dos favoritos: ").strip()
        remove_favorite(user_id, product_id)
        print("Produto removido dos favoritos com sucesso!")

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
    print("\nEditar produto:")
    products = list_user_products(user_id)
    for product in products:
        print(f"ID: {product['_id']}, Nome: {product['nome']}, Preço: {product['preco']}, Quantidade: {product['quantia']}, Marca: {product['marca']}")

    product_id = input("Digite o ID do produto que deseja editar: ").strip()
    product = read_product(product_id)
    if product:
        print("\nDigite os novos dados (pressione Enter para manter os dados atuais):")
        nome = input(f"Nome ({product['nome']}): ").strip()
        preco = input(f"Preço ({product['preco']}): ").strip()
        quantia = input(f"Quantidade ({product['quantia']}): ").strip()
        marca = input(f"Marca ({product['marca']}): ").strip()

        updated_data = {}
        if nome:
            updated_data["nome"] = nome
        if preco:
            updated_data["preco"] = float(preco)
        if quantia:
            updated_data["quantia"] = int(quantia)
        if marca:
            updated_data["marca"] = marca

        if updated_data:
            if update_product(product_id, updated_data):
                print("Produto atualizado com sucesso!")
            else:
                print("Erro ao atualizar o produto.")
        else:
            print("Nenhuma alteração feita.")
    else:
        print("Produto não encontrado.")

def edit_user_profile(user_id):
    user = read_user(user_id)
    if user:
        print("\nEditar perfil do usuário:")
        print("Pressione Enter para manter os dados atuais.")

        nome = input(f"Nome ({user['nome']}): ").strip()
        sobrenome = input(f"Sobrenome ({user['sobrenome']}): ").strip()
        endereco = input(f"Endereço ({user['endereco']}): ").strip()
        email = input(f"Email ({user['email']}): ").strip()
        telefone = input(f"Telefone ({user['telefone']}): ").strip()
        senha = input("Digite a nova senha (deixe em branco para manter a senha atual): ").strip()

        updated_data = {}
        if nome:
            updated_data["nome"] = nome
        if sobrenome:
            updated_data["sobrenome"] = sobrenome
        if endereco:
            updated_data["endereco"] = endereco
        if email:
            updated_data["email"] = email
        if telefone:
            updated_data["telefone"] = telefone
        if senha:
            updated_data["senha"] = senha

        if updated_data:
            if update_user(user_id, updated_data):
                print("Perfil atualizado com sucesso!")
            else:
                print("Erro ao atualizar o perfil.")
        else:
            print("Nenhuma alteração feita.")
    else:
        print("Usuário não encontrado.")

def delete_user_account(user_id):
    print("\nExcluir conta:")
    confirmation = input("Tem certeza de que deseja excluir sua conta? (S/N): ").strip().upper()
    if confirmation == 'S':
        user = read_user(user_id)
        if user:
            user["_id"] = str(user["_id"])  
            redis_client.setex(f"delete_account:{user_id}", ACCOUNT_DELETION_TIMEOUT, json.dumps(user))
            print("Conta marcada para exclusão. Faça login novamente dentro de 2 minutos para cancelar a exclusão.")
            return True
    print("Exclusão de conta cancelada.")
    return False

if __name__ == "__main__":
    main_menu()
