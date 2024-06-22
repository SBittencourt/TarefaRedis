from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi



uri = "mongodb+srv://silmara:123@cluster0.05p7qyc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(uri, server_api=ServerApi('1'))
global db
db = client.mercadolivre

def delete_usuario(nome, sobrenome):
    global db
    mycol = db.usuario
    myquery = {"nome": nome, "sobrenome":sobrenome}
    mydoc = mycol.delete_one(myquery)
    print("Deletado o usuário ",mydoc)

def create_usuario():
    global db
    mycol = db.usuario
    print("\nInserindo um novo usuário")
    nomeUsuario = input("Nome: ")
    sobrenome = input("Sobrenome: ")
    telefone = input("Telefone: ")
    email = input("Email: ")
    cpf = input("CPF: ")
    key = 'S'  
    end = []
    while key.upper() != 'N':  
        rua = input("Rua: ")
        num = input("Num: ")
        bairro = input("Bairro: ")
        cidade = input("Cidade: ")
        estado = input("Estado: ")
        cep = input("CEP: ")
        endereco = {       
            "rua":rua,
            "num": num,
            "bairro": bairro,
            "cidade": cidade,
            "estado": estado,
            "cep": cep
        }
        end.append(endereco) 
        key = input("Deseja cadastrar um novo endereço (S/N)? ").upper()  
    mydoc = { "nome": nomeUsuario, "sobrenome": sobrenome, "cpf": cpf, "end": end, "favorito": [] }
    x = mycol.insert_one(mydoc)
    print("Documento inserido com ID ",x.inserted_id)



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

def ver_compras_realizadas(cpf_usuario):
    global db
    print("Compras realizadas pelo usuário:")
    
    compras_realizadas = db.compras.find({"cpf_usuario": cpf_usuario})
    
    count = 0

    for compra in compras_realizadas:
        count += 1
        print(f"ID da Compra: {compra['_id']}")
        print("Produtos:")
        for produto in compra['produtos']:
            print(f"   Nome do Produto: {produto['nome']} | Preço: {produto['preço']}")
        print(f"Endereço de Entrega: {compra['endereco_entrega']}")
        print("----")
    
    if count == 0:
        print("Nenhuma compra encontrada para este usuário.")

# Voltando ao read_usuario

def read_usuario(nomeUsuario):
    global db
    mycol_usuario = db.usuario
    print("Informações do usuário:")
    if not len(nomeUsuario):
        mydoc_usuario = mycol_usuario.find().sort("nome")
        for user in mydoc_usuario:
            print("Nome:", user["nome"])
            print("CPF:", user["cpf"])
            print("Endereços:")
            for endereco in user["end"]:
                print("Rua:", endereco["rua"])
                print("Número:", endereco["num"])
                print("Bairro:", endereco["bairro"])
                print("Cidade:", endereco["cidade"])
                print("Estado:", endereco["estado"])
                print("CEP:", endereco["cep"])
            print("Favoritos:")
            visualizar_favoritos(user["cpf"])
            print("Compras Realizadas:")
            ver_compras_realizadas(user["cpf"])
            print("----")
    else:
        myquery_usuario = {"nome": nomeUsuario}
        mydoc_usuario = mycol_usuario.find(myquery_usuario)
        for user in mydoc_usuario:
            print("Nome:", user["nome"])
            print("CPF:", user["cpf"])
            print("Endereços:")
            for endereco in user["end"]:
                print("Rua:", endereco["rua"])
                print("Número:", endereco["num"])
                print("Bairro:", endereco["bairro"])
                print("Cidade:", endereco["cidade"])
                print("Estado:", endereco["estado"])
                print("CEP:", endereco["cep"])
            visualizar_favoritos(user["cpf"])
            ver_compras_realizadas(user["cpf"])


def update_usuario(nomeUsuario):
    global db
    mycol = db.usuario
    myquery = {"nome": nomeUsuario}
    mydoc = mycol.find_one(myquery)
    print("Dados do usuário: ", mydoc)

    print("\nMenu de opções:")
    print("1 - Mudar Nome")
    print("2 - Mudar Sobrenome")
    print("3 - Mudar CPF")
    print("4 - Mudar Telefone")
    print("5 - Mudar Email")
    print("6 - Mudar Endereço")
    print("7 - Voltar ao menu principal")

    while True:
        opcao = input("\nEscolha uma opção: ")

        if opcao == "1":
            nome = input("Novo Nome: ")
            if nome:
                mydoc["nome"] = nome
        elif opcao == "2":
            sobrenome = input("Novo Sobrenome: ")
            if sobrenome:
                mydoc["sobrenome"] = sobrenome
        elif opcao == "3":
            cpf = input("Novo CPF: ")
            if cpf:
                mydoc["cpf"] = cpf
        elif opcao == "4":
            telefone = input("Novo Telefone: ")
            if telefone:
                mydoc["telefone"] = telefone
        elif opcao == "5":
            email = input("Novo Email: ")
            if email:
                mydoc["email"] = email
        elif opcao == "6":
            print("\nEndereço atual:")
            for endereco in mydoc["end"]:
                print("Rua:", endereco["rua"])
                print("Número:", endereco["num"])
                print("Bairro:", endereco["bairro"])
                print("Cidade:", endereco["cidade"])
                print("Estado:", endereco["estado"])
                print("CEP:", endereco["cep"])
            rua = input("\nNova Rua: ")
            num = input("Novo Número: ")
            bairro = input("Novo Bairro: ")
            cidade = input("Nova Cidade: ")
            estado = input("Novo Estado: ")
            cep = input("Novo CEP: ")
            endereco = {
                "rua": rua,
                "num": num,
                "bairro": bairro,
                "cidade": cidade,
                "estado": estado,
                "cep": cep
            }
            mydoc["end"] = [endereco]
        elif opcao == "7":
            print("Retornando ao menu principal...")
            break
        else:
            print("Opção inválida. Por favor, escolha uma opção válida.")

    newvalues = {"$set": mydoc}
    mycol.update_one(myquery, newvalues)
