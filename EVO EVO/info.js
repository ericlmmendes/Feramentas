/**
 * info.js
 * Arquivo de configuração de acesso ao sistema CDC Stock.
 * 
 * IMPORTANTE:
 * 1. Mantenha este arquivo fora do controle de versão (ex: adicione ao .gitignore)
 * 2. Em produção, substitua por autenticação real (Firebase Auth, JWT, etc.)
 * 3. Nunca exponha senhas em repositórios públicos.
 */

const ACCESS_CONFIG = {
  users: [
    {
      username: 'Ericlm.Evo',
      password: 'Evo@1989', // Senha forte, manter em produção com criptografia
      role: 'admin'
    },
    {
      username: 'admin',
      password: 'Admin@2025', // Senha mais forte
      role: 'admin'
    },
    {
      username: 'operador1',
      password: 'Op1@2025', // Senha única
      role: 'operador'
    },
    {
      username: 'operador2',
      password: 'Op2@2025', // Senha única
      role: 'operador'
    },
    {
      username: 'operador3',
      password: 'Op3@2025', // Senha única
      role: 'operador'
    }
  ],

  loginErrorMessage: 'Usuário ou senha incorretos!',

  sessionTimeout: 60 * 60 * 1000 // 1 hora
};

export default ACCESS_CONFIG;