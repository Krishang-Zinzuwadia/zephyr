# Speech Recognition Module

The speech recognition module provides speech-to-text transcription using OpenAI's Whisper model via the faster-whisper library.

## Features

- **Multi-model support**: Choose from tiny, base, small, medium, or large models
- **Multi-language support**: Automatic language detection or specify language code
- **Streaming transcription**: Real-time transcription with partial results
- **Voice Activity Detection (VAD)**: Filters out silence and background noise
- **Model caching**: Keeps model in memory for faster subsequent transcriptions
- **Confidence scoring**: Provides confidence indicators for transcription quality

## Basic Usage

### Simple Transcription

```python
from zephyr.speech_recognition import SpeechRecognizer

# Initialize recognizer
recognizer = SpeechRecognizer(
    model_name="base",
    language="en"
)

# Transcribe audio
result = recognizer.transcribe(audio_data)

print(f"Text: {result.text}")
print(f"Confidence: {result.confidence}")
print(f"Language: {result.language}")

# Clean up
recognizer.unload_model()
```

### Streaming Transcription

```python
def on_transcription_update(text: str, is_final: bool):
    """Callback for streaming updates"""
    status = "FINAL" if is_final else "PARTIAL"
    print(f"[{status}] {text}")

# Start streaming
recognizer.start_streaming_transcription(
    callback=on_transcription_update,
    sample_rate=16000
)

# Process audio chunks as they arrive
for chunk in audio_chunks:
    recognizer.process_audio_chunk(chunk)

# Finalize
result = recognizer.finalize_transcription()
```

## Configuration Options

### Model Selection

Choose model based on accuracy vs. speed tradeoff:

- **tiny**: Fastest, lowest accuracy (~1GB RAM)
- **base**: Good balance (default) (~1.5GB RAM)
- **small**: Better accuracy (~2GB RAM)
- **medium**: High accuracy (~5GB RAM)
- **large**: Best accuracy (~10GB RAM)

### Language Options

- `"auto"`: Automatic language detection
- `"en"`: English
- `"es"`: Spanish
- `"fr"`: French
- `"de"`: German
- And many more...

### Voice Activity Detection

```python
recognizer = SpeechRecognizer(
    vad_enabled=True,
    vad_threshold=0.5  # 0.0 to 1.0
)
```

### Model Caching

```python
# Keep model in memory for 5 minutes after last use
recognizer.set_unload_timeout(300)

# Never unload model
recognizer.set_unload_timeout(0)
```

## API Reference

### SpeechRecognizer

#### Constructor

```python
SpeechRecognizer(
    model_name: str = "base",
    language: str = "auto",
    device: str = "cpu",
    compute_type: str = "int8",
    beam_size: int = 5,
    best_of: int = 5,
    temperature: float = 0.0,
    vad_enabled: bool = True,
    vad_threshold: float = 0.5
)
```

#### Methods

- `transcribe(audio_data, sample_rate=16000)` - Transcribe complete audio
- `start_streaming_transcription(callback, sample_rate=16000)` - Start streaming mode
- `process_audio_chunk(audio_chunk)` - Process audio chunk in streaming mode
- `finalize_transcription(audio_data=None)` - Finalize and get final result
- `stop_streaming_transcription()` - Stop streaming mode
- `set_language(language)` - Change transcription language
- `set_unload_timeout(seconds)` - Configure model unload timeout
- `unload_model()` - Manually unload model from memory
- `get_confidence_indicator(result)` - Get visual confidence indicator
- `is_low_confidence(result, threshold=0.7)` - Check if confidence is low

### TranscriptionResult

```python
@dataclass
class TranscriptionResult:
    text: str              # Transcribed text
    confidence: float      # Confidence score (0.0 to 1.0)
    language: str          # Detected/specified language
    duration: float        # Processing duration in seconds
    segments: List[TranscriptionSegment]  # Individual segments
    is_final: bool         # Whether this is the final result
```

### TranscriptionSegment

```python
@dataclass
class TranscriptionSegment:
    text: str              # Segment text
    start: float           # Start time in seconds
    end: float             # End time in seconds
    confidence: float      # Segment confidence score
```

## Error Handling

```python
from zephyr.speech_recognition import (
    TranscriptionError,
    ModelLoadError
)

try:
    result = recognizer.transcribe(audio_data)
except ModelLoadError as e:
    print(f"Failed to load model: {e}")
except TranscriptionError as e:
    print(f"Transcription failed: {e}")
```

## Performance Tips

1. **Use appropriate model size**: Start with "base" and adjust based on needs
2. **Enable model caching**: Set unload timeout to avoid reloading
3. **Use VAD**: Reduces processing of silence
4. **Use CPU for small models**: GPU overhead not worth it for tiny/base
5. **Batch processing**: Process multiple recordings before unloading model

## Requirements

- Python 3.11+
- faster-whisper >= 0.10.0
- numpy >= 1.24.0

## Examples

See `examples/speech_recognition_example.py` for complete working examples.
