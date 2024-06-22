from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from crud_usuario import read_usuario

uri = "mongodb+srv://silmara:123@cluster0.05p7qyc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
global db
db = client.mercadolivre

def adicionar_favorito(cpf_usuario, id_produto):
    global db
    mycol = db.favoritos
    produto = db.produto.find_one({"_id": id_produto})
    if not produto:
        print("Erro: Produto não encontrado.")
        return
    favorito = {"cpf_usuario": cpf_usuario, "id_produto": id_produto}
    x = mycol.insert_one(favorito)
    print("Produto adicionado aos favoritos do usuário com sucesso!")

def visualizar_favoritos(cpf_usuario):
    global db
    mycol = db.favoritos
    print("Favoritos do usuário:")
    myquery = {"cpf_usuario": cpf_usuario}
    mydoc = mycol.find(myquery)
    for favorito in mydoc:
        produto = db.produto.find_one({"_id": favorito["id_produto"]})
        if produto:
            vendedor = db.vendedor.find_one({"cpf": produto.get("vendedor")})
            if vendedor:
                print("Nome do Produto:", produto["nome"])
                print("Preço:", produto["preço"])
                print("Vendedor:", vendedor["nome"])
                print()
            else:
                print("Vendedor não encontrado para o produto:", produto["nome"])
        else:
            print("Produto não encontrado para o favorito com ID:", favorito["_id"])

def excluir_favorito(cpf_usuario):
    global db
    mycol = db.favoritos
    myquery = {"cpf_usuario": cpf_usuario}
    favoritos = list(mycol.find(myquery))

    if favoritos:
        print("Favoritos do usuário:")
        for i, favorito in enumerate(favoritos, start=1):
            produto = db.produto.find_one({"_id": favorito["id_produto"]})
            if produto:
                vendedor = db.vendedor.find_one({"cpf": produto.get("vendedor")})
                if vendedor:
                    print(f"{i} - Nome do Produto: {produto['nome']} | Preço: {produto['preço']} | Vendedor: {vendedor['nome']}")
                else:
                    print(f"{i} - Nome do Produto: {produto['nome']} | Preço: {produto['preço']} | Vendedor: Não disponível")
            else:
                print(f"{i} - Produto não encontrado para o favorito com ID: {favorito['id_produto']}")

        while True:
            try:
                indice = int(input("Digite o número do favorito que deseja excluir (ou '0' para cancelar): "))
                if indice == 0:
                    print("Operação cancelada.")
                    return
                elif 1 <= indice <= len(favoritos):
                    break
                else:
                    print("Número de favorito inválido. Digite um número válido.")
            except ValueError:
                print("Entrada inválida. Digite um número válido.")

        favorito_selecionado = favoritos[indice - 1]
        mycol.delete_one(favorito_selecionado)
        print("Favorito removido com sucesso!")
    else:
        print("O usuário não possui favoritos.")




def listar_produtos():
    global db
    print("Lista de produtos:")
    produtos = list(db.produto.find())
    for i, produto in enumerate(produtos, start=1):
        vendedor = db.vendedor.find_one({"cpf": produto.get("vendedor")})
        if vendedor:
            print(f"{i} - ID: {produto['_id']} | Produto: {produto['nome']} | Vendedor: {vendedor['nome']} | Preço: {produto['preço']}")
        else:
            print(f"{i} - ID: {produto['_id']} | Produto: {produto['nome']} | Vendedor: Não disponível | Preço: {produto['preço']}")

def adicionarnovo_favorito():
    global db
    while True:
        cpf_usuario = input("Digite o CPF do usuário: ")
        if not db.usuario.find_one({"cpf": cpf_usuario}):
            print("Erro: CPF de usuário não encontrado.")
            break

        print("\nLista de produtos:")
        produtos = list(db.produto.find())
        listar_produtos()

        id_produto = input("Digite o número do produto que deseja adicionar aos favoritos (ou 'V' para voltar): ")
        if id_produto.upper() == 'V':
            return

        try:
            id_produto = int(id_produto)
            if id_produto < 1 or id_produto > len(produtos):
                raise ValueError
        except ValueError:
            print("Erro: Entrada inválida. Digite um número válido.")
            continue

        produto_selecionado = produtos[id_produto - 1]
        adicionar_favorito(cpf_usuario, produto_selecionado["_id"])

        adicionar_mais = input("Deseja adicionar mais produtos aos favoritos (S/N)? ").upper()
        if adicionar_mais != "S":
            break

def adicionar_favorito(cpf_usuario, id_produto):
    global db
    usuario_collection = db.usuario
    favoritos_collection = db.favoritos

    usuario = usuario_collection.find_one({"cpf": cpf_usuario})
    if not usuario:
        print("Erro: Usuário não encontrado.")
        return

    # Adiciona o favorito à coleção de favoritos
    favorito = {"cpf_usuario": cpf_usuario, "id_produto": id_produto}
    favoritos_collection.insert_one(favorito)
    print("Produto adicionado aos favoritos do usuário com sucesso!")

    # Atualiza o documento do usuário com o novo favorito
    usuario_collection.update_one(
        {"cpf": cpf_usuario},
        {"$push": {"favorito": id_produto}}
    )


