import uuid
import json
from datetime import datetime, timedelta
from bson import ObjectId
from pymongo import MongoClient
import redis
import time

# Configurar conexão com MongoDB
uri = "mongodb+srv://silmara:123@cluster0.05p7qyc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client.RedisMercadoLivre  
usuarios_collection = db['usuarios']
produtos_collection = db['produtos']
lixeira_collection = db['lixeira']
compras_collection = db['compras']

# Configurar conexão com Redis
redis_client = redis.Redis(
    host='redis-17733.c11.us-east-1-2.ec2.redns.redis-cloud.com',
    port=17733,
    password='FX4HKWXiS1lTASjrm1SE7nWKhqJtW55s'
)

SESSION_TIMEOUT = 30 * 60 # 30 minutos
TRASH_TIMEOUT = 30 * 60 # 30 minutos

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
            # Mover o produto para a coleção "lixeira"
            lixeira_collection.insert_one(product)

            # Remover o produto da coleção "produtos"
            result = produtos_collection.delete_one({"_id": product_id})

            if result.deleted_count > 0:
                # Converter o ObjectId para string antes de salvar no Redis
                product['_id'] = str(product['_id'])
                trash_key = f"trash:{product['user_id']}:{product['_id']}"
                redis_client.setex(trash_key, TRASH_TIMEOUT, json.dumps(product))

                # Agendar a exclusão do produto após TRASH_TIMEOUT
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
            print("Você não possui produtos cadastrados.")

        back_to_menu = input("Deseja voltar ao menu principal? (S/N): ")
        if back_to_menu.upper() == 'S':
            break

def make_purchase(user_id):
    while True:
        products = list_all_products(user_id)
        if not products:
            print("Não há produtos disponíveis para compra.")
            back_to_menu = input("Deseja voltar ao menu principal? (S/N): ")
            if back_to_menu.upper() == 'S':
                break
            continue

        cart = []
        while True:
            print("\nProdutos disponíveis:")
            for i, product in enumerate(products):
                print(f"{i + 1} - {product['nome']} (Preço: {product['preco']}, Quantia: {product['quantia']})")

            choice = input("Digite o número do produto que deseja adicionar ao carrinho (ou 'F' para finalizar): ")

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

                    compra = {
                        "user_id": user_id,
                        "product_id": product['_id'],
                        "data_compra": datetime.now()
                    }
                    compras_collection.insert_one(compra)
                print("Compra realizada com sucesso!")
            else:
                print("Compra cancelada.")
        else:
            print("Nenhum produto adicionado ao carrinho.")

        back_to_menu = input("Deseja voltar ao menu principal? (S/N): ")
        if back_to_menu.upper() == 'S':
            break

def view_profile(user_id):
    while True:
        user = read_user(user_id)
        if user:
            print(f"\nPerfil do usuário:\nNome: {user['nome']}\nSobrenome: {user['sobrenome']}\nCPF: {user['cpf']}\nEndereço: {user['endereco']}\nEmail: {user['email']}\nTelefone: {user['telefone']}")
        else:
            print("Usuário não encontrado.")

        back_to_menu = input("Deseja voltar ao menu principal? (S/N): ")
        if back_to_menu.upper() == 'S':
            break

def trash_menu(user_id):
    while True:
        print("\nLixeira:")
        trash_key_prefix = f"trash:{user_id}:"
        trash_keys = redis_client.keys(f"{trash_key_prefix}*")
        if not trash_keys:
            print("Você não possui produtos na lixeira.")
            back_to_menu = input("Deseja voltar ao menu principal? (S/N): ")
            if back_to_menu.upper() == 'S':
                break
            continue

        print("\nProdutos na lixeira:")
        for i, trash_key in enumerate(trash_keys):
            product_id = trash_key.decode().replace(trash_key_prefix, '')
            product = json.loads(redis_client.get(trash_key))
            print(f"{i + 1} - {product['nome']} (Preço: {product['preco']}, Quantia: {product['quantia']})")

        print("\nOpções:")
        print("1 - Restaurar produto")
        print("2 - Excluir definitivamente produto")
        print("V - Voltar ao Menu Principal")
        choice = input("Digite a opção desejada: ")

        if choice == '1':
            product_index = int(input("Digite o número do produto que deseja restaurar: ")) - 1
            if 0 <= product_index < len(trash_keys):
                trash_key = trash_keys[product_index]
                product_id = trash_key.decode().replace(trash_key_prefix, '')
                product = json.loads(redis_client.get(trash_key))
                create_product(product)  # Restaurar produto para a coleção "produtos"
                redis_client.delete(trash_key)  # Remover do Redis
                lixeira_collection.delete_one({"_id": ObjectId(product_id)})  # Remover da coleção "lixeira"
                print(f"Produto '{product['nome']}' restaurado com sucesso.")
            else:
                print("Opção inválida.")

        elif choice == '2':
            product_index = int(input("Digite o número do produto que deseja excluir definitivamente: ")) - 1
            if 0 <= product_index < len(trash_keys):
                trash_key = trash_keys[product_index]
                product_id = trash_key.decode().replace(trash_key_prefix, '')
                redis_client.delete(trash_key)  # Remover do Redis
                lixeira_collection.delete_one({"_id": ObjectId(product_id)})  # Remover da coleção "lixeira"
                print("Produto excluído definitivamente da lixeira.")
            else:
                print("Opção inválida.")

        elif choice.upper() == 'V':
            break

        else:
            print("Opção inválida.")

def favorites_menu(user_id):
    while True:
        print("\nFavoritos:")
        # Aqui você pode adicionar a lógica para listar, adicionar e remover produtos dos favoritos.

        back_to_menu = input("Deseja voltar ao menu principal? (S/N): ")
        if back_to_menu.upper() == 'S':
            break

def delete_product_menu(user_id):
    while True:
        print("\nExcluir produto:")
        products = list_user_products(user_id)

        if not products:
            print("Você não possui produtos para excluir.")
            back_to_menu = input("Deseja voltar ao menu principal? (S/N): ")
            if back_to_menu.upper() == 'S':
                break
            continue

        print("\nProdutos disponíveis para exclusão:")
        for i, product in enumerate(products):
            print(f"{i + 1} - ID: {product['_id']}, Nome: {product['nome']}")

        choice = input("Digite o número do produto que deseja excluir (ou 'V' para voltar ao Menu Principal): ")

        if choice.upper() == 'V':
            break

        try:
            product_index = int(choice) - 1
            if 0 <= product_index < len(products):
                product_id = products[product_index]['_id']
                if delete_product(product_id):
                    print("Produto movido para a lixeira com sucesso.")
                    products = list_user_products(user_id)  # Atualizar a lista de produtos após exclusão
                else:
                    print("Não foi possível mover o produto para a lixeira.")
            else:
                print("Opção inválida.")
        except ValueError:
            print("Opção inválida. Digite um número válido.")

def schedule_deletion():
    while True:
        # Verificar periodicamente se há produtos agendados para exclusão
        delete_keys = redis_client.keys("delete_later:*")
        for delete_key in delete_keys:
            product_id = redis_client.get(delete_key).decode()
            if not redis_client.exists(f"trash:{product_id}"):
                lixeira_collection.delete_one({"_id": ObjectId(product_id)})
                redis_client.delete(delete_key)
        # Aguarda 1 minuto antes de verificar novamente
        time.sleep(60)

if __name__ == "__main__":
    # Iniciar a tarefa de agendamento de exclusão em segundo plano
    import threading
    deletion_thread = threading.Thread(target=schedule_deletion, daemon=True)
    deletion_thread.start()

    main_menu()
