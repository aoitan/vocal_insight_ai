import librosa
import numpy as np
import parselmouth
import json

# --- 設定項目 ---
RMS_DELTA_PERCENTILE = 95 # RMSの変化点検出に使用するパーセンタイル
MIN_LEN_SEC = 8.0   # セグメントの最小長さ（秒）
MAX_LEN_SEC = 45.0 # セグメントの最大長さ（秒）

def get_segment_boundaries(y, sr, percentile):
    rms = librosa.feature.rms(y=y)[0]
    delta_rms = np.abs(np.diff(rms))
    if len(delta_rms) == 0:
        return np.array([])
    threshold = np.percentile(delta_rms, percentile)
    change_points_frames = np.where(delta_rms > threshold)[0]
    return librosa.frames_to_time(change_points_frames + 1, sr=sr)

def process_boundaries(boundaries_sec, total_duration, min_len, max_len):
    all_boundaries = np.concatenate(([0], boundaries_sec, [total_duration]))
    all_boundaries = np.unique(all_boundaries)
    processed_boundaries = [all_boundaries[0]]
    for i in range(1, len(all_boundaries)):
        if all_boundaries[i] - processed_boundaries[-1] < min_len:
            continue
        processed_boundaries.append(all_boundaries[i])
    final_boundaries = []
    for i in range(len(processed_boundaries) - 1):
        start, end = processed_boundaries[i], processed_boundaries[i+1]
        final_boundaries.append(start)
        duration = end - start
        if duration > max_len:
            num_splits = int(np.ceil(duration / max_len))
            split_len = duration / num_splits
            for j in range(1, num_splits):
                final_boundaries.append(start + j * split_len)
    final_boundaries.append(processed_boundaries[-1])
    return np.unique(final_boundaries)

def analyze_segment_with_praat(y_segment, sr):
    """parselmouthを使って音声セグメント（NumPy配列）を分析し、特徴量を返す"""
    try:
        snd = parselmouth.Sound(y_segment, sr)
        pitch = snd.to_pitch()
        hnr = snd.to_harmonicity()
        formant = snd.to_formant_burg()
        
        f0_values = pitch.selected_array['frequency']
        f0_valid = f0_values[f0_values != 0]
        
        # --- HNRの計算を「有声区間」のみに限定する修正 ---
        voiced_hnr_values = []
        for t, f0 in zip(pitch.ts(), pitch.selected_array['frequency']):
            if f0 > 0: # ピッチが検出されたフレームのみ
                hnr_val = hnr.get_value(time=t)
                if np.isfinite(hnr_val):
                    voiced_hnr_values.append(hnr_val)
        # --- 修正ここまで ---

        f1_mean = np.nanmean([formant.get_value_at_time(1, t) for t in formant.ts() if t is not None])
        f2_mean = np.nanmean([formant.get_value_at_time(2, t) for t in formant.ts() if t is not None])
        f3_mean = np.nanmean([formant.get_value_at_time(3, t) for t in formant.ts() if t is not None])

        return {
            "f0_mean_hz": float(np.mean(f0_valid)) if len(f0_valid) > 0 else 0,
            "f0_std_hz": float(np.std(f0_valid)) if len(f0_valid) > 0 else 0,
            "hnr_mean_db": float(np.mean(voiced_hnr_values)) if len(voiced_hnr_values) > 0 else 0,
            "f1_mean_hz": float(f1_mean) if not np.isnan(f1_mean) else 0,
            "f2_mean_hz": float(f2_mean) if not np.isnan(f2_mean) else 0,
            "f3_mean_hz": float(f3_mean) if not np.isnan(f3_mean) else 0,
        }
    except Exception as e:
        # エラーをサイレントに隠蔽せず、呼び出し元に通知するために例外を再スローする
        raise e


def generate_llm_prompt(analysis_data, filename):
    prompt = f"""
あなたはプロのボーカルアナリストです。
以下のデータは、楽曲「{filename}」の歌声の時系列データから、ダイナミクスの変化で分割したセグメントごとの音響特徴です。
このデータを元に、以下の点を総合的に分析し、レポートを作成してください。
- **感情の推移:** 曲全体を通して、ボーカルの感情はどのように変化していますか？
- **歌唱技術:** ピッチの安定性、声のクリアさ、声質などを元に、歌唱技術について評価してください。
- **セグメント間の比較:** エネルギーが大きく変化しているセグメント同士を比較し、表現の違いを論じてください。
---
### 分析データ
"""
    for segment in analysis_data:
        seg_id, start, end, feat = segment['segment_id'], segment['time_start_s'], segment['time_end_s'], segment['features']
        prompt += f"""
--- Segment {seg_id} ({start:.2f}s - {end:.2f}s) ---
- 平均ピッチ (F0): {feat['f0_mean_hz']:.1f} Hz
- ピッチの揺らぎ (F0 StdDev): {feat['f0_std_hz']:.1f} Hz
- 声のクリアさ (HNR): {feat['hnr_mean_db']:.1f} dB
- フォルマント F1: {feat['f1_mean_hz']:.1f} Hz
- フォルマント F2: {feat['f2_mean_hz']:.1f} Hz
- フォルマント F3: {feat['f3_mean_hz']:.1f} Hz
"""
    prompt += "\n--- 以上です。分析レポートを作成してください。---"
    return prompt

def analyze_audio_segments(y, sr, filename, rms_delta_percentile=RMS_DELTA_PERCENTILE, min_len_sec=MIN_LEN_SEC, max_len_sec=MAX_LEN_SEC):
    total_duration = librosa.get_duration(y=y, sr=sr)
    boundaries = get_segment_boundaries(y, sr, rms_delta_percentile)
    final_boundaries = process_boundaries(boundaries, total_duration, min_len_sec, max_len_sec)
    
    all_results = []
    
    for i in range(len(final_boundaries) - 1):
        start_sec, end_sec = final_boundaries[i], final_boundaries[i+1]
        segment_id = i + 1
        
        segment_y = y[int(start_sec * sr):int(end_sec * sr)]
        
        features = analyze_segment_with_praat(segment_y, sr)
        
        all_results.append({
            "segment_id": segment_id,
            "time_start_s": round(start_sec, 2),
            "time_end_s": round(end_sec, 2),
            "features": features
        })
    
    return all_results, generate_llm_prompt(all_results, filename)