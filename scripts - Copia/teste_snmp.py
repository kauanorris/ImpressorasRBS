import asyncio
from pysnmp.hlapi.v1arch.asyncio import *


async def testar():
    with SnmpDispatcher() as snmp:
        resultado = await get_cmd(
            snmp,
            CommunityData("public"),
            await UdpTransportTarget.create(
                ("10.100.0.1", 161),
                timeout=2,
                retries=1
            ),
            ("1.3.6.1.2.1.1.1.0", None)
        )

        erro, status, indice, dados = resultado

        if erro:
            print("❌ SNMP não respondeu:", erro)

        elif status:
            print("❌ Erro SNMP:", status.prettyPrint())

        else:
            print("✅ IMPRESSORA RESPONDEU VIA SNMP!")

            for item in dados:
                print(item)


asyncio.run(testar())