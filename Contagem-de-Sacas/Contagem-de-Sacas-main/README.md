# SCS - Sistema Contagem de Sacas

O **Sistema Contagem de Sacas (SCS)** é uma aplicação web focada em ambiente corporativo/estoque projetada para gerenciar e contabilizar itens e lotes de forma dinâmica através do escaneamento de códigos de barras (ou QR Codes). O sistema também gera etiquetas personalizadas com códigos únicos, ideais para impressoras térmicas (150x100mm).

## 🚀 Funcionalidades

- **Bipagem pelo Coletor:** Registra leituras feitas por leitores de código de barras ou simuladores de digitação e valida se a etiqueta já foi processada no sistema (bloqueio de duplicidade).
- **Controle de Etiquetas (Geração de QRs):** Sistema de geração de QR Codes com controle interno de **garantia de unicidade**. O sistema valida dinamicamente se o código pretendido para a nova etiqueta já foi lido e listado em tabela, regenerando-o de forma silenciosa para evitar erros.
- **Integração Backend (Firebase):** Salva e sincroniza em tempo real as contagens com um banco de dados NoSQL (Firebase Realtime Database).
- **Relatório de Contagem:** Exibição dinâmica em Cards das contagens, com tabelas para validação histórica de bipes.
- **Exportação dos Dados:** É possível enviar um relatório resumido dos itens diretamente via WhatsApp (bloqueado por senha de administrador).
- **Limpeza de Relatório:** Recurso administrativo com autenticação de segurança para zerar todo o histórico de escaneamento local/Firebase.

## 🛠️ Tecnologias e Bibliotecas Utilizadas

- **HTML5 e CSS3** nativos, com suporte a Flexbox e Grid layouts e variáveis CSS (`:root`).
- **JavaScript Moderno (ES6+)**, explorando Promises, Async/Await e manipulação profunda de DOM.
- **Firebase SDK** para sincronização na nuvem (Realtime Database).
- **QRCode.js:** Para a geração dinâmica dos QRs nas etiquetas.
- **Phosphor Icons:** Biblioteca moderna para ícones de interface.

## 📋 Pré-requisitos & Como Rodar

Este sistema depende de dois arquivos locais não incluídos neste repositório por questões de segurança, que você precisa criar na raiz do seu projeto:

### 1. `acesso.js`
Este arquivo é o responsável por conter as senhas de sistema utilizadas nas exclusões e integrações de WhatsApp. Crie-o na mesma pasta do `index.html`: