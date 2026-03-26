// acesso.js - Controle de acesso centralizado

(function () {
  const USUARIOS_VALIDOS = {
    "admin":       { senha: "123456",       nome: "ERICLM",     paginas: ["index.html", "asset.html"] },
    "inbound":     { senha: "inbound123",   nome: "Gabriel",    paginas: ["inbound_outbound.html"] },
    "expedicao":   { senha: "exp123",       nome: "Rodrigo",    paginas: ["expedicao.html"] },
    "inventario":  { senha: "inv123",       nome: "ERICLM",     paginas: ["inventario.html"] },
    "visualizacao":{ senha: "vis123",       nome: "ERICLM",     paginas: ["visualizacao.html"] },
  };

  function isLoggedIn() {
    return localStorage.getItem("loggedIn") === "true";
  }

  function getUserData() {
    const user = localStorage.getItem("user");
    return user ? USUARIOS_VALIDOS[user] : null;
  }

  function setLoggedIn(login) {
    localStorage.setItem("loggedIn", "true");
    localStorage.setItem("user", login);
  }

  function logout() {
    localStorage.clear();
    window.location.href = "index.html";
  }

  function showMainInterface(config) {
    document.getElementById(config.loginScreenId)?.classList.add("d-none");
    document.getElementById(config.mainScreenId)?.classList.remove("d-none");
    document.getElementById(config.navbarId)?.classList.remove("d-none");

    const userNameEl = document.getElementById(config.userNameId);
    if (userNameEl) {
      const userData = getUserData();
      userNameEl.textContent = userData?.nome || config.userDisplayName || "Usuário";
    }
  }

  function initAccess(options = {}) {
    const config = {
      loginFormId: "loginForm",
      loginScreenId: "loginScreen",
      mainScreenId: "mainScreen",
      navbarId: "navbar",
      userNameId: "userName",
      userDisplayName: "Usuário",
      ...options
    };

    const form = document.getElementById(config.loginFormId);
    if (!form) return;

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const login = document.getElementById("loginInput")?.value?.trim().toLowerCase();
      const senha = document.getElementById("senhaInput")?.value?.trim();

      if (USUARIOS_VALIDOS[login] && USUARIOS_VALIDOS[login].senha === senha) {
        setLoggedIn(login);
        showMainInterface(config);

        if (typeof config.onLogin === "function") {
          config.onLogin();
        }
      } else {
        alert("Login ou senha incorretos!");
      }
    });

    if (isLoggedIn()) {
      const userData = getUserData();
      if (userData) {
        showMainInterface(config);
        if (typeof config.onLogin === "function") {
          config.onLogin();
        }
      } else {
        logout();
      }
    }
  }

  window.access = {
    initAccess,
    logout,
    isLoggedIn,
    getUserData
  };

  window.logout = logout;
})();