import click
import os
import librosa
import soundfile as sf
from vocal_insight_ai import analyze_audio_segments, default_analysis_config

@click.group()
def cli():
    """VocalInsight AI CLI Tool"""
    pass

@cli.command()
@click.argument('input_file', type=click.Path(exists=True, dir_okay=False))
@click.option('--output-dir', type=click.Path(file_okay=False), default='.', help='Directory to save the generated prompt. Defaults to current directory.')
@click.option('--temp-dir', type=click.Path(file_okay=False), default='temp_segments', help='Temporary directory for segment audio files. Will be created and removed.')
def analyze(
    input_file: str,
    output_dir: str,
    temp_dir: str
):
    """Analyze an audio file and generate an LLM prompt."""
    click.echo(f"Analyzing {input_file}...")

    # Load audio file
    y, sr = librosa.load(input_file, sr=None)

    # Extract filename without extension
    filename_without_ext = os.path.splitext(os.path.basename(input_file))[0]
    
    # Analyze audio segments and generate prompt
    try:
        # Note: The core library vocal_insight_ai is now pure and does not handle file I/O for segments.
        # For CLI, we need to manage temporary segment files if analyze_segment_with_praat still expects file paths.
        # However, analyze_segment_with_praat was refactored to accept numpy arrays directly.
        # So, we don't need to create temp files for praat analysis anymore.
        # The `temp_dir` option is currently not used by the core library, but kept for future potential use or if segment saving is desired.

        analysis_results, llm_prompt = analyze_audio_segments(y, sr, os.path.basename(input_file), config=default_analysis_config)

        # Save the generated prompt to a file
        os.makedirs(output_dir, exist_ok=True)
        output_filepath = os.path.join(output_dir, f"{filename_without_ext}_prompt.txt")
        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(llm_prompt)
        click.echo(f"LLM prompt saved to {output_filepath}")

    except Exception as e:
        click.echo(f"Error during analysis: {e}", err=True)
        exit(1)

if __name__ == '__main__':
    cli()