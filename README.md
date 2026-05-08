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

## ユーザー管理

### 初期管理者アカウント

アプリ起動時に `users` テーブルが自動作成されます。テーブルが空の場合は `.env` の値で管理者を自動登録します。

| 項目 | デフォルト値 |
|------|-------------|
| ユーザー名 | `admin` |
| パスワード | `admin123` |

`.env` の `ADMIN_USERNAME` / `ADMIN_PASSWORD` で変更できます。

### 新規ユーザー登録

ログイン画面の「新規登録」タブからユーザーを追加できます。
パスワードは `werkzeug` の `generate_password_hash` でハッシュ化してDBに保存されます。

- ユーザー名: 50文字以内・重複不可
- パスワード: 6文字以上

## API エンドポイント一覧

| メソッド | パス | 認証 | 説明 |
|--------|------|------|------|
| GET  | `/api/health`      | 不要 | バックエンド死活確認 |
| GET  | `/api/status`      | 不要 | API・DB接続ステータス |
| POST | `/api/register`    | 不要 | 新規ユーザー登録 |
| POST | `/api/login`       | 不要 | ログイン → トークン発行 |
| GET  | `/api/server-info` | 必要 | ホスト名・IP・DB状態 |
| POST | `/api/logout`      | 必要 | ログアウト |
