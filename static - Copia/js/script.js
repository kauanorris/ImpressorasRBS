  
/* ======================================================
HORÁRIO
====================================================== */

function atualizarHorario() {
    const elemento = document.getElementById("horario");

    if (elemento) {
        elemento.textContent = new Date().toLocaleString("pt-BR");
    }
}

atualizarHorario();

            // Mantém os indicadores do painel alinhados como no layout de referência.
            (function aplicarLayoutResumo() {
                const estilo = document.createElement("style");
                estilo.textContent = `
                    .cartoes {
                        display: grid !important;
                        grid-template-columns: repeat(4, minmax(0, 1fr));
                        gap: 24px;
                        align-items: start;
                        width: 100%;
                    }

                    .cartoes > * {
                        min-width: 0;
                    }

                    @media (max-width: 700px) {
                        .cartoes {
                            grid-template-columns: repeat(2, minmax(0, 1fr));
                            gap: 16px;
                        }
                    }

                    @media (max-width: 420px) {
                        .cartoes {
                            grid-template-columns: 1fr;
                        }
                    }
                `;
                document.head.appendChild(estilo);
            })();


            setInterval(
                atualizarHorario,
                30000
            );


            /* ======================================================
            RESUMO
            ====================================================== */

            async function atualizarResumo() {

                try {

                    const resposta = await fetch("/dados");

                    if (!resposta.ok) {

                        throw new Error(
                            "Erro HTTP " + resposta.status
                        );

                    }


                    const impressoras =
                        await resposta.json();


                    // ==================================================
                    // TOTAL DE IMPRESSORAS
                    // ==================================================

                    const total =
                        impressoras.length;


                    // ==================================================
                    // IMPRESSORAS ONLINE
                    // ==================================================

                    const online =
                        impressoras.filter(
                            impressora =>
                                impressora.status === "Online"
                        ).length;


                    // ==================================================
                    // IMPRESSORAS OFFLINE
                    // ==================================================

                    const offline =
                        impressoras.filter(
                            impressora =>
                                impressora.status !== "Online"
                        ).length;


                    // ==================================================
                    // TONER BAIXO
                    // ==================================================

                    const tonerBaixo =
                        impressoras.filter(
                            impressora => {

                                const toners = [

                                    impressora.ciano,
                                    impressora.magenta,
                                    impressora.amarelo,
                                    impressora.preto

                                ];


                                return toners.some(
                                    toner => {

                                        if (
                                            !toner ||
                                            toner === "-"
                                        ) {

                                            return false;

                                        }


                                        const valor =
                                            parseInt(
                                                String(toner)
                                                    .replace("%", "")
                                                    .trim()
                                            );


                                        return (
                                            !isNaN(valor) &&
                                            valor <= 7
                                        );

                                    }
                                );

                            }
                        ).length;


                    // ==================================================
                    // ATUALIZA OS CARTÕES DO PAINEL
                    // ==================================================

                    const totalElemento =
                        document.getElementById(
                            "total-impressoras"
                        );


                    const onlineElemento =
                        document.getElementById(
                            "online-impressoras"
                        );


                    const offlineElemento =
                        document.getElementById(
                            "offline-impressoras"
                        );


                    const tonerElemento =
                        document.getElementById(
                            "toner-baixo"
                        );


                    if (totalElemento) {

                        totalElemento.textContent =
                            total;

                    }


                    if (onlineElemento) {

                        onlineElemento.textContent =
                            online;

                    }


                    if (offlineElemento) {

                        offlineElemento.textContent =
                            offline;

                    }


                    if (tonerElemento) {

                        tonerElemento.textContent =
                            tonerBaixo;

                    }


                } catch (erro) {

                    console.error(
                        "Erro ao atualizar resumo:",
                        erro
                    );

                }

            }
            atualizarResumo();

            setInterval(
                atualizarResumo,
                30000
            );

           let secaoMenuAtiva = null;

           function alternarSecaoMenu(secao, abrir) {
                if (secaoMenuAtiva === secao) {
                    secaoMenuAtiva = null;
                    esconderAreas();
                    window.scrollTo({
                        top: 0,
                        behavior: "smooth"
                    });
                    return;
                }

                secaoMenuAtiva = secao;
                abrir();
            }

           function esconderAreas() {

                const ids = [
                    "area-pastas",
                    "area-lista",
                    "area-estoque",
                    "area-tabela-estoque",
                    "formulario-toner",
                    "formulario-saida-toner",
                    "area-historico"
                ];

                ids.forEach(function(id) {

                    const elemento =
                        document.getElementById(id);

                    if (elemento) {
                        elemento.style.display = "none";
                    }

                });


                // ==================================================
                // RESTAURA A TABELA PRINCIPAL
                // ==================================================

                const tabelaImpressoras =
                    document.getElementById(
                        "tabela-impressoras"
                    );

                if (tabelaImpressoras) {

                    tabelaImpressoras.style.display =
                        "table";

                }


                // ==================================================
                // ESCONDE A TABELA DE NÃO CONFIÁVEIS
                // ==================================================

                const areaNaoConfiaveis =
                    document.getElementById(
                        "area-nao-confiaveis"
                    );

                if (areaNaoConfiaveis) {

                    areaNaoConfiaveis.style.display =
                        "none";

                }


                // ==================================================
                // MOSTRA OS CARTÕES
                // ==================================================

                const cartoes =
                    document.querySelector(".cartoes");

                if (cartoes) {

                    cartoes.style.display =
                        "grid";

                }

            }
            /* ======================================================
                 BARRA DE PESQUISA  
            ====================================================== */
            function pesquisarImpressoras() {

                const campo =
                    document.getElementById("pesquisa");
                if (!campo)  return;

                const termo = campo.value.toLowerCase().trim();

                const lista = document.getElementById("area-lista"); 
                if (lista) {
                    lista.style.display= "block";
                    
                }
                const tabela =document.getElementById("tabela-impressoras");
                if (tabela){
                    tabela.style.display="table";

                }
                const linhas = document.querySelectorAll
                ("#corpo-tabela-impressoras tr");
                linhas.forEach(function(linha) {

                    
                
                    
            
                    const grupo = (linha.getAttribute("data-grupo") || ""
                    ) .toLowerCase();
                    const ip =( linha.getAttribute("data-ip") || ""
                    ).toLowerCase();
                    const modelo = (linha.getAttribute("data-modelo") || ""
                    ) .toLowerCase();
                    const patrimonio= (linha.getAttribute("data-patrimonio") || ""
                    ).toLowerCase();


                    if (ip.includes(termo) || modelo.includes(termo) || patrimonio.includes(termo)|| grupo.includes(termo)) {
                        linha.style.display = "";
                    } else {
                        linha.style.display = "none";
                    } 
                })
            }





            /* ==================================================
            IMPRESSORAS
            ================================================== */

            function abrirImpressoras() {

                esconderAreas();

                const pastas =
                    document.getElementById("area-pastas");

                if (!pastas) {

                    console.error(
                        "ERRO: area-pastas não encontrada."
                    );

                    return;
                }

                pastas.style.display = "block";

                window.scrollTo({
                    top: pastas.offsetTop - 20,
                    behavior: "smooth"
                });
            }


            /* ==================================================
            ABRIR PASTAS / SETOR
            ================================================== */

            function abrirPastas(grupo) {

                esconderAreas();

                const lista =
                    document.getElementById("area-lista");

                if (!lista) {

                    console.error(
                        "ERRO: area-lista não encontrada."
                    );

                    return;
                }

                lista.style.display = "block";

                const titulo =
                    document.getElementById("titulo-grupo");

                if (titulo) {

                    titulo.textContent =
                        "📁 " + grupo;

                }

                const linhas =
                    document.querySelectorAll(
                        "#area-lista tr[data-grupo]"
                    );

                linhas.forEach(function(linha) {

                    const grupoLinha =
                        linha.getAttribute("data-grupo");

                    linha.style.display =
                        grupoLinha === grupo
                            ? ""
                            : "none";

                });

                const pesquisa =
                    document.getElementById("pesquisa");

                if (pesquisa) {
                    pesquisa.value = "";
                }

                window.scrollTo({
                    top: lista.offsetTop - 20,
                    behavior: "smooth"
                });
            }


            /* ==================================================
            VOLTAR AO INÍCIO
            ================================================== */

            function voltarInicio() {

                esconderAreas();

                window.scrollTo({
                    top: 0,
                    behavior: "smooth"
                });
            }


            /* ==================================================
            IMPRESSORAS 
            ================================================== */

            function carregar_offline() {

                esconderAreas();

                const lista =
                    document.getElementById("area-lista");

                if (!lista) {

                    console.error(
                        "ERRO: area-lista não encontrada."
                    );

                    return;
                }

                lista.style.display = "block";

                const titulo =
                    document.getElementById("titulo-grupo");

                if (titulo) {

                    titulo.textContent =
                        "🔴 Impressoras Offline";

                }

                const linhas =
                    document.querySelectorAll(
                        "#area-lista tr[data-status]"
                    );

                let quantidadeOffline = 0;

                linhas.forEach(function(linha) {

                    const status =
                        (
                            linha.getAttribute("data-status") || ""
                        )
                        .trim()
                        .toLowerCase();

                    if (status === "offline") {

                        linha.style.display = "";

                        quantidadeOffline++;

                    } else {

                        linha.style.display = "none";

                    }

                });

                console.log(
                    "Impressoras offline encontradas:",
                    quantidadeOffline
                );

                const pesquisa =
                    document.getElementById("pesquisa");

                if (pesquisa) {
                    pesquisa.value = "";
                }

                window.scrollTo({
                    top: lista.offsetTop - 20,
                    behavior: "smooth"
                });
            }
            
            function fecharOffline() {

                esconderAreas();

                window.scrollTo({
                    top: 0,
                    behavior: "smooth"
                });
            }

            /* ==================================================
            TONERS BAIXOS
             ================================================== */
            async function mostrarTonerBaixo() {

                esconderAreas();

                const lista = document.getElementById("area-lista");

                if (!lista) {
                    console.error("ERRO: area-lista não encontrada.");
                    return;
                }

                lista.style.display = "block";

                const titulo = document.getElementById("titulo-grupo");

                if (titulo) {
                    titulo.textContent = "⚠️ Toners baixos";
                }

                try {

                    // Busca os toners classificados como não confiáveis
                    const resposta = await fetch("/toners-nao-confiaveis");

                    if (!resposta.ok) {
                        throw new Error("Erro HTTP " + resposta.status);
                    }

                    const naoConfiaveis = await resposta.json();

                    const linhas = document.querySelectorAll(
                        "#corpo-tabela-impressoras tr"
                    );

                    linhas.forEach(function(linha) {

                        const ip = (
                            linha.getAttribute("data-ip") || ""
                        ).trim();

                        let existeTonerBaixoConfiavel = false;

                        const barras = linha.querySelectorAll(
                            ".toner-bar"
                        );

                        barras.forEach(function(barra) {

                            const nomeToner = (
                                barra.getAttribute("data-toner") || ""
                            ).trim();

                            const barraPercentual =
                                barra.querySelector(".progress-bar");

                            if (!barraPercentual) {
                                return;
                            }

                            const texto = barraPercentual.textContent
                                .replace("%", "")
                                .trim();

                            const valor = parseInt(texto, 10);

                            if (
                                isNaN(valor) ||
                                valor < 0 ||
                                valor > 7
                            ) {
                                return;
                            }

                            // Verifica se este toner específico
                            // já foi classificado como não confiável
                            const ehNaoConfiavel =
                                naoConfiaveis.some(function(toner) {

                                    const ipToner =
                                        String(toner.ip || "").trim();

                                    const nomeTonerHistorico =
                                        String(toner.toner || "")
                                            .trim()
                                            .toLowerCase();

                                    return (
                                        ipToner === ip &&
                                        nomeTonerHistorico ===
                                            nomeToner.toLowerCase()
                                    );
                                });

                            // Só considera toner baixo se
                            // NÃO for um toner não confiável
                            if (!ehNaoConfiavel) {
                                existeTonerBaixoConfiavel = true;
                            }

                        });

                        if (existeTonerBaixoConfiavel) {
                            linha.style.display = "";
                        } else {
                            linha.style.display = "none";
                        }

                    });

                } catch (erro) {

                    console.error(
                        "Erro ao carregar toners baixos:",
                        erro
                    );

                }

                window.scrollTo({
                    top: lista.offsetTop - 20,
                    behavior: "smooth"
                });
            }


            function abrirAbaEstoque(aba) {

                const tabelaEstoque =
                    document.getElementById("area-tabela-estoque");

                const formularioToner =
                    document.getElementById("formulario-toner");

                const formularioSaida =
                    document.getElementById("formulario-saida-toner");


                // Esconde todas as áreas

                if (tabelaEstoque) {
                    tabelaEstoque.style.display = "none";
                }

                if (formularioToner) {
                    formularioToner.style.display = "none";
                }

                if (formularioSaida) {
                    formularioSaida.style.display = "none";
                }


                // Remove seleção das abas

                document
                    .querySelectorAll(".aba-estoque")
                    .forEach(function(botao) {

                        botao.classList.remove("ativa");
                        botao.setAttribute("aria-selected", "false");

                    });


                // ESTOQUE

                if (aba === "estoque") {

                    if (tabelaEstoque) {
                        tabelaEstoque.style.display = "block";
                    }

                    const botao = document.querySelector(
                        '.aba-estoque[data-aba="estoque"]'
                    );

                    if (botao) {
                        botao.classList.add("ativa");
                        botao.setAttribute("aria-selected", "true");
                    }

                    mostrarEstoque();

                }


                // CADASTRO DE TONER

                if (aba === "cadastro") {

                    if (formularioToner) {
                        formularioToner.style.display = "block";
                    }

                    const botao = document.querySelector(
                        '.aba-estoque[data-aba="cadastro"]'
                    );

                    if (botao) {
                        botao.classList.add("ativa");
                        botao.setAttribute("aria-selected", "true");
                    }

                }


                // SAÍDAS

                if (aba === "saidas") {

                    if (formularioSaida) {
                        formularioSaida.style.display = "block";
                    }

                    const botao = document.querySelector(
                        '.aba-estoque[data-aba="saidas"]'
                    );

                    if (botao) {
                        botao.classList.add("ativa");
                        botao.setAttribute("aria-selected", "true");
                    }

                }
            }

            async function mostrarEstoque() {

                esconderAreas();

                document.getElementById(
                    "area-estoque"
                ).style.display = "block";


                document.getElementById(
                    "formulario-toner"
                ).style.display = "none";

                document.getElementById(
                    "formulario-saida-toner"
                ).style.display = "none";


                const areaTabela =
                    document.getElementById(
                        "area-tabela-estoque"
                    );

                areaTabela.style.display = "block";

                document
                    .querySelectorAll(".aba-estoque")
                    .forEach(function(botao) {
                        const selecionada =
                            botao.dataset.aba === "estoque";

                        botao.classList.toggle("ativa", selecionada);
                        botao.setAttribute(
                            "aria-selected",
                            String(selecionada)
                        );
                    });

                const tabela = document.getElementById(
                    "corpo-tabela-estoque"
                );
                const mostrarInativos = document.getElementById(
                    "mostrar-toners-inativos"
                );
                const incluirInativos =
                    localStorage.getItem("mostrar_toners_inativos") === "1";
                if (mostrarInativos) {
                    mostrarInativos.checked = incluirInativos;
                }

                tabela.innerHTML = `

                    <tr>

                        <td
                            colspan="8"
                            class="text-center">

                            Carregando estoque...

                        </td>

                    </tr>

                `;


                try {

                    const resposta =
                        await fetch(
                            "/estoque?incluir_inativos=" +
                            (incluirInativos ? "1" : "0")
                        );


                    if (!resposta.ok) {

                        throw new Error(
                            "Erro HTTP " +
                            resposta.status
                        );

                    }


                    const toners =
                        await resposta.json();


                    tabela.innerHTML = "";


                    if (!toners.length) {

                        tabela.innerHTML = `

                            <tr>

                                <td
                                    colspan="8"
                                    class="text-center">

                                    Nenhum toner cadastrado.

                                </td>

                            </tr>

                        `;


                        return;

                    }


                    toners.forEach(
                        function(toner) {

                            let situacao;

                            if (!toner.ativo) {
                                situacao = `
                                    <span class="badge bg-secondary">
                                        Inativo
                                    </span>
                                `;
                            } else if (
                                toner.estoque <=
                                toner.estoque_minimo
                            ) {

                                situacao = `

                                    <span
                                        class="badge bg-danger">

                                        Estoque baixo

                                    </span>

                                `;

                            } else {

                                situacao = `

                                    <span
                                        class="badge bg-success">

                                        OK

                                    </span>

                                `;

                            }


                            tabela.innerHTML += `

                                <tr class="${toner.ativo ? "" : "table-secondary"}">

                                    <td>
                                        ${escaparHtml(toner.marca)}
                                    </td>

                                    <td>
                                        ${escaparHtml(toner.codigo)}
                                    </td>

                                    <td>
                                        <span id="modelos-toner-${toner.id}">${escaparHtml(toner.modelos_compativeis || "Não configurado")}</span>
                                        <button
                                            class="btn btn-sm btn-outline-primary ms-1"
                                            onclick="editarModelosCompativeis(${toner.id})">
                                            Editar
                                        </button>
                                    </td>

                                    <td>
                                        ${escaparHtml(toner.cor)}
                                    </td>

                                    <td>
                                        <div class="d-flex align-items-center gap-2">

                                            <button
                                                type="button"
                                                class="btn btn-sm btn-outline-danger"
                                                title="Retirar uma unidade"
                                                onclick="alterarEstoqueRapido(${toner.id}, 'saida')">
                                                −
                                            </button>

                                            <strong style="min-width: 25px; text-align: center;">
                                                ${toner.estoque}
                                            </strong>

                                            <button
                                                type="button"
                                                class="btn btn-sm btn-outline-success"
                                                title="Adicionar uma unidade"
                                                onclick="alterarEstoqueRapido(${toner.id}, 'entrada')">
                                                +
                                            </button>

                                        </div>
                                    </td>

                                    <td>
                                        ${toner.estoque_minimo}
                                    </td>

                                    <td>
                                        ${situacao}
                                    </td>
                                    <td>
                                        ${
                                            toner.ativo
                                                ? `<button class="btn btn-sm btn-danger" onclick="removerToner(${toner.id})">Remover</button>`
                                                : `<button class="btn btn-sm btn-success" onclick="reativarToner(${toner.id})">Reativar</button>`
                                        }
                                    </td>

                                </tr>

                            `;

                        }
                    );


                } catch (erro) {

                    console.error(
                        "Erro ao carregar estoque:",
                        erro
                    );


                    tabela.innerHTML = `

                        <tr>

                            <td
                                colspan="8"
                                class="text-center text-danger">

                                Erro ao carregar o estoque.

                            </td>

                        </tr>

                    `;

                }


                window.scrollTo({

                    top:
                        document.getElementById(
                            "area-estoque"
                        ).offsetTop - 20,

                    behavior: "smooth"

                });

            }

            function escaparHtml(valor) {
                const entidades = {
                    "&": "&amp;",
                    "<": "&lt;",
                    ">": "&gt;",
                    '"': "&quot;",
                    "'": "&#39;"
                };
                return String(valor == null ? "" : valor).replace(
                    /[&<>"']/g,
                    caracter => entidades[caracter]
                );
            }

            function definirTonersInativos(exibir) {
                localStorage.setItem(
                    "mostrar_toners_inativos",
                    exibir ? "1" : "0"
                );
                mostrarEstoque();
            }

            async function editarModelosCompativeis(tonerId) {
                const elemento = document.getElementById(
                    "modelos-toner-" + tonerId
                );
                const atuais =
                    elemento.textContent === "Não configurado"
                        ? ""
                        : elemento.textContent;
                const modelos = prompt(
                    "Informe os modelos compatíveis separados por vírgula:",
                    atuais
                );
                if (modelos === null) {
                    return;
                }

                try {
                    const resposta = await fetch(
                        "/toner/" + tonerId + "/modelos-compativeis",
                        {
                            method: "PUT",
                            headers: {"Content-Type": "application/json"},
                            body: JSON.stringify({
                                modelos_compativeis: modelos
                            })
                        }
                    );
                    const resultado = await resposta.json();
                    if (!resposta.ok) {
                        alert(resultado.erro || "Não foi possível atualizar os modelos.");
                        return;
                    }
                    mostrarEstoque();
                } catch (erro) {
                    console.error("Erro ao atualizar modelos compatíveis:", erro);
                    alert("Erro de comunicação com o servidor.");
                }
            }

            async function reativarToner(tonerId) {
                try {
                    const resposta = await fetch(
                        "/reativar-toner/" + tonerId,
                        {method: "POST"}
                    );
                    const resultado = await resposta.json();
                    if (!resposta.ok) {
                        alert(resultado.erro || "Não foi possível reativar o toner.");
                        return;
                    }
                    mostrarEstoque();
                } catch (erro) {
                    console.error("Erro ao reativar toner:", erro);
                    alert("Erro de comunicação com o servidor.");
                }
            }


            async function mostrarTonersNaoConfiaveis() {

                esconderAreas();

                const lista =
                    document.getElementById("area-lista");

                if (!lista) {
                    return;
                }

                lista.style.display = "block";

                const titulo =
                    document.getElementById("titulo-grupo");

                if (titulo) {
                    titulo.textContent =
                        "⚠️ Toners não confiáveis";
                }


                // ==================================================
                // ESCONDE A TABELA PRINCIPAL
                // ==================================================

                const tabelaImpressoras =
                    document.getElementById(
                        "tabela-impressoras"
                    );

                if (tabelaImpressoras) {
                    tabelaImpressoras.style.display = "none";
                }


                // ==================================================
                // MOSTRA A TABELA DE NÃO CONFIÁVEIS
                // ==================================================

                const areaNaoConfiaveis =
                    document.getElementById(
                        "area-nao-confiaveis"
                    );

                if (!areaNaoConfiaveis) {
                    console.error(
                        "ERRO: area-nao-confiaveis não encontrada."
                    );
                    return;
                }

                areaNaoConfiaveis.style.display = "block";


                const tabela =
                    document.getElementById(
                        "corpo-nao-confiaveis"
                    );

                if (!tabela) {
                    console.error(
                        "ERRO: corpo-nao-confiaveis não encontrado."
                    );
                    return;
                }


                try {

                    const resposta =
                        await fetch(
                            "/toners-nao-confiaveis"
                        );


                    if (!resposta.ok) {

                        throw new Error(
                            "Erro HTTP " +
                            resposta.status
                        );

                    }


                    const toners =
                        await resposta.json();


                    // Limpa SOMENTE a tabela
                    // de toners não confiáveis

                    tabela.innerHTML = "";


                    if (!toners.length) {

                        tabela.innerHTML = `
                            <tr>
                                <td colspan="5"
                                    class="text-center">

                                    Nenhum toner não confiável encontrado.

                                </td>
                            </tr>
                        `;

                        return;
                    }


                    toners.forEach(function(toner) {

                        tabela.innerHTML += `
                            <tr>

                                <td>
                                    ${toner.impressora || "-"}
                                </td>

                                <td>
                                    ${toner.ip || "-"}
                                </td>

                                <td>
                                    ${toner.toner || "-"}
                                </td>

                                <td>
                                    ${toner.dias_6 || "-"}
                                </td>

                                <td>
                                    <span class="badge bg-warning text-dark">
                                        ⚠️ Não confiável
                                    </span>
                                </td>

                            </tr>
                        `;

                    });


                } catch (erro) {

                    console.error(
                        "Erro ao carregar toners não confiáveis:",
                        erro
                    );

                }


                window.scrollTo({
                    top: lista.offsetTop - 20,
                    behavior: "smooth"
                });

            }
            /* ======================================================
            FECHAR CADASTRO
            ====================================================== */

            function fecharCadastroToner() {

                document.getElementById(
                    "formulario-toner"
                ).style.display = "none";


            }


          

            /* ======================================================
            CADASTRAR TONER
            ====================================================== */

            async function cadastrarToner() {

                const marca =
                    document.getElementById(
                        "toner-marca"
                    ).value.trim();


                const codigo =
                    document.getElementById(
                        "toner-codigo"
                    ).value.trim();


                const cor =
                    document.getElementById(
                        "toner-cor"
                    ).value;

                const modelosCompativeis =
                    document.getElementById(
                        "toner-modelos"
                    ).value.trim();


                const estoque =
                    document.getElementById(
                        "toner-estoque"
                    ).valueAsNumber;


                const estoqueMinimo =
                    document.getElementById(
                        "toner-minimo"
                    ).valueAsNumber;


                if (
                    !marca ||
                    !codigo ||
                    !cor
                ) {

                    alert(
                        "Preencha marca, código e cor."
                    );

                    return;

                }


                if (
                    !Number.isInteger(estoque) ||
                    !Number.isInteger(estoqueMinimo) ||
                    estoque < 0 ||
                    estoqueMinimo < 0
                ) {

                    alert(
                        "Informe quantidades inteiras e não negativas."
                    );

                    return;

                }


                try {

                    const resposta =
                        await fetch(
                            "/cadastrar-toner",
                            {

                                method: "POST",

                                headers: {

                                    "Content-Type":
                                        "application/json"

                                },

                                body:JSON.stringify({

                                    marca: marca,

                                    codigo: codigo,

                                    cor: cor,

                                    modelos_compativeis:
                                        modelosCompativeis,

                                    estoque: estoque,

                                    estoque_minimo:
                                        estoqueMinimo

                                })

                            }
                        );


                    const resultado =
                        await resposta.json();


                    if (!resposta.ok) {

                        alert(
                            resultado.erro ||
                            "Não foi possível cadastrar."
                        );

                        return;

                    }


                    alert(
                        "Toner cadastrado com sucesso!"
                    );


                    document.getElementById(
                        "toner-marca"
                    ).value = "";


                    document.getElementById(
                        "toner-codigo"
                    ).value = "";


                    document.getElementById(
                        "toner-cor"
                    ).value = "";

                    document.getElementById(
                        "toner-modelos"
                    ).value = "";


                    document.getElementById(
                        "toner-estoque"
                    ).value = "0";


                    document.getElementById(
                        "toner-minimo"
                    ).value = "1";


                    fecharCadastroToner();


                    mostrarEstoque();


                } catch (erro) {

                    console.error(erro);


                    alert(
                        "Erro de comunicação com o servidor."
                    );

                }

            }
            
            async function mostrarhistorico() {

                esconderAreas();

                 try {

                    const resposta = await fetch("/historico");

                    const texto = await resposta.text();

                    if (!resposta.ok) {
                        throw new Error(
                            "Erro HTTP " +
                            resposta.status +
                            ": " +
                            texto
                        );
                    }

                    const dados = JSON.parse(texto);

                    if (secaoMenuAtiva !== "historico") {
                        return;
                    }

                    let areahistorico =
                        document.getElementById("area-historico");

                    if (!areahistorico) {

                        areahistorico =
                            document.createElement("div");

                        areahistorico.id =
                            "area-historico";

                        areahistorico.className =
                            "mb-4";

                        document
                            .querySelector(".container-fluid")
                            .appendChild(areahistorico);
                    }

                    function criarTabela(lista, tipo) {

                        if (!lista || lista.length === 0) {

                            return `
                                <div class="alert alert-info">
                                    Nenhum registro encontrado.
                                </div>
                            `;
                        }

                        if (
                            tipo === "ENTRADAS" ||
                            tipo === "SAIDAS" ||
                            tipo === "AUTOMATICAS"
                        ) {
                            const colunaLocal =
                                tipo === "AUTOMATICAS"
                                    ? "<th>Local</th>"
                                    : "";

                            return `
                                <div class="table-responsive">

                                    <table class="table table-striped table-hover">

                                        <thead class="table-dark">

                                            <tr>
                                                <th>Data</th>
                                                <th>Tipo</th>
                                                <th>Toner</th>
                                                <th>Quantidade</th>
                                                <th>IP</th>
                                                ${colunaLocal}
                                                <th>Patrimônio</th>
                                                <th>Responsável</th>
                                                <th>Observação</th>
                                            </tr>

                                        </thead>

                                        <tbody>

                                            ${lista.map(item => `

                                                <tr>

                                                    <td>
                                                        ${item.data || "-"}
                                                    </td>

                                                    <td>
                                                        ${item.tipo || "-"}
                                                    </td>

                                                    <td>
                                                        ${item.toner || "-"}
                                                    </td>

                                                    <td>
                                                        ${item.quantidade || "-"}
                                                    </td>

                                                    <td>
                                                        ${item.ip_impressora || "-"}
                                                    </td>

                                                    ${
                                                        tipo === "AUTOMATICAS"
                                                            ? `<td>${item.local_impressora || "-"}</td>`
                                                            : ""
                                                    }

                                                    <td>
                                                        ${item.patrimonio || "-"}
                                                    </td>

                                                    <td>
                                                        ${item.responsavel || "-"}
                                                    </td>

                                                    <td>
                                                        ${item.observacao || "-"}
                                                    </td>

                                                </tr>

                                            `).join("")}

                                        </tbody>

                                    </table>

                                </div>
                            `;
                        }

                        return `
                            <div class="table-responsive">

                                <table class="table table-striped table-hover">

                                    <thead class="table-dark">

                                        <tr>
                                            <th>Data</th>
                                            <th>Modelo / Local</th>
                                            <th>IP</th>
                                            <th>Patrimônio</th>
                                            <th>Tempo Offline</th>
                                        </tr>

                                    </thead>

                                    <tbody>

                                        ${lista.map(item => `

                                            <tr>

                                                <td>
                                                    ${item.data || "-"}
                                                </td>

                                                <td>
                                                    ${item.modelo || "-"}
                                                </td>

                                                <td>
                                                    ${item.ip_impressora || "-"}
                                                </td>

                                                <td>
                                                    ${item.patrimonio || "-"}
                                                </td>

                                                <td>
                                                    <strong>
                                                        ${item.duracao || "-"}
                                                    </strong>
                                                </td>

                                            </tr>

                                        `).join("")}

                                    </tbody>

                                </table>

                            </div>
                        `;
                    }

                    areahistorico.innerHTML = `

                        <div class="cabecalho-lista">

                            <h3>
                                Histórico de movimentações
                            </h3>

                        </div>


                        <div
                            style="
                                display:flex;
                                gap:10px;
                                margin:20px 0;
                                flex-wrap:wrap;
                            ">

                            <button
                                id="barra-entradas"
                                class="btn btn-success"
                                onclick="mostrarAbahistorico('entradas')">

                                ENTRADAS DE TONER

                            </button>


                            <button
                                id="barra-saidas"
                                class="btn btn-warning"
                                onclick="mostrarAbahistorico('saidas')">

                                SAÍDAS DE TONER

                            </button>

                            <button
                                id="barra-trocas-automaticas"
                                class="btn btn-info"
                                onclick="mostrarAbahistorico('automaticas')">

                                TROCAS AUTOMÁTICAS (${dados.saidas_automaticas.length})

                            </button>


                            <button
                                id="barra-offline"
                                class="btn btn-danger"
                                onclick="mostrarAbahistorico('offline')">

                                IMPRESSORAS OFFLINE

                            </button>

                        </div>


                        <div id="historico-entradas">

                            <h4>
                                Entradas de Toner
                            </h4>

                            ${criarTabela(
                                dados.entradas,
                                "ENTRADAS"
                            )}

                        </div>


                        <div
                            id="historico-saidas"
                            style="display:none;">

                            <h4>
                                Saídas de Toner
                            </h4>

                            ${criarTabela(
                                dados.saidas,
                                "SAIDAS"
                            )}

                        </div>

                        <div
                            id="historico-automaticas"
                            style="display:none;">

                            <h4>
                                Trocas de toner detectadas automaticamente
                            </h4>

                            ${criarTabela(
                                dados.saidas_automaticas,
                                "AUTOMATICAS"
                            )}

                        </div>


                        <div
                            id="historico-offline"
                            style="display:none;">

                            <h4>
                                Impressoras Offline
                            </h4>

                            ${criarTabela(
                                dados.offline,
                                "OFFLINE"
                            )}

                        </div>

                    `;


                    window.mostrarAbahistorico =
                        function(tipo) {

                            document.getElementById(
                                "historico-entradas"
                            ).style.display = "none";

                            document.getElementById(
                                "historico-saidas"
                            ).style.display = "none";

                            document.getElementById(
                                "historico-offline"
                            ).style.display = "none";

                            document.getElementById(
                                "historico-automaticas"
                            ).style.display = "none";


                            document.getElementById(
                                "historico-" + tipo
                            ).style.display = "block";
                        };


                    areahistorico.style.display =
                        "block";


                    window.scrollTo({

                        top:
                            areahistorico.offsetTop - 20,

                        behavior:
                            "smooth"

                    });


                } catch (erro) {

                    console.error(
                        "Erro ao carregar histórico:",
                        erro
                    );

                    if (secaoMenuAtiva === "historico") {
                        alert(
                            "Não foi possível carregar o Histórico."
                        );
                    }
                }
            }

            /* ======================================================
            REMOVER TONER
            ====================================================== */

            async function removerToner(tonerId) {

                const confirmar = confirm(
                    "Tem certeza que deseja remover este toner do estoque?"
                );

                if (!confirmar) {

                    return;

                }


                try {

                    const resposta = await fetch(
                        "/remover-toner/" + tonerId,
                        {
                            method: "DELETE"
                        }
                    );


                    const resultado =
                        await resposta.json();


                    if (!resposta.ok) {

                        alert(
                            resultado.erro ||
                            "Não foi possível remover o toner."
                        );

                        return;

                    }


                    alert(
                        "Toner removido com sucesso!"
                    );


                    mostrarEstoque();


                } catch (erro) {

                    console.error(
                        "Erro ao remover toner:",
                        erro
                    );


                    alert(
                        "Erro de comunicação com o servidor."
                    );

                }

            }
            /* ======================================================
            ABRIR SAÍDA DE TONER
            ====================================================== */

            async function abrirSaidaToner() {

                document.getElementById(
                    "formulario-toner"
                ).style.display = "none";


                document.getElementById(
                    "formulario-saida-toner"
                ).style.display = "block";


                const select =
                    document.getElementById(
                        "saida-toner"
                    );


                select.innerHTML = `
                    <option value="">
                        Carregando toners...
                    </option>
                `;


                try {

                    const resposta =
                        await fetch("/estoque");


                    const toners =
                        await resposta.json();


                    select.innerHTML = `
                        <option value="">
                            Selecione o toner
                        </option>
                    `;


                    toners.forEach(function(toner) {

                        select.innerHTML += `

                            <option
                                value="${toner.id}"
                                data-estoque="${toner.estoque}">

                                ${toner.marca}
                                -
                                ${toner.codigo}
                                -
                                ${toner.cor}

                                (Estoque:
                                ${toner.estoque})

                            </option>

                        `;

                    });


                } catch (erro) {

                    console.error(erro);


                    select.innerHTML = `
                        <option value="">
                            Erro ao carregar toners
                        </option>
                    `;

                }

            }


            /* ======================================================
            FECHAR SAÍDA DE TONER
            ====================================================== */

            function fecharSaidaToner() {

                document.getElementById(
                    "formulario-saida-toner"
                ).style.display = "none";

            }

            /* ======================================================
            REGISTRAR SAÍDA DE TONER
            ====================================================== */

            async function salvarSaidaToner() {

                const tonerId =
                    document.getElementById(
                        "saida-toner"
                    ).value;


                const quantidade =
                    parseInt(
                        document.getElementById(
                            "saida-quantidade"
                        ).value
                    );


                const ip =
                    document.getElementById(
                        "saida-ip"
                    ).value.trim();


                const patrimonio =
                    document.getElementById(
                        "saida-patrimonio"
                    ).value.trim();


                const responsavel =
                    document.getElementById(
                        "saida-responsavel"
                    ).value.trim();


                const observacao =
                    document.getElementById(
                        "saida-observacao"
                    ).value.trim();


                if (!tonerId) {

                    alert(
                        "Selecione o toner."
                    );

                    return;

                }


                if (
                    isNaN(quantidade) ||
                    quantidade <= 0
                ) 
                {

                    alert(
                        "Informe uma quantidade válida."
                    );

                    return;

                }


                if (!ip) {

                    alert(
                        "Informe o IP da impressora."
                    );

                    return;

                }


                if (!responsavel) {

                    alert(
                        "Informe o responsável."
                    );

                    return;

                }


                const confirmar = confirm(
                    "Confirmar saída de " +
                    quantidade +
                    " unidade(s) deste toner?"
                );


                if (!confirmar) {

                    return;

                }


                try {

                    const resposta =
                        await fetch(
                            "/registrar-saida-toner",
                            {

                                method: "POST",

                                headers: {

                                    "Content-Type":
                                        "application/JSON"

                                },

                                body:JSON.stringify({

                                    toner_id:
                                        tonerId,

                                    quantidade:
                                        quantidade,

                                    ip_impressora:
                                        ip,

                                    patrimonio:
                                        patrimonio,

                                    responsavel:
                                        responsavel,

                                    observacao:
                                        observacao

                                })

                            }
                        );


                    const resultado =
                        await resposta.json();


                    if (!resposta.ok) {

                        alert(
                            resultado.erro ||
                            "Não foi possível registrar a saída."
                        );

                        return;

                    }


                    alert(
                        "Saída registrada com sucesso!\n\n" +
                        "Novo estoque: " +
                        resultado.novo_estoque
                    );


                    document.getElementById(
                        "saida-toner"
                    ).value = "";


                    document.getElementById(
                        "saida-quantidade"
                    ).value = "1";


                    document.getElementById(
                        "saida-ip"
                    ).value = "";


                    document.getElementById(
                        "saida-patrimonio"
                    ).value = "";


                    document.getElementById(
                        "saida-responsavel"
                    ).value = "";


                    document.getElementById(
                        "saida-observacao"
                    ).value = "";


                    fecharSaidaToner();


                    mostrarEstoque();


                } catch (erro) {

                    console.error(
                        "Erro ao registrar saída:",
                        erro
                    );


                    alert(
                        "Erro de comunicação com o servidor."
                    );

                }
            }


            /* ======================================================
            BUSCAR IMPRESSORA PELO IP
            ====================================================== */

            async function buscarImpressoraSaida() {

                const ip =
                    document.getElementById(
                        "saida-busca-ip"
                    ).value.trim();


                const resultado =
                    document.getElementById(
                        "resultado-impressora-saida"
                    );


                const dados =
                    document.getElementById(
                        "dados-impressora-saida"
                    );


                if (!ip) {

                    alert(
                        "Digite o IP da impressora."
                    );

                    return;

                }


                resultado.style.display = "block";


                dados.className =
                    "alert alert-info mb-0";


                dados.textContent =
                    "Procurando impressora...";


                try {

                    const resposta =
                        await fetch("/dados");


                    if (!resposta.ok) {

                        throw new Error(
                            "Não foi possível consultar as impressoras."
                        );

                    }


                    const impressoras =
                        await resposta.json();


                    const impressora =
                        impressoras.find(
                            item =>
                                String(item.ip).trim() === ip
                        );


                    if (!impressora) {

                        dados.className =
                            "alert alert-danger mb-0";


                        dados.textContent =
                            "Nenhuma impressora encontrada com o IP " +
                            ip;


                        return;

                    }


                    dados.className =
                        "alert alert-success mb-0";


                    dados.innerHTML = `

                        <strong>
                            Impressora encontrada
                        </strong>

                        <br>

                        Modelo/Local:
                        ${impressora.modelo || "-"}

                        <br>

                        Patrimônio:
                        ${impressora.patrimonio || "-"}

                        <br>

                        IP:
                        ${impressora.ip}

                    `;


                    document.getElementById(
                        "saida-ip"
                    ).value =
                        impressora.ip;


                    document.getElementById(
                        "saida-patrimonio"
                    ).value =
                        impressora.patrimonio || "";

                } catch (erro) {

                    console.error(erro);


                    dados.className =
                        "alert alert-danger mb-0";


                    dados.textContent =
                        "Erro ao consultar as impressoras.";

                }

            }
            /* ======================================================
            MOSTRAR ESTOQUE DISPONÍVEL
            ====================================================== */

            function atualizarEstoqueSaida() {

                const select =
                    document.getElementById(
                        "saida-toner"
                    );

                const opcao =
                    select.options[
                        select.selectedIndex
                    ];


                const quantidade =
                    document.getElementById(
                        "saida-quantidade"
                    );


                const aviso =
                    document.getElementById(
                        "saida-estoque-disponivel"
                    );


                if (
                    !opcao ||
                    !opcao.value
                ) 
                {

                    aviso.textContent =
                        "Estoque disponível: -";

                    quantidade.max = "";

                    return;

                }


                const estoque = Number(opcao.dataset.estoque);
                if (!Number.isInteger(estoque)) {

                    aviso.textContent =
                        "Estoque disponível: não informado";

                    quantidade.max = "";

                    return;

                }


                aviso.textContent =
                    "Estoque disponível: " +
                    estoque +
                    " (a baixa pode deixar o estoque negativo)";
                quantidade.removeAttribute("max");

            }

            async function alterarEstoqueRapido(tonerId, acao) {

                try {

                    const resposta = await fetch(
                        `/ajustar-estoque/${tonerId}`,
                        {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json"
                            },
                            body: JSON.stringify({
                                acao: acao
                            })
                        }
                    );

                    const resultado = await resposta.json();

                    if (!resposta.ok) {
                        alert(resultado.erro || "Erro ao alterar estoque.");
                        return;
                    }

                    // Atualiza a tabela com o novo saldo
                    await mostrarEstoque();

                } catch (erro) {

                    console.error("Erro ao alterar estoque:", erro);

                    alert("Não foi possível atualizar o estoque.");

                }
            }

      


/* ======================================================
BARRA LATERAL RECOLHÍVEL
====================================================== */

function alternarMenu() {
    const corpo = document.body;
    const btnToggle = document.getElementById("btn-toggle-menu");

    if (window.matchMedia("(max-width: 768px)").matches) {
        const menuAberto = corpo.classList.toggle("menu-aberto-mobile");
        const acao = menuAberto ? "Fechar" : "Abrir";

        if (btnToggle) {
            btnToggle.setAttribute("aria-expanded", String(menuAberto));
            btnToggle.setAttribute("aria-label", `${acao} menu`);
            btnToggle.setAttribute("title", `${acao} menu`);
            const texto = btnToggle.querySelector(".texto-toggle");
            if (texto) {
                texto.textContent = `${acao} Menu`;
            }
        }

        return;
    }

    corpo.classList.remove("menu-aberto-mobile");
    const estaRecolhido = corpo.classList.toggle("menu-recolhido");

    try {
        localStorage.setItem("menu_recolhido", estaRecolhido ? "1" : "0");
    } catch (erro) {
        console.error("Não foi possível salvar o estado do menu:", erro);
    }

    if (btnToggle) {
        btnToggle.setAttribute("aria-expanded", String(!estaRecolhido));
        btnToggle.setAttribute(
            "title",
            estaRecolhido ? "Expandir menu lateral" : "Recolher menu lateral"
        );
        btnToggle.setAttribute(
            "aria-label",
            estaRecolhido ? "Expandir menu lateral" : "Recolher menu lateral"
        );
        const texto = btnToggle.querySelector(".texto-toggle");
        if (texto) {
            texto.textContent =
                estaRecolhido ? "Expandir Menu" : "Recolher Menu";
        }
    }
}

function focarPesquisa() {
    if (document.body.classList.contains("menu-recolhido")) {
        alternarMenu();
    }
    const inputPesquisa = document.getElementById("pesquisa");
    if (inputPesquisa) {
        setTimeout(() => inputPesquisa.focus(), 150);
    }
}

window.alternarMenu = alternarMenu;
window.focarPesquisa = focarPesquisa;

let consultaContadorAtual = null;
let idConsultaContador = 0;

async function abrirFichaImpressora(linha) {
    const ficha = document.getElementById("ficha-impressora");
    const ip = (linha.dataset.ip || "").trim();

    if (!ficha || !ip) {
        console.error("Não foi possível abrir a ficha da impressora.");
        return;
    }

    if (consultaContadorAtual) {
        consultaContadorAtual.abort();
    }

    const idConsulta = ++idConsultaContador;
    consultaContadorAtual = new AbortController();

    document.getElementById("ficha-impressora-titulo").textContent =
        linha.dataset.setor || linha.dataset.modelo || "Impressora";
    document.getElementById("ficha-impressora-setor").textContent =
        linha.dataset.setor || "-";
    document.getElementById("ficha-impressora-ip").textContent = ip;
    document.getElementById("ficha-impressora-patrimonio").textContent =
        linha.dataset.patrimonio || "Não informado";
    document.getElementById("ficha-impressora-modelo").textContent =
        linha.dataset.modelo || "Não informado";
    document.getElementById("ficha-impressora-status").textContent =
        linha.dataset.status || "Não informado";
    document.getElementById("ficha-impressora-toner").textContent =
        "Consultando cadastro...";
    document.getElementById("ficha-impressora-contador").textContent =
        "Consultando impressora...";
    document.getElementById("ficha-impressora-mensagem").textContent = "";

    if (!ficha.open) {
        ficha.showModal();
    }

    try {
        const resposta = await fetch(
            `/api/impressoras/${encodeURIComponent(ip)}/contador`,
            { signal: consultaContadorAtual.signal }
        );
        const dados = await resposta.json();

        if (!resposta.ok) {
            throw new Error(
                dados.erro || `Erro HTTP ${resposta.status}`
            );
        }

        if (idConsulta !== idConsultaContador || !ficha.open) {
            return;
        }

        const areaToner = document.getElementById(
            "ficha-impressora-toner"
        );
        areaToner.replaceChildren();

        if (!dados.toners || dados.toners.length === 0) {
            areaToner.textContent =
                "Nenhum toner compatível cadastrado para este modelo.";
        } else {
            dados.toners.forEach(function(toner) {
                const item = document.createElement("span");
                item.className = "ficha-impressora-toner-item";
                item.textContent =
                    `${toner.marca} ${toner.codigo} (${toner.cor})`;
                areaToner.appendChild(item);
            });
        }

        if (!Number.isSafeInteger(dados.contador) || dados.contador < 0) {
            document.getElementById("ficha-impressora-contador").textContent =
                "Contador indisponível";
            document.getElementById("ficha-impressora-mensagem").textContent =
                dados.erro || "A impressora não informou o contador de páginas.";
            return;
        }

        document.getElementById("ficha-impressora-contador").textContent =
            `${dados.contador.toLocaleString("pt-BR")} páginas`;
        document.getElementById("ficha-impressora-mensagem").textContent =
            "Contador lido diretamente da impressora via SNMP.";
    } catch (erro) {
        if (erro.name === "AbortError") {
            return;
        }

        if (idConsulta !== idConsultaContador || !ficha.open) {
            return;
        }

        console.error("Erro ao consultar ficha da impressora:", erro);
        document.getElementById("ficha-impressora-contador").textContent =
            "Contador indisponível";
        document.getElementById("ficha-impressora-toner").textContent =
            "Não foi possível carregar os toners compatíveis.";
        document.getElementById("ficha-impressora-mensagem").textContent =
            erro.message;
    }
}

function abrirFichaImpressoraComTeclado(evento, linha) {
    if (evento.key === "Enter" || evento.key === " ") {
        evento.preventDefault();
        abrirFichaImpressora(linha);
    }
}

function fecharFichaImpressora() {
    const ficha = document.getElementById("ficha-impressora");
    if (ficha && ficha.open) {
        ficha.close();
    }
}

document.addEventListener("DOMContentLoaded", function() {
    const ficha = document.getElementById("ficha-impressora");
    if (ficha) {
        ficha.addEventListener("close", function() {
            idConsultaContador++;
            if (consultaContadorAtual) {
                consultaContadorAtual.abort();
                consultaContadorAtual = null;
            }
        });
    }
});

window.abrirFichaImpressora = abrirFichaImpressora;
window.abrirFichaImpressoraComTeclado =
    abrirFichaImpressoraComTeclado;
window.fecharFichaImpressora = fecharFichaImpressora;
