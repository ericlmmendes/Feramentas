// bd.js - Banco de dados (Firebase)
// Este arquivo expõe o objeto global `DB` com métodos assíncronos de CRUD.

import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.14.0/firebase-app.js';
import {
  getDatabase,
  ref,
  push,
  update,
  remove,
  set,
  get,
} from 'https://www.gstatic.com/firebasejs/10.14.0/firebase-database.js';

const firebaseConfig = {
  apiKey: 'AIzaSyAuKRaFDaViCQj72lQgLH7HDFUxOk43fss',
  authDomain: 'insumo-16085.firebaseapp.com',
  projectId: 'insumo-16085',
  storageBucket: 'insumo-16085.firebasestorage.app',
  messagingSenderId: '706106422021',
  appId: '1:706106422021:web:4e6b4fafda82104df93d6c',
  measurementId: 'G-1Y7ZRBX658',
};

let database = null;
let firebaseReady = false;

function log(msg, ...args) {
  console.log('[DB]', msg, ...args);
}

async function initFirebase() {
  if (firebaseReady) return;

  try {
    const app = initializeApp(firebaseConfig);
    database = getDatabase(app);
    firebaseReady = true;
    log('Firebase inicializado.');
  } catch (err) {
    console.error('Não foi possível inicializar Firebase:', err);
    firebaseReady = false;
  }
}

function toArrayObject(obj = {}) {
  return Object.entries(obj).map(([key, value]) => ({ id: key, ...value }));
}

async function readFromFirebase(path) {
  await initFirebase();
  if (!firebaseReady) return null;
  try {
    const snapshot = await get(ref(database, path));
    return snapshot.exists() ? snapshot.val() : null;
  } catch (err) {
    console.warn('Erro ao ler Firebase:', err);
    return null;
  }
}

async function writeToFirebase(path, data) {
  await initFirebase();
  if (!firebaseReady) return false;
  try {
    await set(ref(database, path), data);
    return true;
  } catch (err) {
    console.warn('Erro ao gravar Firebase:', err);
    return false;
  }
}

async function pushToFirebase(path, data) {
  await initFirebase();
  if (!firebaseReady) return null;
  try {
    const snapshot = await push(ref(database, path), data);
    return snapshot.key;
  } catch (err) {
    console.warn('Erro ao inserir no Firebase:', err);
    return null;
  }
}

async function removeFromFirebase(path) {
  await initFirebase();
  if (!firebaseReady) return false;
  try {
    await remove(ref(database, path));
    return true;
  } catch (err) {
    console.warn('Erro ao remover no Firebase:', err);
    return false;
  }
}

async function getAll(path) {
  const firebaseData = await readFromFirebase(path);
  if (!firebaseData) return [];
  return toArrayObject(firebaseData);
}

async function addItem(path, item) {
  const key = await pushToFirebase(path, item);
  return key;
}

async function updateItem(path, id, item) {
  if (!id) return false;
  return await updateItemFirebase(path, id, item);
}

async function deleteItem(path, id) {
  if (!id) return false;
  return await removeFromFirebase(`${path}/${id}`);
}

async function updateItemFirebase(path, id, item) {
  await initFirebase();
  if (!firebaseReady) return false;
  try {
    await update(ref(database, `${path}/${id}`), item);
    return true;
  } catch (err) {
    console.warn('Erro ao atualizar Firebase:', err);
    return false;
  }
}

async function getEntradas() {
  return await getAll('entradas');
}

async function getSaidas() {
  return await getAll('saidas');
}

async function getInventory() {
  const entradas = await getEntradas();
  const saidas = await getSaidas();

  const map = new Map();

  const keyFor = (item) => `${item.codigo || ''}||${item.nome || ''}`;

  entradas.forEach((e) => {
    const key = keyFor(e);
    const current = map.get(key) || {
      codigo: e.codigo || '',
      nome: e.nome || '',
      entrada: 0,
      saida: 0,
      imagem: e.imagem || '',
    };
    current.entrada += Number(e.quantidade) || 0;
    current.imagem = current.imagem || e.imagem || '';
    map.set(key, current);
  });

  saidas.forEach((s) => {
    const key = keyFor(s);
    const current = map.get(key) || {
      codigo: s.codigo || '',
      nome: s.nome || '',
      entrada: 0,
      saida: 0,
      imagem: s.imagem || '',
    };
    current.saida += Number(s.quantidade) || 0;
    current.imagem = current.imagem || s.imagem || '';
    map.set(key, current);
  });

  return Array.from(map.values()).map((item) => ({
    ...item,
    saldo: (Number(item.entrada) || 0) - (Number(item.saida) || 0),
  }));
}

async function addEntrada(entrada) {
  return addItem('entradas', entrada);
}
async function updateEntrada(id, entrada) {
  return updateItem('entradas', id, entrada);
}
async function deleteEntrada(id) {
  return deleteItem('entradas', id);
}

async function addSaida(saida) {
  return addItem('saidas', saida);
}
async function updateSaida(id, saida) {
  return updateItem('saidas', id, saida);
}
async function deleteSaida(id) {
  return deleteItem('saidas', id);
}

function gerarQRCode(elementId, texto) {
  const el = document.getElementById(elementId);
  if (el) {
    el.innerHTML = '';
    new window.QRCode(el, { text: texto, width: 100, height: 100 });
  }
}

const DB = {
  initFirebase,
  getAll,
  addItem,
  updateItem,
  deleteItem,
  getEntradas,
  addEntrada,
  updateEntrada,
  deleteEntrada,
  getSaidas,
  addSaida,
  updateSaida,
  deleteSaida,
  getInventory,
  gerarQRCode,
};

window.DB = DB;

export { DB };