# Frontend ImmoPilot

React 18 + TypeScript + Vite, consommant `/api/v1/`.

## Lancer

    cd frontend
    npm install
    npm run dev

Le serveur Django doit tourner en parallele. Vite relaie `/api` vers
`http://127.0.0.1:8140` par defaut ; `VITE_API_URL` permet d'en changer,
le port 8000 etant souvent deja pris par un autre projet.

    VITE_API_URL=http://127.0.0.1:8000 npm run dev

## Organisation

    src/api/       client HTTP : jeton, rafraichissement, erreurs
    src/auth/      contexte d'authentification
    src/components/ coquille de l'application
    src/pages/     un fichier par ecran
    src/types/     contrats de l'API

## Ce que le front ne fait pas

Aucune regle metier. L'imputation d'un encaissement sur les echeances est
calculee par le serveur : le front envoie ce que l'agent a saisi, et
affiche ce que le serveur repond. Un client ne doit pas pouvoir fausser
un solde.

## Coexistence avec l'interface Django

Les deux fronts tournent en parallele pendant la migration. Le theme est
volontairement identique, et le choix clair/sombre est lu dans la meme
cle `localStorage` : passer de l'un a l'autre ne doit pas donner
l'impression de changer d'application.
