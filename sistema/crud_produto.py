import pymongo

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://silmara:123@cluster0.05p7qyc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(uri, server_api=ServerApi('1'))
global db
db = client.mercadolivre

def delete_produto(nomeProduto): 
    global db
    mycol = db.produto
    myquery = {"nome": nomeProduto}  
    mydoc = mycol.delete_one(myquery)
    print("Deletado o produto ", mydoc)

def create_produto():
    global db
    mycol = db.produto
    print("\nInserindo um novo produto")
    nomeProduto = input("Nome: ")
    preco = input("Preço: ")
    marca = input("Marca: ")

    print("Vendedores existentes:")
    for vendedor in db.vendedor.find():
        print("- Nome:", vendedor["nome"], "| CPF:", vendedor["cpf"])

    cpfVendedor = input("Digite o CPF do vendedor para associar ao produto: ")

    vendedor_existente = db.vendedor.find_one({"cpf": cpfVendedor})
    if not vendedor_existente:
        print("Vendedor com o CPF", cpfVendedor, "não encontrado. Produto não foi criado.")
        return

    mydoc = { "nome": nomeProduto, "preço": preco, "marca": marca, "vendedor": cpfVendedor }
    x = mycol.insert_one(mydoc)
    print("Documento inserido com ID ",x.inserted_id)


def read_produto(nomeProduto):
    global db
    mycol = db.produto
    print("Produtos existentes: ")
    if not len(nomeProduto):
        mydoc = mycol.find().sort("nome")
        for x in mydoc:
            print(x["nome"])
    else:
        myquery = {"nome": nomeProduto}
        mydoc = mycol.find(myquery)
        for x in mydoc:
            print(x)

def update_produto(nomeProduto):
    global db
    mycol = db.produto
    myquery = {"nome": nomeProduto}
    mydoc = mycol.find_one(myquery)
    if mydoc:
        print("Dados do produto: ", mydoc)
        novo_nome = input("Mudar nome do produto:")
        if novo_nome:
            mydoc["nome"] = novo_nome

        novo_preco = input("Mudar preço:")
        if novo_preco:
            mydoc["preço"] = novo_preco

        nova_marca = input("Mudar marca:")
        if nova_marca:
            mydoc["marca"] = nova_marca

        print("Vendedores existentes:")
        for vendedor in db.vendedor.find():
            print("- Nome:", vendedor["nome"], "| CPF:", vendedor["cpf"])

        cpfVendedor = input("Digite o novo CPF do vendedor para associar ao produto: ")

        vendedor_existente = db.vendedor.find_one({"cpf": cpfVendedor})
        if not vendedor_existente:
            print("Vendedor com o CPF", cpfVendedor, "não encontrado. Produto não foi atualizado.")
            return

        mydoc["vendedor"] = cpfVendedor

        newvalues = { "$set": mydoc }
        mycol.update_one(myquery, newvalues)
        print("Produto atualizado com sucesso!")
    else:
        print("Produto não encontrado.")
