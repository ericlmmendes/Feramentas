// BD.js
import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.14.0/firebase-app.js';
import { getDatabase, ref, push, update, onValue, remove, set, get } from 'https://www.gstatic.com/firebasejs/10.14.0/firebase-database.js';

// Configuração do Firebase
const firebaseConfig = {
  apiKey: "AIzaSyB8lqLFl0agRrisPtjsmoWxr0nbTagiaqQ",
  authDomain: "d2d-cdc.firebaseapp.com",
  databaseURL: "https://d2d-cdc-default-rtdb.firebaseio.com",
  projectId: "d2d-cdc",
  storageBucket: "d2d-cdc.firebasestorage.app",
  messagingSenderId: "809375112221",
  appId: "1:809375112221:web:c80428315e9d084bd53af4",
  measurementId: "G-V876KE79ZC"
};

// Inicializar Firebase
const app = initializeApp(firebaseConfig);
const database = getDatabase(app);

// Função para enviar contagem ao Firebase
async function enviarContagem(tipo, unidades) {
  try {
    const contagemRef = ref(database, 'contagens');
    await push(contagemRef, {
      tipo,
      unidades,
      data: new Date().toISOString()
    });
    return true;
  } catch (e) {
    console.error('Erro ao enviar contagem:', e);
    return false;
  }
}

// Função para gerar QRCode (opcional, pode ser removida se não usada)
function gerarQRCode(elementId, texto) {
  const el = document.getElementById(elementId);
  if (el) {
    el.innerHTML = '';
    new window.QRCode(el, { text: texto, width: 100, height: 100 });
  }
}

// Exportar
export { database, ref, push, update, onValue, remove, set, get, enviarContagem, gerarQRCode };
