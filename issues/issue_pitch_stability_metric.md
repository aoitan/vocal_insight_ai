# Pitch Analysis Stability 指標が常に0になる

## 概要
`vocal_insight` のピッチ精度分析で算出する `stability` 値が、実用的なサンプルに対してほぼ常に 0.00 と出力される。算出式が標準偏差を 200 セントで正規化する簡易実装のため、少しでも変動があると 0 付近に張り付いてしまい、ユーザーに有益な情報を提供できていない。

## 詳細
- 再現手順:
  1. `poetry run vocal-insight analyze` でピッチ解析を有効化 (`--pitch-analysis-enabled`)。
  2. 解析結果の JSON または CLI のサマリーを見ると `Stability: 0.00` となる。
- 現行実装: `vocal_insight/pitch/metrics.py` の `compute_stability` が `std_cents` を 200 セントで割り、1 から減算する単純式。
- 結果: 平均的な歌唱でも標準偏差が 200 セントを超えやすく、0.00 ばかりになり指標として機能していない。

## 期待される対応
- 安定度指標の再設計（例: 区間ごとのローカル変動、メディアンベースの正規化など）。
- しきい値が実データに適合するような再調整。
- 将来的にはピッチ変動を視覚化する補助情報や、ビブラートなど表現要素を切り出す仕組みを検討。

## 参考
- 実データ: `Mean deviation` が ~60 セント、`Hit rate` が ~0.75 のケースでも `Stability` が常に 0.00。
- 関連ファイル: `vocal_insight/pitch/metrics.py`, `doc/pitch_accuracy_analysis_requirements.md`

