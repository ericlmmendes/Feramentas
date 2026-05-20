let products = JSON.parse(localStorage.getItem('products')) || [];

function generateQRCode(text, container) {
  container.innerHTML = '';
  new QRCode(container, {
    text: text,
    width: 128,
    height: 128
  });
}

document.getElementById('productForm').addEventListener('submit', (e) => {
  e.preventDefault();
  
  const product = {
    id: Date.now(),
    nome: document.getElementById('nome').value,
    codigo: document.getElementById('codigo').value,
    descricao: document.getElementById('descricao').value,
    quantidade: parseInt(document.getElementById('quantidade').value)
  };

  products.push(product);
  localStorage.setItem('products', JSON.stringify(products));
  renderProducts();
  e.target.reset();
});

function renderProducts(filtered = products) {
  const list = document.getElementById('productList');
  list.innerHTML = '';

  filtered.forEach(p => {
    const div = document.createElement('div');
    div.className = 'product-card';
    div.innerHTML = `
      <h3>${p.nome}</h3>
      <p>Código: ${p.codigo}</p>
      <div class="qrcode" id="qr-${p.id}"></div>
      <button onclick="editProduct(${p.id})">Editar</button>
    `;
    list.appendChild(div);
    generateQRCode(p.codigo, document.getElementById(`qr-${p.id}`));
  });
}

// Busca
document.getElementById('search').addEventListener('input', (e) => {
  const term = e.target.value.toLowerCase();
  const filtered = products.filter(p => 
    p.nome.toLowerCase().includes(term) || 
    p.codigo.toLowerCase().includes(term)
  );
  renderProducts(filtered);
});

function criarTarefa() {
  // Aqui você seleciona produtos para a tarefa de coleta
  alert("Funcionalidade de criar tarefa em desenvolvimento.\nOs produtos selecionados irão para coleta.html");
  // Salvar tarefa no localStorage e redirecionar
  window.location.href = 'coleta.html';
}