import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import librosa
import yaml

# 新しいモジュールアーキテクチャのインポート
from vocal_insight import (
    AnalysisConfig,
    FeatureData,
    analyze_audio_segments,
)

# レガシー互換性のためのインポート
from vocal_insight_ai import analyze_audio_segments as legacy_analyze


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress all output except errors")
@click.version_option(version="0.1.0", prog_name="VocalInsight AI")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, quiet: bool):
    """VocalInsight AI - Advanced vocal analysis tool with modular architecture.

    This tool provides comprehensive vocal analysis including segment detection,
    acoustic feature extraction, and LLM prompt generation using a modular
    architecture for maximum flexibility and extensibility.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet

    if verbose and quiet:
        click.echo(
            "Error: --verbose and --quiet are mutually exclusive options.",
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
    help="Directory to save analysis results [default: current directory]",
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
    ctx: click.Context,
    input_file: Path,
    output_dir: Path,
    module: str,
    min_segment: float,
    max_segment: float,
    percentile: int,
    output_format: str,
):
    """Analyze an audio file and generate comprehensive analysis results.

    This command performs complete vocal analysis including segment detection,
    acoustic feature extraction, and LLM prompt generation. It maintains full
    backward compatibility with existing usage patterns while providing access
    to enhanced modular functionality.

    Examples:

        # Basic usage (existing compatibility)
        vocal-insight analyze recording.wav

        # Custom segment settings
        vocal-insight analyze recording.wav --min-segment 5.0 --max-segment 30.0

        # JSON output for structured data
        vocal-insight analyze recording.wav --format json --output-dir ./results

        # Use specific processing module
        vocal-insight analyze recording.wav --module acoustic --format yaml
    """
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    if not quiet:
        click.echo(f"🎵 Analyzing {input_file.name}...")

    # Parameter validation
    if min_segment >= max_segment:
        click.echo("Error: --min-segment must be less than --max-segment", err=True)
        ctx.exit(1)

    # Create configuration
    config = AnalysisConfig(
        rms_delta_percentile=percentile,
        min_len_sec=min_segment,
        max_len_sec=max_segment,
    )

    try:
        # Module dispatch
        if module == "legacy":
            if verbose:
                click.echo("📦 Using legacy module (vocal_insight_ai)")

            # Load audio file
            y, sr = librosa.load(input_file, sr=None)

            # Use legacy analysis
            analysis_results, llm_prompt = legacy_analyze(
                y, sr, input_file.name, config=config
            )

            # Convert to modern format for consistent output handling
            segments = analysis_results

        else:
            if verbose:
                click.echo("📦 Using new modular architecture (vocal_insight)")

            # Use new modular analysis
            segments = analyze_audio_segments(str(input_file), config)

            # Generate LLM prompt from segments
            llm_prompt = _generate_llm_prompt_from_segments(segments, input_file.name)

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate output filename
        base_name = input_file.stem

        # Save results based on format
        if output_format == "txt":
            output_file = output_dir / f"{base_name}_analysis.txt"
            _save_text_format(output_file, segments, llm_prompt)
        elif output_format == "json":
            output_file = output_dir / f"{base_name}_analysis.json"
            _save_json_format(output_file, segments, input_file.name, config)
        elif output_format == "yaml":
            output_file = output_dir / f"{base_name}_analysis.yaml"
            _save_yaml_format(output_file, segments, input_file.name, config)

        if not quiet:
            click.echo(f"✅ Analysis saved to {output_file}")

        if verbose:
            click.echo(f"📊 Analyzed {len(segments)} segments")
            if segments:
                total_duration = segments[-1].get("time_end_s", 0)
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
    help="Start time for partial extraction (seconds)",
)
@click.option(
    "--segment-end",
    type=float,
    help="End time for partial extraction (seconds)",
)
@click.pass_context
def extract(
    ctx: click.Context,
    input_file: Path,
    output_dir: Path,
    output_format: str,
    extractor: str,
    segment_start: Optional[float],
    segment_end: Optional[float],
):
    """Extract acoustic features from an audio file.

    This command performs only feature extraction without full analysis,
    useful for obtaining structured feature data or analyzing specific
    time segments of recordings.

    Examples:

        # Extract features from entire file
        vocal-insight extract recording.wav

        # Extract features from specific time range
        vocal-insight extract recording.wav --segment-start 10.0 --segment-end 20.0

        # Output as CSV for data analysis
        vocal-insight extract recording.wav --format csv --output-dir ./features
    """
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    if not quiet:
        click.echo(f"🔍 Extracting features from {input_file.name}...")

    # Validate time range
    if segment_start is not None and segment_end is not None:
        if segment_start >= segment_end:
            click.echo(
                "Error: --segment-start must be less than --segment-end", err=True
            )
            ctx.exit(1)

    try:
        # Load audio
        y, sr = librosa.load(input_file, sr=None)

        # Apply time range if specified
        if segment_start is not None or segment_end is not None:
            start_sample = int(segment_start * sr) if segment_start is not None else 0
            end_sample = int(segment_end * sr) if segment_end is not None else len(y)
            y = y[start_sample:end_sample]

            if verbose:
                duration = (end_sample - start_sample) / sr
                click.echo(
                    f"📐 Analyzing segment: {segment_start or 0:.1f}s - {segment_end or duration:.1f}s"
                )

        # Extract features using new modular system
        from vocal_insight.features import AcousticFeatureExtractor

        extractor_instance = AcousticFeatureExtractor()
        features = extractor_instance.extract(y, sr)

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        base_name = input_file.stem

        # Save features
        if output_format == "json":
            output_file = output_dir / f"{base_name}_features.json"
            _save_features_json(
                output_file, features, input_file.name, segment_start, segment_end
            )
        elif output_format == "csv":
            output_file = output_dir / f"{base_name}_features.csv"
            _save_features_csv(output_file, features)
        elif output_format == "yaml":
            output_file = output_dir / f"{base_name}_features.yaml"
            _save_features_yaml(
                output_file, features, input_file.name, segment_start, segment_end
            )

        if not quiet:
            click.echo(f"✅ Features saved to {output_file}")

        if verbose:
            click.echo(f"📊 Extracted {len(features)} feature values")

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
    "--plot",
    is_flag=True,
    help="Generate visualization plot of segments (requires matplotlib)",
)
@click.pass_context
def segment(
    ctx: click.Context,
    input_file: Path,
    output_dir: Path,
    output_format: str,
    min_segment: float,
    max_segment: float,
    percentile: int,
    plot: bool,
):
    """Detect and analyze segments in an audio file.

    This command performs only segment boundary detection without full
    feature extraction, useful for understanding the temporal structure
    of recordings.

    Examples:

        # Basic segment detection
        vocal-insight segment recording.wav

        # Generate visualization
        vocal-insight segment recording.wav --plot --output-dir ./segments

        # Custom segment parameters
        vocal-insight segment recording.wav --min-segment 5.0 --percentile 90
    """
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    if not quiet:
        click.echo(f"✂️  Detecting segments in {input_file.name}...")

    # Parameter validation
    if min_segment >= max_segment:
        click.echo("Error: --min-segment must be less than --max-segment", err=True)
        ctx.exit(1)

    try:
        # Use new modular system for segment detection
        from vocal_insight.segments import SegmentBoundaryDetector, SegmentProcessor

        # Load audio
        y, sr = librosa.load(input_file, sr=None)

        # Detect boundaries
        detector = SegmentBoundaryDetector()
        boundaries = detector.detect_boundaries(y, sr, percentile)

        # Process segments
        processor = SegmentProcessor()
        segments = processor.process_boundaries(
            boundaries, len(y), sr, min_segment, max_segment
        )

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        base_name = input_file.stem

        # Save segment data
        if output_format == "json":
            output_file = output_dir / f"{base_name}_segments.json"
            _save_segments_json(output_file, segments, input_file.name)
        elif output_format == "csv":
            output_file = output_dir / f"{base_name}_segments.csv"
            _save_segments_csv(output_file, segments)
        elif output_format == "yaml":
            output_file = output_dir / f"{base_name}_segments.yaml"
            _save_segments_yaml(output_file, segments, input_file.name)

        # Generate plot if requested
        if plot:
            plot_file = output_dir / f"{base_name}_segments.png"
            _generate_segment_plot(plot_file, y, sr, segments)
            if not quiet:
                click.echo(f"📊 Plot saved to {plot_file}")

        if not quiet:
            click.echo(f"✅ Segment data saved to {output_file}")

        if verbose:
            click.echo(f"📐 Detected {len(segments)} segments")
            total_duration = segments[-1]["time_end_s"] if segments else 0
            click.echo(f"⏱️  Total duration: {total_duration:.1f} seconds")

    except Exception as e:
        click.echo(f"❌ Error during segment detection: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        ctx.exit(1)


@cli.command()
def examples():
    """Show usage examples for different commands and scenarios."""
    click.echo("""
🎵 VocalInsight AI Usage Examples

Basic Analysis:
  vocal-insight analyze recording.wav
  vocal-insight analyze recording.wav --verbose

Custom Settings:
  vocal-insight analyze recording.wav --min-segment 5.0 --max-segment 30.0
  vocal-insight analyze recording.wav --percentile 90 --format json

Structured Output:
  vocal-insight analyze recording.wav --format json --output-dir ./results
  vocal-insight analyze recording.wav --format yaml --quiet

Feature Extraction:
  vocal-insight extract recording.wav --format csv
  vocal-insight extract recording.wav --segment-start 10.0 --segment-end 20.0

Segment Detection:
  vocal-insight segment recording.wav --plot
  vocal-insight segment recording.wav --min-segment 5.0 --format yaml

Module Selection:
  vocal-insight analyze recording.wav --module acoustic
  vocal-insight analyze recording.wav --module legacy

Batch Processing:
  vocal-insight --quiet analyze *.wav --format json --output-dir ./batch

Get Help:
  vocal-insight --help
  vocal-insight analyze --help
  vocal-insight modules
""")


@cli.command()
def modules():
    """Show available processing modules and their descriptions."""
    click.echo("""
📦 Available Processing Modules

auto:
  Automatically selects the best available module (default)
  
acoustic:
  Advanced acoustic feature extraction using new modular architecture
  - F0 (fundamental frequency) analysis
  - HNR (harmonics-to-noise ratio) 
  - Formant frequency detection (F1, F2, F3)
  
core:
  Basic feature extraction with essential functionality
  
legacy:
  Original implementation for backward compatibility
  - Use only when compatibility issues arise
  - Will be deprecated in future versions

Usage:
  vocal-insight analyze file.wav --module acoustic
  vocal-insight analyze file.wav --module legacy
""")


@cli.command()
def formats():
    """Show supported output formats and their use cases."""
    click.echo("""
📄 Supported Output Formats

txt (Text):
  Human-readable LLM prompt format (default for analyze)
  - Compatible with existing workflows
  - Includes analysis summary and prompts
  
json (JSON):
  Structured data format for programmatic use
  - Machine-readable
  - Complete metadata included
  - Ideal for API integration
  
yaml (YAML):
  Human-readable structured format
  - Easy to read and edit
  - Good for configuration and documentation
  
csv (CSV):
  Tabular data format (features and segments only)
  - Compatible with spreadsheet applications
  - Ideal for data analysis and visualization
  - Available for extract and segment commands

Usage Examples:
  vocal-insight analyze file.wav --format json
  vocal-insight extract file.wav --format csv
  vocal-insight segment file.wav --format yaml
""")


@cli.command()
def info():
    """Display system and version information."""
    import platform
    import sys

    try:
        import librosa

        librosa_version = librosa.__version__
    except ImportError:
        librosa_version = "not installed"

    try:
        import parselmouth

        praat_version = parselmouth.__version__
    except ImportError:
        praat_version = "not installed"

    click.echo(f"""
🔍 VocalInsight AI System Information

Version: 0.1.0
Python: {sys.version}
Platform: {platform.system()} {platform.release()}

Dependencies:
  librosa: {librosa_version}
  parselmouth: {praat_version}
  click: {click.__version__}

Module Architecture:
  vocal_insight: Available
  vocal_insight_ai: Available (legacy)
  
Supported Audio Formats:
  WAV, FLAC, MP3, M4A, OGG (via librosa)
""")


# Helper functions for output formatting
def _generate_llm_prompt_from_segments(
    segments: List[Dict[str, Any]], filename: str
) -> str:
    """Generate LLM prompt from segment analysis results."""
    prompt_parts = [
        f"Vocal Analysis Results for {filename}",
        "=" * (len(filename) + 28),
        "",
        f"Audio file: {filename}",
        f"Total segments analyzed: {len(segments)}",
        "",
    ]

    for i, segment in enumerate(segments):
        prompt_parts.extend(
            [
                f"Segment {i}:",
                f"  Time range: {segment.get('time_start_s', 0):.1f}s - {segment.get('time_end_s', 0):.1f}s",
                f"  Duration: {segment.get('time_end_s', 0) - segment.get('time_start_s', 0):.1f}s",
            ]
        )

        if "features" in segment:
            features = segment["features"]
            prompt_parts.extend(
                [
                    f"  F0 mean: {features.get('f0_mean_hz', 0):.1f} Hz",
                    f"  F0 std: {features.get('f0_std_hz', 0):.1f} Hz",
                    f"  HNR mean: {features.get('hnr_mean_db', 0):.1f} dB",
                    f"  F1 mean: {features.get('f1_mean_hz', 0):.1f} Hz",
                    f"  F2 mean: {features.get('f2_mean_hz', 0):.1f} Hz",
                    f"  F3 mean: {features.get('f3_mean_hz', 0):.1f} Hz",
                ]
            )
        prompt_parts.append("")

    return "\n".join(prompt_parts)


def _save_text_format(
    output_file: Path, segments: List[Dict[str, Any]], llm_prompt: str
):
    """Save analysis results in text format."""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(llm_prompt)


def _save_json_format(
    output_file: Path,
    segments: List[Dict[str, Any]],
    filename: str,
    config: AnalysisConfig,
):
    """Save analysis results in JSON format."""
    data = {
        "filename": filename,
        "analysis_config": {
            "rms_delta_percentile": config["rms_delta_percentile"],
            "min_len_sec": config["min_len_sec"],
            "max_len_sec": config["max_len_sec"],
        },
        "segments": segments,
        "metadata": {
            "total_segments": len(segments),
            "total_duration_s": segments[-1].get("time_end_s", 0) if segments else 0,
        },
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _save_yaml_format(
    output_file: Path,
    segments: List[Dict[str, Any]],
    filename: str,
    config: AnalysisConfig,
):
    """Save analysis results in YAML format."""
    data = {
        "filename": filename,
        "analysis_config": {
            "rms_delta_percentile": config["rms_delta_percentile"],
            "min_len_sec": config["min_len_sec"],
            "max_len_sec": config["max_len_sec"],
        },
        "segments": segments,
        "metadata": {
            "total_segments": len(segments),
            "total_duration_s": segments[-1].get("time_end_s", 0) if segments else 0,
        },
    }

    with open(output_file, "w", encoding="utf-8") as f:
        yaml.dump(
            data, f, default_flow_style=False, allow_unicode=True, sort_keys=False
        )


def _save_features_json(
    output_file: Path,
    features: FeatureData,
    filename: str,
    start_time: Optional[float],
    end_time: Optional[float],
):
    """Save features in JSON format."""
    data = {
        "filename": filename,
        "time_range": {
            "start_s": start_time,
            "end_s": end_time,
        }
        if start_time is not None or end_time is not None
        else None,
        "features": dict(features),
        "metadata": {
            "extraction_method": "acoustic",
            "feature_count": len(features),
        },
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _save_features_csv(output_file: Path, features: FeatureData):
    """Save features in CSV format."""
    import csv

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["feature", "value"])
        for key, value in features.items():
            writer.writerow([key, value])


def _save_features_yaml(
    output_file: Path,
    features: FeatureData,
    filename: str,
    start_time: Optional[float],
    end_time: Optional[float],
):
    """Save features in YAML format."""
    data = {
        "filename": filename,
        "time_range": {
            "start_s": start_time,
            "end_s": end_time,
        }
        if start_time is not None or end_time is not None
        else None,
        "features": dict(features),
        "metadata": {
            "extraction_method": "acoustic",
            "feature_count": len(features),
        },
    }

    with open(output_file, "w", encoding="utf-8") as f:
        yaml.dump(
            data, f, default_flow_style=False, allow_unicode=True, sort_keys=False
        )


def _save_segments_json(
    output_file: Path, segments: List[Dict[str, Any]], filename: str
):
    """Save segments in JSON format."""
    data = {
        "filename": filename,
        "segments": segments,
        "metadata": {
            "total_segments": len(segments),
            "total_duration_s": segments[-1].get("time_end_s", 0) if segments else 0,
        },
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _save_segments_csv(output_file: Path, segments: List[Dict[str, Any]]):
    """Save segments in CSV format."""
    import csv

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        if not segments:
            return

        writer = csv.DictWriter(
            f, fieldnames=["segment_id", "time_start_s", "time_end_s", "duration_s"]
        )
        writer.writeheader()

        for i, segment in enumerate(segments):
            writer.writerow(
                {
                    "segment_id": i,
                    "time_start_s": segment.get("time_start_s", 0),
                    "time_end_s": segment.get("time_end_s", 0),
                    "duration_s": segment.get("time_end_s", 0)
                    - segment.get("time_start_s", 0),
                }
            )


def _save_segments_yaml(
    output_file: Path, segments: List[Dict[str, Any]], filename: str
):
    """Save segments in YAML format."""
    data = {
        "filename": filename,
        "segments": segments,
        "metadata": {
            "total_segments": len(segments),
            "total_duration_s": segments[-1].get("time_end_s", 0) if segments else 0,
        },
    }

    with open(output_file, "w", encoding="utf-8") as f:
        yaml.dump(
            data, f, default_flow_style=False, allow_unicode=True, sort_keys=False
        )


def _generate_segment_plot(
    output_file: Path, y: Any, sr: int, segments: List[Dict[str, Any]]
):
    """Generate visualization plot of segments."""
    try:
        import matplotlib.pyplot as plt
        import numpy as np

        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

        # Time axis
        time = np.arange(len(y)) / sr

        # Plot waveform
        ax1.plot(time, y, alpha=0.7, color="blue")
        ax1.set_ylabel("Amplitude")
        ax1.set_title("Audio Waveform with Detected Segments")
        ax1.grid(True, alpha=0.3)

        # Plot RMS
        frame_length = 2048
        hop_length = 512
        rms = librosa.feature.rms(
            y=y, frame_length=frame_length, hop_length=hop_length
        )[0]
        rms_time = librosa.frames_to_time(
            np.arange(len(rms)), sr=sr, hop_length=hop_length
        )

        ax2.plot(rms_time, rms, color="orange", label="RMS Energy")
        ax2.set_xlabel("Time (seconds)")
        ax2.set_ylabel("RMS Energy")
        ax2.set_title("RMS Energy with Segment Boundaries")
        ax2.grid(True, alpha=0.3)

        # Add segment boundaries
        for i, segment in enumerate(segments):
            start_time = segment.get("time_start_s", 0)
            end_time = segment.get("time_end_s", 0)

            # Vertical lines for boundaries
            for ax in [ax1, ax2]:
                ax.axvline(
                    start_time, color="red", linestyle="--", alpha=0.7, linewidth=1
                )
                ax.axvline(
                    end_time, color="red", linestyle="--", alpha=0.7, linewidth=1
                )

            # Segment labels
            mid_time = (start_time + end_time) / 2
            ax1.annotate(
                f"S{i}",
                xy=(mid_time, 0),
                xytext=(mid_time, ax1.get_ylim()[1] * 0.8),
                ha="center",
                va="center",
                fontsize=8,
                alpha=0.8,
            )

        ax2.legend()
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches="tight")
        plt.close()

    except ImportError:
        # matplotlib not available
        click.echo(
            "Warning: matplotlib not available, skipping plot generation", err=True
        )


if __name__ == "__main__":
    cli()
