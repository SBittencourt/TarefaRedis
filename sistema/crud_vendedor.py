from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://silmara:123@cluster0.05p7qyc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(uri, server_api=ServerApi('1'))
global db
db = client.mercadolivre

def delete_vendedor(nome, cpf):
    global db
    mycol = db.vendedor
    myquery = {"nome": nome, "cpf": cpf}
    mydoc = mycol.delete_one(myquery)
    print("Vendedor deletado ", mydoc.deleted_count)

def create_vendedor():
    global db
    mycol = db.vendedor
    print("\nInserindo um novo vendedor")
    nome = input("Nome: ")
    cpf = input("CPF: ")
    telefone = input("Telefone: ")
    email = input("Email: ")
    
    key = 'S'
    enderecos = []
    while key.upper() == 'S':
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
        key = input("Deseja adicionar outro endereço (S/N)? ")

    mydoc = {
        "nome": nome,
        "cpf": cpf,
        "telefone": telefone,
        "email": email,
        "enderecos": enderecos
    }

    x = mycol.insert_one(mydoc)
    print("Vendedor inserido com ID ", x.inserted_id)

def read_vendedor(nome):
    global db
    mycol = db.vendedor
    print("Vendedores existentes: ")
    if not len(nome):
        mydoc = mycol.find().sort("nome")
        for x in mydoc:
            print(x["nome"], x["cpf"])
    else:
        myquery = {"nome": nome}
        mydoc = mycol.find(myquery)
        for x in mydoc:
            print(x)

def update_vendedor(nome):
    global db
    mycol = db.vendedor
    myquery = {"nome": nome}
    mydoc = mycol.find_one(myquery)
    print("Dados do vendedor: ", mydoc)
    novo_nome = input("Novo nome: ")
    if novo_nome:
        mydoc["nome"] = novo_nome

    cpf = input("Novo CPF: ")
    if cpf:
        mydoc["cpf"] = cpf

    telefone = input("Novo telefone: ")
    if telefone:
        mydoc["telefone"] = telefone

    email = input("Novo email: ")
    if email:
        mydoc["email"] = email

    newvalues = {"$set": mydoc}
    mycol.update_one(myquery, newvalues)
    print("Vendedor atualizado com sucesso!")
