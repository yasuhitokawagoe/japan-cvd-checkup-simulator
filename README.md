# 健診結果連携版・一次予防シミュレーター

健診結果を見ながら入力し、既存の一次予防心血管リスクモデルで将来リスクと介入シナリオを比較する、一般利用者向けStreamlitアプリです。

## ローカル起動

```bash
pip install -r requirements.txt
streamlit run app.py
```

## URLパラメータ

- `source`
- `campaign`（`A` / `B`）
- `facility_id`
- `ref`
- `admin=1`：匿名イベント集計
- `mode=handout`：健診添付用A4 QR台紙

Analyticsには健診値・リスク値・病歴・薬剤選択を保存しません。
