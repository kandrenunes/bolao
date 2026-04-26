# Bolão Survivor — Web

Sistema de bolão survivor com grupos de apostas por rodada.

## Stack
- **Backend**: FastAPI + Python
- **Frontend**: React + Tailwind + Vite
- **Auth**: JWT
- **Deploy**: Railway (ou qualquer plataforma Docker)

## Estrutura
```
bolao/
├── backend/
│   ├── main.py        ← API FastAPI (todas as rotas)
│   ├── core.py        ← Lógica de negócio
│   ├── auth.py        ← JWT
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/     ← Login, Cadastro, Dashboard, Apostas, Grupos, AdminPanel
│   │   ├── components/← Layout
│   │   ├── api.js     ← Cliente axios
│   │   └── store.js   ← Zustand auth
│   └── package.json
├── jogos.csv          ← Jogos do campeonato (obrigatório)
├── Dockerfile
└── railway.toml
```

## Desenvolvimento local

### Backend
```bash
cd backend
pip install -r requirements.txt
# Coloque jogos.csv na raiz
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev   # proxy para localhost:8000
```

Acesse: http://localhost:5173

### Admin
Login: celular = `admin`, senha = `admin123`
(altere SENHA_ADMIN via variável de ambiente em produção)

## Deploy no Railway

1. Crie conta em [railway.app](https://railway.app)
2. Novo projeto → Deploy from GitHub
3. Configure as variáveis de ambiente:
   ```
   SECRET_KEY=sua-chave-secreta-longa-aqui
   SENHA_ADMIN=senha-forte-do-admin
   ```
4. Adicione um Volume montado em `/app/dados`
5. O deploy é automático via Dockerfile

## Variáveis de ambiente

| Variável      | Padrão          | Descrição                    |
|---------------|-----------------|------------------------------|
| `SECRET_KEY`  | (inseguro)      | Chave JWT — mude em produção |
| `SENHA_ADMIN` | `admin123`      | Senha do painel admin        |
| `DADOS_DIR`   | `dados`         | Pasta dos JSONs              |
| `JOGOS_CSV`   | `jogos.csv`     | Caminho do CSV de jogos      |
| `PORT`        | `8000`          | Porta do servidor            |

## jogos.csv
O CSV deve ter o formato: `rodada,casa,visitante`
```csv
1,Flamengo,Palmeiras
1,Santos,Gremio
...
```

## API — principais endpoints

| Método | Rota                       | Descrição                    |
|--------|----------------------------|------------------------------|
| POST   | /api/auth/login            | Login (retorna JWT)          |
| POST   | /api/auth/cadastro         | Novo apostador               |
| GET    | /api/usuario/situacao      | Funis e status do usuário    |
| GET    | /api/rodadas               | Info da rodada ativa         |
| POST   | /api/apostas/nova-entrada  | Cria funis (debita créditos) |
| POST   | /api/apostas/continuar-funil| Aposta em funil vivo        |
| PUT    | /api/apostas/alterar       | Altera aposta desta rodada   |
| GET    | /api/grupos                | Lista grupos e apostadores   |
| POST   | /api/admin/abrir-rodada    | Abre rodada (admin)          |
| POST   | /api/admin/resultado       | Insere resultado (admin)     |

Documentação interativa: http://localhost:8000/docs
