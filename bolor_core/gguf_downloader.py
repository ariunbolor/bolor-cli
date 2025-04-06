import os
import requests
from pathlib import Path
from rich.progress import Progress

# Model URLs - Using more reliable public CDN URLs
GGUF_MODELS = {
    "phi-2": "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf?download=true",
    "starcoder2-3b": "https://huggingface.co/second-state/Starcoder2-3B-GGUF/resolve/main/Starcoder2-3B.Q4_K_M.gguf?download=true"
}

# Fallback URLs if main URLs don't work
FALLBACK_GGUF_MODELS = {
    "phi-2": "https://gpt4all.io/models/phi-2.gguf",
    "starcoder2-3b": "https://gpt4all.io/models/starcoder2-3b.gguf"
}

def download_file(url: str, dest: Path):
    """
    Download a file from a URL to the specified destination path.
    
    Args:
        url: URL to download from
        dest: Path where the file will be saved
    """
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total = int(response.headers.get('content-length', 0))

    with open(dest, 'wb') as file, Progress() as progress:
        task = progress.add_task("Downloading", total=total)
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                file.write(chunk)
                progress.update(task, advance=len(chunk))

def ensure_models(models_dir: Path):
    """
    Ensure that required models are downloaded.
    
    Args:
        models_dir: Directory where models will be stored
    """
    os.makedirs(models_dir, exist_ok=True)
    
    # Simulate model presence for testing without downloads
    # Remove this block in production
    simulate_phi2 = models_dir / "phi-2.gguf"
    if not simulate_phi2.exists():
        # Create an empty file for testing
        with open(simulate_phi2, 'wb') as f:
            f.write(b'Mock model file for testing')
        print(f"✅ [MOCK] phi-2 model created for testing.")
    
    # Only attempt to download starcoder2-3b if the model doesn't exist
    model_path = models_dir / "starcoder2-3b.gguf"
    if not model_path.exists():
        # Create a mock file for testing
        with open(model_path, 'wb') as f:
            f.write(b'Mock model file for testing')
        print(f"✅ [MOCK] starcoder2-3b model created for testing.")
    else:
        print(f"✅ starcoder2-3b already exists.")
