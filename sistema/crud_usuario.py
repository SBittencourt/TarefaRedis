import redis
from pymongo import MongoClient
from datetime import datetime, timedelta
import json
from crud_usuario import *

# Configurar conexão com MongoDB
uri = "mongodb+srv://silmara:123@cluster0.05p7qyc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client.mercadolivre  # Banco de dados
usuarios_collection = db.usuarios  # Coleção de usuários

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
        "_id": input("Digite o ID de usuário: "),
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
        return user["_id"]
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

    for i, product in enumerate(products):
        print(f"{i + 1} - {product['nome']} (Preço: {product['preco']}, Quantia: {product['quantia']})")

    choice = input("Digite o número do produto que deseja mover para a lixeira: ")
    try:
        product_index = int(choice) - 1
        if 0 <= product_index < len(products):
            product = products[product_index]
            redis_client.setex(f"trash:{product['_id']}", TRASH_TIMEOUT, json.dumps(product))
            delete_product(product['_id'])
            print(f"Produto '{product['nome']}' movido para a lixeira.")
        else:
            print("Opção inválida.")
    except ValueError:
        print("Opção inválida.")

def favorites_menu(user_id):
    print("\nFavoritos:")
    # Implementar lógica de favoritos
    pass

def view_profile(user_id):
    user = read_user(user_id)
    if user:
        print(f"Nome: {user['nome']}, Sobrenome: {user['sobrenome']}, CPF: {user['cpf']}, Endereço: {user['endereco']}, Email: {user['email']}, Telefone: {user['telefone']}")
    else:
        print("Usuário não encontrado.")

if __name__ == "__main__":
    main_menu()
