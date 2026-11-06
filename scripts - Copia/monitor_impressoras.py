impressoras = [
    {"nome": "Controladoria", "ip": "10.0.0.14", "toner": 8},
    {"nome": "RH", "ip": "10.0.0.20", "toner": 65},
    {"nome": "Financeiro", "ip": "10.0.0.25", "toner": 18}
]

for impressora in impressoras:
    print(
        impressora["nome"],
        "-",
        impressora["ip"],
        "- Toner:",
        impressora["toner"],
        "%"
    )

    if impressora["toner"] <= 10:
       print("🔴 CRÍTICO: trocar toner em breve!")

    elif impressora["toner"] < 20:
      print("🟡 ATENÇÃO: toner acabando!")

    else:
       print("🟢 OK: nível de toner normal")