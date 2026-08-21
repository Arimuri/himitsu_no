# himitsu_no

in the blue shirt「ひみつの」(ボカコレ2026夏) のMV生成コード。

手描きワイヤーフレーム調の3Dシーンを pygame で直接描画し、ffmpeg にパイプして
mp4 を書き出すオフラインレンダラー群です。
- 紺地 (50,92,122) 
- 白ジッタ線の2度描き
- ミクはスクリブル線
- 1280x720 / 12fps。

## 構成

```
core/      描画エンジン(全カット共通)
cuts/      カット1本 = スクリプト1本(実行すると movie/current/ に mp4 を出力)
tools/     構図スタディ・モック
stems/     パート別ステム(wav)
lyric.txt  歌詞
```

### core/

| ファイル | 内容 |
| --- | --- |
| `scribble.py` | 手描き風ストローク線(p5.scribble.js の pygame 移植)+ ジッタ線 `jitter_line` |
| `bg_sketch.py` | 3D投影(EYE/CENTER/カメラ基底)、スタイル定義、面単位の遮蔽描画 `draw_shape` |
| `bg_props.py` | パラメトリック背景素材(建物・木・岩・鉄塔・観覧車・星座・歌詞モチーフ等 60種以上)、ワールド固定の星空 `stars()` |
| `design_sketch.py` | ミクのキャラクターリグ(`draw_miku`: ぴょこぴょこ歩き・テール揺れ・後ろ姿) |
| `bg_models.json` | 材質テーブル等のモデルデータ |

### cuts/

各スクリプトは単体実行。出力先は各スクリプト冒頭の `OUT_DIR` 定数で指定
(既定値は制作環境のローカルパスなので、手元で動かす場合は書き換える)。

```
venv/bin/python cuts/grand_finale.py
```

| カット | 内容 |
| --- | --- |
| alone_plain | 無地平面にポツンとミク(ヒキ静止) |
| bldg_lookup | 「遠いとこまで行きたいなら」地上から見上げ→空パン→月 |
| bulb_idea | 「考えたほうがいい」床に転がる電球+這うケーブル |
| busstop_wait | バス停で待つミク(横トラック+上昇) |
| claw_play | クレーンゲームで遊ぶ(掴み損ね) |
| comet_twinkle | 流れ星2本が時間差で流れる |
| comp_video / comp2_pull / comp3_video | 基本構図3種の動画化(静・引き・空パン) |
| cradle_click | ニュートンのゆりかご |
| dice_bowl | サイコロ2個が丼に飛び込みピンゾロ |
| ferris_ride | 観覧車ゴンドラのミクにズーム(深度ソート不透明ゴンドラ) |
| float_ride | 屋根乗り浮遊→太陽系中心へフライスルー |
| gacha_roll | ガチャのクランク→カプセルころん |
| grand_finale | 全要素回収の大俯瞰フィナーレ |
| konbini_wait | コンビニ前のミク |
| lamp_glow | 「やるせない人間の輝き」街灯3本の点滅 |
| laundry_hang | シャツを物干しに干す |
| metronome3 | メトロノーム3台が5:4:3で刻む |
| motif_swap | ミク立ち+背景モチーフ2拍替え |
| radio_sky | 電波塔→オービット空パン→魚眼星座 |
| rocket_launch | ロケット発射(comp_3後半と同カメラ) |
| soba_wire | 「そばにいなくても」2軒を結ぶ電線のパルス往復 |
| solar_spin | 太陽系8秒完全ループ |
| space_finale | 宇宙タブローのフィナーレ |
| stringphone_call | 糸電話(パルス1回) |
| swing_ride | ブランコ立ち乗り(3D) |
| telescope_sky | 望遠鏡→空パン→魚眼星座リング+ロール |
| train_cut | 踏切を列車が通過 |
| ufo_talk | UFOとの会話→離脱 |
| walk_comp1 / walk_comp2 | 後ろ姿で歩き去る / 奥から歩いてくる(背景差し替え各3種) |
| yarn_roll | 毛糸玉が糸をほどきながら転がる(円弧パン) |

### tools/

| ファイル | 内容 |
| --- | --- |
| `mock_frame.py` / `mock_walk.py` / `mock_zoom.py` | スタイル・歩き・ズームの検証モック |
| `motif_spin.py` | モチーフのターンテーブル・ショーケース |

## セットアップ

```
python3 -m venv venv
venv/bin/pip install -r requirements.txt   # pygame
brew install ffmpeg                        # mp4 書き出しに使用
```

レンダリングはヘッドレス(`SDL_VIDEODRIVER=dummy` をスクリプト内で設定)。

## クレジット / ライセンス

- `core/scribble.py` は [p5.scribble.js](https://github.com/generative-light/p5.scribble.js)
  (原典: Processing の Handy/Scribble ライブラリ)の pygame 移植です。
- 上記以外のコードは in the blue shirt (有村崚) によるものです。
