import redis
from pymongo import MongoClient
from datetime import datetime, timedelta
import json
import uuid

# Configurar conexão com MongoDB
uri = "mongodb+srv://silmara:123@cluster0.05p7qyc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client.RedisMercadoLivre  # Banco de dados renomeado
usuarios_collection = db.usuarios  # Coleção de usuários
produtos_collection = db.produtos  # Coleção de produtos
compras_collection = db.compras  # Coleção de compras

# Configurar conexão com Redis
redis_client = redis.Redis(
    host='redis-17733.c11.us-east-1-2.ec2.redns.redis-cloud.com',
    port=17733,
    password='FX4HKWXiS1lTASjrm1SE7nWKhqJtW55s'
)

SESSION_TIMEOUT = 30 * 60  # 30 minutos
TRASH_TIMEOUT = 30 * 60  # 30 minutos

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

def create_user(user_data):
    if usuarios_collection.find_one({"cpf": user_data["cpf"]}):
        raise Exception("CPF já cadastrado.")
    result = usuarios_collection.insert_one(user_data)
    return str(result.inserted_id)

def read_user(user_id):
    user = usuarios_collection.find_one({"_id": user_id})
    return user

def update_user(user_id, updated_data):
    result = usuarios_collection.update_one({"_id": user_id}, {"$set": updated_data})
    return result.modified_count

def delete_user(user_id):
    result = usuarios_collection.delete_one({"_id": user_id})
    return result.deleted_count > 0

def create_product(product_data):
    result = produtos_collection.insert_one(product_data)
    return str(result.inserted_id)

def read_product(product_id):
    product = produtos_collection.find_one({"_id": product_id})
    return product

def update_product(product_id, updated_data):
    result = produtos_collection.update_one({"_id": product_id}, {"$set": updated_data})
    return result.modified_count

def delete_product(product_id):
    result = produtos_collection.delete_one({"_id": product_id})
    return result.deleted_count > 0

def list_user_products(user_id):
    products = produtos_collection.find({"user_id": user_id})
    return list(products)

def list_all_products(exclude_user_id):
    products = produtos_collection.find({"user_id": {"$ne": exclude_user_id}})
    return list(products)

def create_product_menu(user_id):
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

def list_my_products(user_id):
    products = list_user_products(user_id)
    if products:
        for product in products:
            print(f"ID: {product['_id']}, Nome: {product['nome']}, Preço: {product['preco']}, Quantia: {product['quantia']}, Marca: {product['marca']}")
    else:
        print("Você não possui produtos cadastrados.")

def make_purchase(user_id):
    products = list_all_products(user_id)
    if not products:
        print("Não há produtos disponíveis para compra.")
        return

    cart = []
    while True:
        print("\nProdutos disponíveis:")
        for i, product in enumerate(products):
            print(f"{i + 1} - {product['nome']} (Preço: {product['preco']}, Quantia: {product['quantia']})")

        choice = input("Digite o número do produto que deseja adicionar ao carrinho (ou 'F' para finalizar a compra): ")
        if choice.upper() == 'F':
            break

        try:
            product_index = int(choice) - 1
            if 0 <= product_index < len(products):
                product = products[product_index]
                cart.append(product)
                print(f"Produto '{product['nome']}' adicionado ao carrinho.")
            else:
                print("Opção inválida.")
        except ValueError:
            print("Opção inválida.")

    if cart:
        total = sum(product['preco'] for product in cart)
        print(f"\nTotal da compra: {total}")
        confirm = input("Deseja confirmar a compra? (S/N): ")
        if confirm.upper() == 'S':
            for product in cart:
                update_product(product['_id'], {"quantia": product['quantia'] - 1})
                # Registrar a compra
                compra = {
                    "user_id": user_id,
                    "product_id": product["_id"],
                    "data_compra": datetime.now()
                }
                compras_collection.insert_one(compra)
            print("Compra realizada com sucesso!")
        else:
            print("Compra cancelada.")
    else:
        print("Carrinho vazio.")

def trash_menu(user_id):
    print("\nLixeira:")
    products = list_user_products(user_id)
    if not products:
        print("Você não possui produtos para mover para a lixeira.")
        return

    while True:
        print("\nProdutos disponíveis para mover para a lixeira:")
        for i, product in enumerate(products):
            print(f"{i + 1} - {product['nome']} (Preço: {product['preco']}, Quantia: {product['quantia']})")

        choice = input("Digite o número do produto que deseja mover para a lixeira (ou 'S' para sair): ")
        if choice.upper() == 'S':
            break

        try:
            product_index = int(choice) - 1
            if 0 <= product_index < len(products):
                product = products[product_index]
                redis_client.setex(f"trash:{product['_id']}", TRASH_TIMEOUT, json.dumps(product, default=str))
                delete_product(product['_id'])
                print(f"Produto '{product['nome']}' movido para a lixeira.")
            else:
                print("Opção inválida.")
        except ValueError:
            print("Opção inválida.")

def favorites_menu(user_id):
    print("\nFavoritos:")
    user = read_user(user_id)
    if user:
        if "favoritos" not in user:
            user["favoritos"] = []

        while True:
            print("\n1 - Adicionar favorito")
            print("2 - Remover favorito")
            print("3 - Listar favoritos")
            print("S - Sair")
            choice = input("Digite a opção desejada: ")

            if choice == '1':
                products = list_all_products(user_id)
                for i, product in enumerate(products):
                    print(f"{i + 1} - {product['nome']} (Preço: {product['preco']}, Quantia: {product['quantia']})")
                product_choice = int(input("Digite o número do produto que deseja adicionar aos favoritos: ")) - 1
                if 0 <= product_choice < len(products):
                    favorite_product = products[product_choice]
                    user["favoritos"].append(str(favorite_product["_id"]))  # Convertendo para string
                    update_user(user_id, {"favoritos": user["favoritos"]})
                    print(f"Produto '{favorite_product['nome']}' adicionado aos favoritos.")
                else:
                    print("Opção inválida.")
            elif choice == '2':
                for i, product_id in enumerate(user["favoritos"]):
                    product = read_product(product_id)
                    if product:
                        print(f"{i + 1} - {product['nome']} (Preço: {product['preco']})")
                product_choice = int(input("Digite o número do produto que deseja remover dos favoritos: ")) - 1
                if 0 <= product_choice < len(user["favoritos"]):
                    removed_product_id = user["favoritos"].pop(product_choice)
                    update_user(user_id, {"favoritos": user["favoritos"]})
                    removed_product = read_product(removed_product_id)
                    if removed_product:
                        print(f"Produto '{removed_product['nome']}' removido dos favoritos.")
                    else:
                        print("Produto não encontrado.")
                else:
                    print("Opção inválida.")
            elif choice == '3':
                if user["favoritos"]:
                    for product_id in user["favoritos"]:
                        product = read_product(product_id)
                        if product:
                            print(f"ID: {product['_id']}, Nome: {product['nome']}, Preço: {product['preco']}")
                        else:
                            print(f"Produto com ID {product_id} não encontrado.")
                else:
                    print("Você não possui produtos favoritos.")
            elif choice.upper() == 'S':
                break
            else:
                print("Opção inválida.")
    else:
        print("Usuário não encontrado.")


def view_profile(user_id):

    from bson import ObjectId
    user_id = ObjectId(user_id)  

    user = read_user(user_id)
    if user:
        print(f"Nome: {user['nome']}, Sobrenome: {user['sobrenome']}, CPF: {user['cpf']}, Endereço: {user['endereco']}, Email: {user['email']}, Telefone: {user['telefone']}")
        print("Compras realizadas:")
        compras = compras_collection.find({"user_id": user_id})
        for compra in compras:
            product = read_product(compra["product_id"])
            print(f"Produto: {product['nome']}, Data da compra: {compra['data_compra']}")
    else:
        print("Usuário não encontrado.")


if __name__ == "__main__":
    main_menu()
