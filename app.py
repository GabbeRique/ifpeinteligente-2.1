from flask import Flask, render_template, request, redirect, session, url_for
from firebase_config import auth, db
import requests
import json

app = Flask(__name__)
app.secret_key = "chave-super-secreta-do-gabriel"

API_KEY = "AIzaSyA23RqXJ2Z92E-B19hajBi5uumh6XbGvpw"


# ========== FUNÇÃO LOGIN FIREBASE ==========
def login_firebase(email, senha):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
    
    payload = {
        "email": email,
        "password": senha,
        "returnSecureToken": True
    }

    r = requests.post(url, json=payload)
    return r.json()


# ========== TELA INICIAL ==========
@app.route("/")
def index():
    return render_template("telainicial.html")   # <<< PRIMEIRA TELA


# ========== CRIAR CONTA ==========
@app.route("/criarconta", methods=["GET", "POST"])
def criarconta():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]
        serie = request.form["serie"]
        curso = request.form["curso"]

        try:
            user = auth.create_user(
                email=email,
                password=senha,
                display_name=nome
            )

            db.collection("usuarios").document(user.uid).set({
                "nome": nome,
                "email": email,
                "pontos": 0,
                "curso": curso,
                "turma": serie,
                "locais_visitados": []
            })

            return redirect("/login")

        except Exception as e:
            return f"Erro ao criar conta: {e}"

    return render_template("criarconta.html")


# ========== LOGIN ==========
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        resultado = login_firebase(email, senha)

        if "localId" in resultado:  # login correto
            session["user"] = resultado["localId"]
            return redirect("/home")
        else:
            return "Email ou senha incorretos."

    return render_template("telalogin.html")


# ============ HOME ============
@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/login")
    return render_template("home.html")


# ============ PERFIL ============
@app.route("/perfil")
def perfil():
    if "user" not in session:
        return redirect("/login")

    user_id = session["user"]

    dados = db.collection("usuarios").document(user_id).get()

    if dados.exists:
        usuario = dados.to_dict()
    else:
        usuario = {
            "nome": "Não encontrado",
            "curso": "Não informado",
            "turma": "Não informado",
            "pontos": 0,
            "flow_visitas": 0,
            "helpme_interacoes": 0
        }

    return render_template("perfil.html", usuario=usuario)


# ============ OUTRAS ROTAS ============
@app.route("/config")
def configuracoes():
    if "user" not in session:
        return redirect("/login")
    return render_template("configuracoes.html")


@app.route("/ifpeflow")
def ifpeflow():
    if "user" not in session:
        return redirect("/login")
    return render_template("ifpeflow.html")


@app.route("/ecoscan")
def ecoscan():
    if "user" not in session:
        return redirect("/login")
    return render_template("ecoscan.html")


# ============ LOGOUT ============
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/registrar_lixo", methods=["POST"])
def registrar_lixo():
    if "user" not in session:
        return {"erro": "não logado"}, 403

    user_id = session["user"]
    dados = request.get_json()

    tipo = dados["tipo"]
    quantidade = int(dados["quantidade"])

    multiplicador = 1 # você disse: 1 lixo = 2 pontos
    pontos = quantidade * multiplicador

    usuario_ref = db.collection("usuarios").document(user_id)
    usuario_data = usuario_ref.get().to_dict()

    novo_total = usuario_data.get("pontos", 0) + pontos

    usuario_ref.update({"pontos": novo_total})

    return {"status": "ok", "pontos_adicionados": pontos, "novo_total": novo_total}


if __name__ == "__main__":
    app.run(debug=True)
