# nfc-timecard

ローカルWindows専用のNFC勤務表アプリ。
NFCリーダー(PaSoRi)でマイナンバーカードをタップして、出勤/退勤をCSVに記録します。FastAPIでローカルAPIも提供します。

## できること（要件対応）
- 対象カード：マイナンバーカード。それ以外は原則無視（環境変数で緩和可）
- 1日2回の打刻：出勤→退勤
- 勤務時間 = 退勤 − 出勤 − 休憩1時間（マイナスは0扱い）
- 保存先：`./data/records.csv`（ローカルのみ）
- API: FastAPI で取得・集計（ローカル）

---

## セットアップ（uv 前提）

`pyproject.toml` に依存を追加・更新したら、プロジェクト直下で以下を実行します。

```powershell
# 依存ロックと同期（.venv が無ければ自動作成）
uv lock
uv sync
```

任意で仮想環境を有効化する場合:
```powershell
./.venv/Scripts/Activate.ps1
```

## Windows用ドライバ（WinUSB）
- Zadig をダウンロード: https://zadig.akeo.ie/
- NFCリーダーを接続
- Zadig → Options → "List All Devices" をON
- デバイス一覧から NFCリーダー（PaSoRi等）を選択 → Driver に "WinUSB" を選び Install Driver

## nfcpy 動作確認
```powershell
python -m nfc
```
読取待ちになればOK。うまくいかない場合はドライバ設定を再確認。

---

## 使い方

### 1) APIサーバを起動
```powershell
uvx uvicorn app.main:app --reload
```
- ヘルスチェック: http://127.0.0.1:8000/health
- レコード取得: http://127.0.0.1:8000/records
- 日次集計: http://127.0.0.1:8000/summary/daily?date=YYYY-MM-DD

### 2) NFCウォッチャを起動（別ターミナルで）
```powershell
uv run nfc_watch.py
```
- マイナンバーカードをタップすると、当日の社員ID（カード識別子を非PIIのHEX化）で出勤/退勤をトグル記録します。
- 二度目のタップで退勤が入り、所定の勤務時間（-1h 休憩）がCSVに確定します。

### 3) APIでレコード確認
- 当日全件
  ```powershell
  curl "http://127.0.0.1:8000/records?date=2025-11-11"
  ```
- 社員別
  ```powershell
  curl "http://127.0.0.1:8000/records/AB12CD34..."
  ```
- 日次集計
  ```powershell
  curl "http://127.0.0.1:8000/summary/daily?date=2025-11-11"
  ```

### リーダーが無い場合の簡易テスト
APIから擬似打刻できます。
```powershell
# 出勤（1回目）
curl -X POST "http://127.0.0.1:8000/punch?employee_id=TEST001"
# 退勤（2回目）
curl -X POST "http://127.0.0.1:8000/punch?employee_id=TEST001"
```

---

## データ仕様
- 保存先: `./data/records.csv`
- 形式: ヘッダ付きCSV（UTF-8）
- カラム: `date, employee_id, clock_in, clock_out, hours`
- 日時はISO8601（ローカルタイム）

---

## 実装メモ（KISS）
- ストレージはCSVのみ（`app/storage_csv.py`）。必要なら将来SQLiteへ拡張
- 業務ロジックは最小限（`app/domain.py`）
  - 勤務時間 = 退勤 − 出勤 − 1時間（最低0）
  - 社員IDはタグ識別子（bytes）をHEX化して非PII化
- NFCウォッチ: `nfc_watch.py`
  - 既定では My Number らしき Type4Tag のみ受け付け
  - 確実性が必要なら環境変数で緩和可能

### 環境変数
- `ACCEPT_ALL_TAGS=1` を設定すると、カード種別チェックを無効化（デモ/検証向け）

---

## トラブルシュート
- `ImportError: No module named fastapi` → 仮想環境が未有効または依存が未インストール。`Activate.ps1` と `uv pip install -e .` を再実行
- `python -m nfc` で読取待ちにならない → ZadigでWinUSBドライバを再確認
- PaSoRiの型番によっては名前が異なる場合あり（"Sony RC-S380" など）

---

## ライセンス
このリポジトリの `LICENSE` を参照してください。
