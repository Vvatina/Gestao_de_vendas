# PT- Sistema de Gestão de Maquilhagem
status:Finalizada (melhorias a serem comitadas)

Aplicação desktop em Python com Tkinter e SQLite, usada para gerir clientes, produtos, funcionários e encomendas.

## Funcionalidades:

- Login com utilizadores (admin e funcionários)

- Gestão de clientes

- Gestão de produtos (inclui controlo de stock)

- Gestão de funcionários (apenas Admin)

- Registo de encomendas

- Consulta e detalhes das encomendas

- Pesquisa rápida em todas as listas

## Tecnologias:

- Python 3

- Tkinter (interface gráfica)

- SQLite3 (base de dados local)

- Pillow / PIL (imagens)

- hashlib (hash de password)

## Instalação:

- Instale as dependências necessárias:
- pip install pillow


Certifique-se de que a pasta icons/ existe com as imagens:

icons/
  logo.png
  clientes.png
  produtos.png
  funcionarios.png
  encomendas.png
  logout.png


### Execute o programa:

python gestao_de_maquilhagem.py

Login inicial no sistema com o administrador criado automaticamente: Utilizador: admin Senha: admin123

Observações:

A base de dados maquilhagem.db é criada automaticamente.

Apenas o administrador pode remover funcionários, produtos e clientes.

Stock é atualizado automaticamente ao criar e apagar encomendas.
