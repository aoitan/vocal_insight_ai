#!/usr/bin/env python3
"""
VocalInsight CLI - 新モジュールアーキテクチャ対応版

このファイルは設計サンプルです。実装時の参考として使用してください。
"""

from pathlib import Path
from typing import Optional

import click
import librosa

# 新しいモジュールアーキテクチャのインポート
from vocal_insight import AnalysisConfig, analyze_audio_segments
from vocal_insight.features import AcousticFeatureExtractor
from vocal_insight.segments import SegmentBoundaryDetector, SegmentProcessor

# レガシー互換性のためのインポート
from vocal_insight_ai import analyze_audio_segments as legacy_analyze


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Quiet mode")
@click.version_option()
@click.pass_context
def cli(ctx, verbose: bool, quiet: bool):
    """VocalInsight AI - Advanced vocal analysis tool with modular architecture."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet

    if verbose and quiet:
        click.echo(
            "Error: --verbose and --quiet are mutually exclusive. Use one or the other.",
            err=True,
        )
        ctx.exit(1)


@cli.command()
@click.argument(
    "input_file", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path.cwd(),
    help="Output directory [default: current directory]",
)
@click.option(
    "--module",
    "-m",
    default="auto",
    type=click.Choice(["auto", "acoustic", "core", "legacy"], case_sensitive=False),
    help="Processing module to use [default: auto]",
)
@click.option(
    "--min-segment",
    type=float,
    default=8.0,
    help="Minimum segment length in seconds [default: 8.0]",
)
@click.option(
    "--max-segment",
    type=float,
    default=45.0,
    help="Maximum segment length in seconds [default: 45.0]",
)
@click.option(
    "--percentile",
    type=click.IntRange(1, 100),
    default=95,
    help="RMS percentile for boundary detection [default: 95]",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["txt", "json", "yaml"], case_sensitive=False),
    default="txt",
    help="Output format [default: txt]",
)
@click.pass_context
def analyze(
    ctx,
    input_file: Path,
    output_dir: Path,
    module: str,
    min_segment: float,
    max_segment: float,
    percentile: int,
    output_format: str,
):
    """Analyze an audio file and generate analysis results.

    This command performs complete vocal analysis including segment detection,
    feature extraction, and LLM prompt generation.

    Examples:

        # Basic usage (existing compatibility)
        vocal-insight analyze recording.wav

        # Custom segment settings
        vocal-insight analyze recording.wav --min-segment 5.0 --max-segment 30.0

        # JSON output
        vocal-insight analyze recording.wav --format json --output-dir ./results
    """
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    if not quiet:
        click.echo(f"🎵 Analyzing {input_file.name}...")

    # パラメータ検証
    if min_segment >= max_segment:
        click.echo("Error: --min-segment must be less than --max-segment", err=True)
        ctx.exit(1)

    # 設定作成
    config = AnalysisConfig(
        rms_delta_percentile=percentile,
        min_len_sec=min_segment,
        max_len_sec=max_segment,
    )

    try:
        # モジュール選択
        if module == "legacy":
            if verbose:
                click.echo("📦 Using legacy module (vocal_insight_ai)")
            # レガシーモジュール使用
            y, sr = librosa.load(input_file)
            analysis_results, llm_prompt = legacy_analyze(
                y, sr, input_file.name, config=config
            )
        else:
            if verbose:
                click.echo("📦 Using new modular architecture (vocal_insight)")
            # 新しいモジュールアーキテクチャ使用
            segments = analyze_audio_segments(str(input_file), config)

            # LLMプロンプト生成（後で実装）
            llm_prompt = _generate_llm_prompt_from_segments(segments)
            analysis_results = segments

        # 出力ディレクトリ作成
        output_dir.mkdir(parents=True, exist_ok=True)

        # 出力ファイル名生成
        base_name = input_file.stem

        if output_format == "txt":
            output_file = output_dir / f"{base_name}_analysis.txt"
            _save_text_format(output_file, analysis_results, llm_prompt)
        elif output_format == "json":
            output_file = output_dir / f"{base_name}_analysis.json"
            _save_json_format(output_file, analysis_results, input_file.name, config)
        elif output_format == "yaml":
            output_file = output_dir / f"{base_name}_analysis.yaml"
            _save_yaml_format(output_file, analysis_results, input_file.name, config)

        if not quiet:
            click.echo(f"✅ Analysis saved to {output_file}")

        if verbose:
            click.echo(f"📊 Found {len(analysis_results)} segments")
            total_duration = (
                analysis_results[-1]["time_end_s"] if analysis_results else 0
            )
            click.echo(f"⏱️  Total duration: {total_duration:.1f} seconds")

    except Exception as e:
        click.echo(f"❌ Error during analysis: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        ctx.exit(1)


@cli.command()
@click.argument(
    "input_file", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path.cwd(),
    help="Output directory [default: current directory]",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "csv", "yaml"], case_sensitive=False),
    default="json",
    help="Output format [default: json]",
)
@click.option(
    "--extractor",
    default="acoustic",
    type=click.Choice(["acoustic"], case_sensitive=False),
    help="Feature extractor to use [default: acoustic]",
)
@click.option(
    "--segment-start",
    type=float,
    help="Start time in seconds (extract from specific segment)",
)
@click.option(
    "--segment-end",
    type=float,
    help="End time in seconds (extract from specific segment)",
)
@click.pass_context
def extract(
    ctx,
    input_file: Path,
    output_dir: Path,
    output_format: str,
    extractor: str,
    segment_start: Optional[float],
    segment_end: Optional[float],
):
    """Extract acoustic features from audio file.

    This command extracts only acoustic features without performing
    full analysis or generating prompts.

    Examples:

        # Extract features from entire file
        vocal-insight extract recording.wav

        # Extract from specific time range
        vocal-insight extract recording.wav --segment-start 10.0 --segment-end 20.0

        # CSV output
        vocal-insight extract recording.wav --format csv
    """
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    if not quiet:
        click.echo(f"🔧 Extracting features from {input_file.name}...")

    # パラメータ検証
    _validate_time_range(segment_start, segment_end, ctx)

    try:
        # 音声読み込み
        y, sr = librosa.load(input_file)

        # セグメント切り出し（指定された場合）
        if segment_start is not None or segment_end is not None:
            start_frame = int((segment_start or 0) * sr)
            end_frame = int((segment_end or len(y) / sr) * sr)
            y = y[start_frame:end_frame]

            if verbose:
                duration = len(y) / sr
                click.echo(f"📏 Analyzing segment: {duration:.1f} seconds")

        # 特徴量抽出
        extractor_obj = AcousticFeatureExtractor()
        features = extractor_obj.extract(y, sr)

        # 出力
        output_dir.mkdir(parents=True, exist_ok=True)
        base_name = input_file.stem

        if segment_start is not None or segment_end is not None:
            suffix = f"_{segment_start or 0:.1f}s-{segment_end or (len(y)/sr):.1f}s"
            base_name += suffix

        if output_format == "json":
            output_file = output_dir / f"{base_name}_features.json"
            _save_features_json(output_file, features, input_file.name)
        elif output_format == "csv":
            output_file = output_dir / f"{base_name}_features.csv"
            _save_features_csv(output_file, features)
        elif output_format == "yaml":
            output_file = output_dir / f"{base_name}_features.yaml"
            _save_features_yaml(output_file, features, input_file.name)

        if not quiet:
            click.echo(f"✅ Features saved to {output_file}")

        if verbose:
            click.echo("📈 Extracted features:")
            for key, value in features.items():
                click.echo(f"   {key}: {value:.2f}")

    except Exception as e:
        click.echo(f"❌ Error during feature extraction: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        ctx.exit(1)


@cli.command()
@click.argument(
    "input_file", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path.cwd(),
    help="Output directory [default: current directory]",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "csv", "yaml"], case_sensitive=False),
    default="json",
    help="Output format [default: json]",
)
@click.option(
    "--min-segment",
    type=float,
    default=8.0,
    help="Minimum segment length in seconds [default: 8.0]",
)
@click.option(
    "--max-segment",
    type=float,
    default=45.0,
    help="Maximum segment length in seconds [default: 45.0]",
)
@click.option(
    "--percentile",
    type=click.IntRange(1, 100),
    default=95,
    help="RMS percentile for boundary detection [default: 95]",
)
@click.option(
    "--plot", is_flag=True, help="Generate visualization plot (requires matplotlib)"
)
@click.pass_context
def segment(
    ctx,
    input_file: Path,
    output_dir: Path,
    output_format: str,
    min_segment: float,
    max_segment: float,
    percentile: int,
    plot: bool,
):
    """Detect and analyze audio segments.

    This command performs only segment boundary detection without
    feature extraction or prompt generation.

    Examples:

        # Basic segmentation
        vocal-insight segment recording.wav

        # With visualization
        vocal-insight segment recording.wav --plot --output-dir ./results

        # Custom settings
        vocal-insight segment recording.wav --min-segment 5.0 --percentile 90
    """
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    if not quiet:
        click.echo(f"✂️  Detecting segments in {input_file.name}...")

    # パラメータ検証
    _validate_segment_range(min_segment, max_segment, ctx)

    try:
        # 音声読み込み
        y, sr = librosa.load(input_file)
        total_duration = len(y) / sr

        # セグメント検出
        detector = SegmentBoundaryDetector()
        boundaries = detector.detect(y, sr, percentile)

        # セグメント処理
        config = AnalysisConfig(
            rms_delta_percentile=percentile,
            min_len_sec=min_segment,
            max_len_sec=max_segment,
        )
        processor = SegmentProcessor()
        segments = processor.process(boundaries, total_duration, config)

        # 結果データ構築
        segment_data = []
        for i, (start, end) in enumerate(segments):
            segment_data.append(
                {
                    "segment_id": i,
                    "time_start_s": start,
                    "time_end_s": end,
                    "duration_s": end - start,
                }
            )

        # 出力
        output_dir.mkdir(parents=True, exist_ok=True)
        base_name = input_file.stem

        if output_format == "json":
            output_file = output_dir / f"{base_name}_segments.json"
            _save_segments_json(output_file, segment_data, input_file.name, config)
        elif output_format == "csv":
            output_file = output_dir / f"{base_name}_segments.csv"
            _save_segments_csv(output_file, segment_data)
        elif output_format == "yaml":
            output_file = output_dir / f"{base_name}_segments.yaml"
            _save_segments_yaml(output_file, segment_data, input_file.name, config)

        if not quiet:
            click.echo(f"✅ Segments saved to {output_file}")

        if verbose:
            click.echo(f"📊 Detected {len(segments)} segments")
            avg_duration = sum(end - start for start, end in segments) / len(segments)
            click.echo(f"⏱️  Average segment duration: {avg_duration:.1f} seconds")

        # 可視化プロット（オプション）
        if plot:
            try:
                plot_file = _create_segment_plot(
                    y, sr, segments, output_dir / f"{base_name}_segments.png"
                )
                if not quiet:
                    click.echo(f"📈 Plot saved to {plot_file}")
            except ImportError:
                click.echo("⚠️  matplotlib not available for plotting", err=True)

    except Exception as e:
        click.echo(f"❌ Error during segmentation: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        ctx.exit(1)


# ユーティリティコマンド群


@cli.command()
def examples():
    """Show usage examples."""
    examples_text = """
VocalInsight CLI Usage Examples:

📝 Basic Analysis:
   vocal-insight analyze recording.wav
   vocal-insight analyze recording.wav --output-dir ./results

🔧 Feature Extraction:
   vocal-insight extract recording.wav
   vocal-insight extract recording.wav --segment-start 10.0 --segment-end 20.0
   vocal-insight extract recording.wav --format csv

✂️  Segmentation:
   vocal-insight segment recording.wav
   vocal-insight segment recording.wav --plot
   vocal-insight segment recording.wav --min-segment 5.0 --max-segment 30.0

📊 Different Output Formats:
   vocal-insight analyze recording.wav --format json
   vocal-insight analyze recording.wav --format yaml
   vocal-insight extract recording.wav --format csv

🔍 Verbose Output:
   vocal-insight --verbose analyze recording.wav
   vocal-insight -v extract recording.wav --format json

🎯 Advanced Usage:
   vocal-insight analyze recording.wav --module acoustic --percentile 90
   vocal-insight segment recording.wav --percentile 85 --plot --output-dir ./analysis
"""
    click.echo(examples_text)


@cli.command()
def modules():
    """List available processing modules."""
    modules_text = """
Available Processing Modules:

🔄 auto      - Automatic module selection (default)
🎵 acoustic  - Standard acoustic feature extraction
🏗️  core      - Basic functionality only
🔙 legacy    - Original implementation (deprecated)

Usage:
   vocal-insight analyze --module acoustic recording.wav
   vocal-insight analyze --module legacy recording.wav  # for compatibility
"""
    click.echo(modules_text)


@cli.command()
def formats():
    """List supported output formats."""
    formats_text = """
Supported Output Formats:

📄 txt   - Human-readable text (LLM prompts) [analyze only]
📋 json  - Structured JSON data
📊 csv   - Comma-separated values [extract, segment only]  
📝 yaml  - YAML format

Usage:
   vocal-insight analyze --format json recording.wav
   vocal-insight extract --format csv recording.wav
   vocal-insight segment --format yaml recording.wav
"""
    click.echo(formats_text)


@cli.command()
@click.pass_context
def info(ctx):
    """Show system and version information."""
    import platform
    import sys

    info_text = f"""
VocalInsight AI System Information:

🖥️  System:
   Platform: {platform.system()} {platform.release()}
   Python: {sys.version.split()[0]}
   Architecture: {platform.machine()}

📦 Modules:
   vocal_insight: Available ✅
   vocal_insight_ai: Available ✅ (legacy)
   
🔧 Dependencies:
   librosa: Available ✅
   numpy: Available ✅
   parselmouth: Available ✅
   click: Available ✅
"""

    # オプション依存関係チェック
    try:
        import matplotlib

        info_text += f"   matplotlib: {matplotlib.__version__} ✅ (plotting enabled)\n"
    except ImportError:
        info_text += "   matplotlib: Not available ❌ (plotting disabled)\n"

    click.echo(info_text)


# ヘルパー関数群（実装時に詳細化）


def _generate_llm_prompt_from_segments(segments):
    """Generate an LLM prompt from segments."""
    # To be implemented in detail
    return "LLM Prompt generated from segments..."


# バリデーション共通関数
def _validate_segment_range(min_segment: float, max_segment: float, ctx) -> None:
    """Validate segment range parameters."""
    if min_segment >= max_segment:
        click.echo(
            f"Error: --min-segment ({min_segment}) must be less than --max-segment ({max_segment})",
            err=True,
        )
        ctx.exit(1)


def _validate_time_range(
    start_time: Optional[float], end_time: Optional[float], ctx
) -> None:
    """Validate time range parameters."""
    if start_time is not None and end_time is not None:
        if start_time >= end_time:
            click.echo(
                f"Error: --segment-start ({start_time}) must be less than --segment-end ({end_time})",
                err=True,
            )
            ctx.exit(1)


# ヘルパー関数群（実装時に詳細化）


def _generate_llm_prompt_from_segments(segments):
    """Generate an LLM prompt from segments."""
    # To be implemented in detail
    return "LLM Prompt generated from segments..."


def _save_text_format(output_file, analysis_results, llm_prompt):
    """Save results in text format."""
    # To be implemented in detail
    pass


def _save_json_format(output_file, analysis_results, filename, config):
    """Save results in JSON format."""
    # To be implemented in detail
    pass


def _save_yaml_format(output_file, analysis_results, filename, config):
    """Save results in YAML format."""
    # To be implemented in detail
    pass


def _save_features_json(output_file, features, filename):
    """Save features in JSON format."""
    # To be implemented in detail
    pass


def _save_features_csv(output_file, features):
    """Save features in CSV format."""
    # To be implemented in detail
    pass


def _save_features_yaml(output_file, features, filename):
    """Save features in YAML format."""
    # To be implemented in detail
    pass


def _save_segments_json(output_file, segments, filename, config):
    """Save segment information in JSON format."""
    # To be implemented in detail
    pass


def _save_segments_csv(output_file, segments):
    """Save segment information in CSV format."""
    # To be implemented in detail
    pass


def _save_segments_yaml(output_file, segments, filename, config):
    """Save segment information in YAML format."""
    # To be implemented in detail
    pass


def _create_segment_plot(audio, sr, segments, output_file):
    """Create a segment visualization plot."""
    # To be implemented in detail (using matplotlib)
    pass


if __name__ == "__main__":
    cli()
