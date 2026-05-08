# ネットワーク確認ツール

インフラ間（WebサーバーApp/サーバー/DBサーバー）のネットワーク接続を確認するための探知機アプリです。

## ディレクトリ構成

```
network_study/
├── backend/
│   ├── app.py           # Flask バックエンドAPI
│   ├── requirements.txt
│   └── .env.example     # 環境変数のテンプレート
├── frontend/
│   ├── index.html       # ログイン画面（ステータス表示）
│   └── dashboard.html   # ダッシュボード（サーバー情報）
├── .gitignore
└── README.md
```

## 起動手順

### 1. バックエンドのセットアップ

```bash
cd backend

# 環境変数ファイルを作成
cp .env.example .env
# .env を編集して DB接続情報・パスワードを設定

# 仮想環境を作成して依存パッケージをインストール
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

# バックエンドAPI起動（デフォルト: ポート 5000）
python app.py
```

### 2. フロントエンドの設定

`frontend/index.html` と `frontend/dashboard.html` の先頭付近にある下記の行を環境に合わせて変更してください。

```js
const API_BASE = "http://localhost:5000";
//                  ↑ バックエンドのホスト:ポートに書き換える
```

### 3. フロントエンドの配信

**方法A: Nginx / Apache（本番想定）**
`frontend/` ディレクトリをドキュメントルートに配置してください。

**方法B: Python の簡易サーバー（動作確認用）**
```bash
cd frontend
python3 -m http.server 8080
# ブラウザで http://localhost:8080 を開く
```

## デフォルトのログイン情報

| 項目 | 値 |
|------|-----|
| ユーザー名 | `admin` |
| パスワード | `admin123` |

`.env` の `ADMIN_USERNAME` / `ADMIN_PASSWORD` で変更できます。

## API エンドポイント一覧

| メソッド | パス | 説明 |
|--------|------|------|
| GET | `/api/health` | バックエンド死活確認 |
| GET | `/api/status` | API・DB接続ステータス（認証不要） |
| POST | `/api/login` | ログイン → トークン発行 |
| GET | `/api/server-info` | ホスト名・IP・DB状態（要認証） |
| POST | `/api/logout` | ログアウト |
