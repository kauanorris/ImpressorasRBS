import asyncio
from pysnmp.hlapi.v1arch.asyncio import *


async def testar():

    ip = "10.52.0.3"

    with SnmpDispatcher() as snmp:

        transporte = await UdpTransportTarget.create(
            (ip, 161),
            timeout=2,
            retries=1
        )

        oid_base = "1.3.6.1.4.1.1347.43.12"

        print("Testando impressora:", ip)
        print("OID:", oid_base)
        print("-" * 60)

        async for erro, status, indice, dados in walk_cmd(
            snmp,
            CommunityData("public"),
            transporte,
            (oid_base, None)
        ):

            if erro:
                print("ERRO:", erro)
                break

            if status:
                print(
                    "ERRO:",
                    status.prettyPrint()
                )
                break

            for oid, valor in dados:

                texto_oid = oid.prettyPrint()

                if not texto_oid.startswith(oid_base):
                    return

                print(
                    texto_oid,
                    "=",
                    valor.prettyPrint()
                )


asyncio.run(testar())