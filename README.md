# ちい活マップ

ちいかわのお店・カフェ・期間限定イベントを、日本・韓国・台湾・中国の地図で探せる非公式ファンまとめです。

**サイト：** https://mayuko9775orz-wq.github.io/chiikatsu-map/

- 国ごとの地図と、地方・都市ごとの一覧
- 種類・エリア・キーワードでの絞り込み
- 「行った」スタンプ(記録は見ている人のブラウザにだけ保存)
- Googleマップ連携：スポットごとの行き方、複数スポットをまとめて回るルート、マイマップ用CSVの保存

## 更新のしかた

1. `data/spots.json` を編集する(項目の意味は下の表)
2. ページを作り直す
   ```
   python tools/build.py
   ```
3. 変更をコミットして push する。数分で GitHub Pages に反映されます

`docs/index.html` は自動で作られるファイルなので、直接は編集しません。

| 項目 | 内容 |
|---|---|
| `id` | 英小文字とハイフンの識別子。スタンプ記録とひもづくので、一度決めたら変えない |
| `country` | `JP` / `KR` / `TW` / `CN`(香港・マカオは `CN`) |
| `category` | `shop` / `food` / `facility` / `limited` |
| `name` / `nameLocal` | 店名(日本語)/ 現地語の名前 |
| `pref` / `area` / `place` / `address` | 都道府県または都市 / エリア / 建物とフロア / 住所 |
| `lat` / `lng` | 緯度・経度(不明なら `null`) |
| `hours` / `highlights` / `url` | 営業時間 / その店のポイント / 情報元のURL |
| `startDate` / `endDate` | 期間限定の開始日・終了日(`YYYY-MM-DD`)。終了日を過ぎると自動で非表示 |
| `checkedNote` | いつ・どこで確認したかのメモ |

`data/notes-*.md` は、スポットを集めたときの調査メモ(出典、確認しきれなかった点)です。

## ファイル構成

- `src/template.html` … ページ本体(デザインと動き)
- `src/footer.html` … フッターの文章
- `data/spots.json` … スポットのデータ
- `data/basemap.json` … 地図の形(`tools/make_map.py` で作成)
- `tools/build.py` … データをページに埋め込んで `docs/index.html` などを作る
- `docs/` … GitHub Pages で公開されるフォルダ

## このサイトについて

「ちいかわ」が好きな個人がつくった非公式のまとめです。原作者・公式・各店舗とは関係ありません。キャラクターの画像やロゴは使っていません。

「ちいかわ」©nagano / chiikawa committee

地図データ：日本は地球地図日本(国土地理院)を加工して作成、日本以外は Natural Earth。
