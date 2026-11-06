(function() {
    try {
        if (localStorage.getItem("menu_recolhido") === "1") {
            document.body.classList.add("menu-recolhido");
        }
    } catch (erro) {
        console.error("Não foi possível restaurar o estado do menu:", erro);
    }
})();
