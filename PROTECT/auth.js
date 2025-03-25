// auth.js
// ********** Configuração do Firebase **********
// Substitua os valores abaixo pelas configurações do seu projeto Firebase.
// auth.js
// ********** Configuração do Firebase **********
// Substitua os valores abaixo pelas configurações do seu projeto Firebase.
var firebaseConfig = {
    apiKey: "AIzaSyAUJJG81h2TPYs-9O27VZtDdgz3MO2duR8",
    authDomain: "usuario-cce07",
    projectId: "58847949782",
    storageBucket: "YOUR_STORAGE_BUCKET",
    messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
    appId: "YOUR_APP_ID"
  };
  
// Inicializa o Firebase
firebase.initializeApp(firebaseConfig);

// ********** Função para Verificação de Autenticação e Aprovação **********
function checkAuth() {
  firebase.auth().onAuthStateChanged(function(user) {
    if (user) {
      // Usuário autenticado, verifica aprovação
      firebase.firestore().collection('usuarios').doc(user.uid).get()
        .then(function(doc) {
          if (doc.exists && doc.data().aprovado) {
            // Usuário aprovado, permite acesso
            console.log("Acesso permitido.");
          } else {
            // Usuário não aprovado, redireciona
            window.location.href = "aguardando_aprovacao.html";
          }
        })
        .catch(function(error) {
          console.error("Erro ao verificar aprovação: ", error);
          window.location.href = "erro.html";
        });
    } else {
      // Usuário não autenticado, redireciona para login
      window.location.href = "login.html";
    }
  });
}
