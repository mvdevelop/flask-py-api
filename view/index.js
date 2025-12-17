
const API_URL = "http://localhost:3000/api/produtos";

async function carregarProdutos() {
  try {
    const response = await fetch(API_URL);

    if (!response.ok) {
      throw new Error("Erro ao buscar produtos");
    }

    const produtos = await response.json();
    const container = document.getElementById("produtos");

    container.innerHTML = "";

    if (produtos.length === 0) {
      container.innerHTML = "<p>Nenhum produto cadastrado.</p>";
      return;
    }

    produtos.forEach(produto => {
      const div = document.createElement("div");
      div.classList.add("produto");

      div.innerHTML = `
        <img src="${produto.img}" alt="${produto.nome}">
        <h3>${produto.nome}</h3>
        <p>${produto.descricao}</p>
      `;

      container.appendChild(div);
    });

  } catch (error) {
    console.error(error);
    document.getElementById("produtos").innerHTML =
      "<p>Erro ao carregar produtos.</p>";
  }
}

carregarProdutos();
