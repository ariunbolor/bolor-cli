"""
Dataset loader module for Bolor code repair.

This module provides functionality for downloading and loading datasets and
models used by Bolor.
"""

import os
import json
import zipfile
import tarfile
import tempfile
import logging
import warnings
import requests
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

# Silence the annoying urllib3/requests warnings in a way that works with both urllib3 v1.x and v2.x
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", module="requests")
warnings.filterwarnings("ignore", module="urllib3")

# Handle urllib3 warnings more robustly since the API changed between versions
try:
    # For direct urllib3 imports
    import urllib3
    # Silence specific warning types if they exist
    for warning_type in ["InsecureRequestWarning", "InsecurePlatformWarning", "SNIMissingWarning"]:
        try:
            warning_class = getattr(urllib3.exceptions, warning_type, None)
            if warning_class is not None:
                warnings.filterwarnings("ignore", category=warning_class)
        except (AttributeError, ImportError):
            pass
    
    # For requests package urllib3 warnings (legacy path)
    try:
        if hasattr(requests, "packages") and hasattr(requests.packages, "urllib3"):
            for warning_type in ["InsecureRequestWarning", "InsecurePlatformWarning", "SNIMissingWarning"]:
                try:
                    warning_class = getattr(requests.packages.urllib3.exceptions, warning_type, None)
                    if warning_class is not None:
                        warnings.filterwarnings("ignore", category=warning_class)
                except (AttributeError, ImportError):
                    pass
    except (AttributeError, ImportError):
        pass
except (AttributeError, ImportError):
    pass

import chromadb
from tqdm import tqdm

from bolor.utils.config import Config


class DatasetLoader:
    """
    Dataset loader class for Bolor code repair.
    
    This class is responsible for downloading, preparing, and managing the
    datasets and models used by Bolor.
    """
    
    def __init__(self, config: Config):
        """
        Initialize a new DatasetLoader instance.
        
        Args:
            config: Configuration object containing dataset settings.
        """
        self.config = config
        self.verbose = config.get("verbose", False)
        self.force_download = config.get("force_download", False)
        
        # Set up paths
        self.models_dir = self.config.get_path("models_dir")
        self.datasets_dir = self.config.get_path("datasets_dir")
        self.vector_store_dir = self.config.get_path("vector_store_dir")
        self.cache_dir = self.config.get_path("cache_dir")
        
        # Initialize logger
        self.logger = logging.getLogger("bolor.dataset_loader")
        if self.verbose:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
    
    def download_model(self, force: Optional[bool] = None) -> Path:
        """
        Download the model if it doesn't exist.
        
        Args:
            force: If True, force re-download even if the model exists.
                  If None, use the value from config.
                  
        Returns:
            Path to the downloaded model.
        """
        if force is None:
            force = self.force_download
        
        # Get model information from config
        model_name = self.config.get("model.name", "phi-2")
        model_file = self.config.get("model.file", "phi-2.Q4_K_M.gguf")
        model_url = self.config.get("model.url", "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf")
        fallback_model_file = "phi-2.Q2_K.gguf"  # Smaller fallback model
        fallback_model_url = "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q2_K.gguf"
        
        # Create the model directory if it doesn't exist
        model_dir = self.models_dir / model_name
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Set the paths
        model_path = model_dir / model_file
        fallback_model_path = model_dir / fallback_model_file
        
        # Check if the model already exists and works
        if model_path.exists() and not force:
            # Verify the model can be loaded
            if self._test_model_loading(model_path):
                self.logger.info(f"Model {model_name} already exists and works at {model_path}")
                return model_path
            else:
                self.logger.warning(f"Existing model at {model_path} cannot be loaded. Attempting to fix...")
                # Fall through to download/fix
        
        # Try to download the smaller fallback model first (more reliable)
        self.logger.info(f"Downloading fallback model {fallback_model_file} from {fallback_model_url}")
        try:
            if not fallback_model_path.exists() or force:
                self._download_file(fallback_model_url, fallback_model_path)
                
            # Verify the fallback model
            if self._test_model_loading(fallback_model_path):
                self.logger.info(f"Fallback model successfully loaded from {fallback_model_path}")
                # Update the config to use this model as the default
                self._update_model_config(fallback_model_file)
                return fallback_model_path
            else:
                self.logger.warning(f"Fallback model cannot be loaded. Attempting primary model...")
        except Exception as e:
            self.logger.warning(f"Error downloading fallback model: {e}")
        
        # Try the primary model if fallback failed
        try:
            # Download the primary model if it doesn't exist or force is True
            if not model_path.exists() or force:
                self.logger.info(f"Downloading primary model {model_name} from {model_url}")
                self._download_file(model_url, model_path)
            
            # Verify the primary model
            if self._test_model_loading(model_path):
                self.logger.info(f"Primary model successfully loaded from {model_path}")
                # Update the config to use this model as the default
                self._update_model_config(model_file)
                return model_path
        except Exception as e:
            self.logger.warning(f"Error downloading primary model: {e}")
        
        # If we got here, neither model works
        self.logger.error("Failed to load any model. LLM functionality will not work.")
        
        # Return fallback path anyway as best effort
        if fallback_model_path.exists():
            return fallback_model_path
        return model_path
        
    def _test_model_loading(self, model_path: Path) -> bool:
        """
        Test if a model can be loaded.
        
        Args:
            model_path: Path to the model file.
            
        Returns:
            True if the model can be loaded, False otherwise.
        """
        self.logger.info(f"Testing if model at {model_path} can be loaded...")
        try:
            from ctransformers import AutoModelForCausalLM
            
            # Try different model types since 'phi' might not be supported in this version
            model_types = ["phi", "gpt2", "llama"]
            
            for model_type in model_types:
                try:
                    self.logger.info(f"Trying to load with model type: {model_type}")
                    model = AutoModelForCausalLM.from_pretrained(
                        str(model_path.parent),
                        model_file=model_path.name,
                        model_type=model_type
                    )
                    
                    # Test a simple generation
                    test_input = "Hello, my name is"
                    output = model(test_input, max_new_tokens=5)
                    self.logger.info(f"Model loaded successfully with type {model_type}")
                    
                    # Store the successful model type for configuration
                    self._successful_model_type = model_type
                    return True
                except Exception as e:
                    self.logger.debug(f"Failed to load with model type {model_type}: {e}")
                    continue
            
            self.logger.warning("Failed to load model with any known model type")
            return False
            
        except ImportError:
            self.logger.error("ctransformers not installed. Please install with 'pip install ctransformers'")
            return False
        except Exception as e:
            self.logger.error(f"Error testing model loading: {e}")
            return False
    
    def _update_model_config(self, model_file: str) -> None:
        """
        Update the model configuration.
        
        Args:
            model_file: The model filename to set as default.
        """
        try:
            model_name = self.config.get("model.name", "phi-2")
            model_type = getattr(self, "_successful_model_type", "phi")
            
            # Update the in-memory config
            self.config.set("model.file", model_file)
            self.config.set("model.type", model_type)
            
            # Save to disk
            self.config.save()
            
            self.logger.info(f"Updated model configuration: name={model_name}, file={model_file}, type={model_type}")
        except Exception as e:
            self.logger.warning(f"Error updating model config: {e}")
    
    def download_datasets(self, force: Optional[bool] = None) -> Dict[str, Path]:
        """
        Download and prepare datasets.
        
        Args:
            force: If True, force re-download even if the datasets exist.
                  If None, use the value from config.
                  
        Returns:
            Dictionary mapping dataset names to their paths.
        """
        if force is None:
            force = self.force_download
        
        # Get dataset information from config
        datasets_config = self.config.get("datasets", {})
        
        # Dictionary to store dataset paths
        dataset_paths = {}
        
        # Download and prepare each dataset
        for dataset_name, dataset_config in datasets_config.items():
            if not dataset_config.get("enabled", True):
                self.logger.info(f"Dataset {dataset_name} is disabled, skipping")
                continue
            
            dataset_url = dataset_config.get("url")
            if not dataset_url:
                self.logger.warning(f"No URL provided for dataset {dataset_name}, skipping")
                continue
            
            # Create the dataset directory
            dataset_dir = self.datasets_dir / dataset_name
            dataset_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if the dataset already exists
            if dataset_dir.exists() and list(dataset_dir.glob("*")) and not force:
                self.logger.info(f"Dataset {dataset_name} already exists at {dataset_dir}")
                dataset_paths[dataset_name] = dataset_dir
                continue
            
            # Download and prepare the dataset
            self.logger.info(f"Downloading dataset {dataset_name} from {dataset_url}")
            try:
                if dataset_name == "codexglue":
                    self._download_and_prepare_codexglue(dataset_url, dataset_dir)
                elif dataset_name == "mbpp":
                    self._download_and_prepare_mbpp(dataset_url, dataset_dir)
                elif dataset_name == "quixbugs":
                    self._download_and_prepare_quixbugs(dataset_url, dataset_dir)
                else:
                    self.logger.warning(f"Unknown dataset {dataset_name}, using generic download")
                    self._download_generic_dataset(dataset_url, dataset_dir)
                
                dataset_paths[dataset_name] = dataset_dir
                
            except Exception as e:
                self.logger.error(f"Error downloading dataset {dataset_name}: {str(e)}")
        
        return dataset_paths
    
    def build_vector_store(self, force: Optional[bool] = None) -> Path:
        """
        Build a vector store from the downloaded datasets.
        
        Args:
            force: If True, force rebuild even if the vector store exists.
                  If None, use the value from config.
                  
        Returns:
            Path to the vector store.
        """
        if force is None:
            force = self.force_download
        
        # Create the vector store directory
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if the vector store already exists
        if self.vector_store_dir.exists() and list(self.vector_store_dir.glob("*")) and not force:
            self.logger.info(f"Vector store already exists at {self.vector_store_dir}")
            return self.vector_store_dir
        
        # Initialize a chromadb client
        try:
            client = chromadb.PersistentClient(path=str(self.vector_store_dir))
            
            # Create or get collections for different types of data
            bug_fixes_collection = client.get_or_create_collection("bug_fixes")
            code_patterns_collection = client.get_or_create_collection("code_patterns")
            
            # Process all datasets and add to vector store
            self.logger.info(f"Building vector store at {self.vector_store_dir}")
            
            # Process CodeXGLUE dataset if available
            codexglue_dir = self.datasets_dir / "codexglue"
            if codexglue_dir.exists():
                self._process_codexglue_for_vector_store(codexglue_dir, bug_fixes_collection)
            
            # Process MBPP dataset if available
            mbpp_dir = self.datasets_dir / "mbpp"
            if mbpp_dir.exists():
                self._process_mbpp_for_vector_store(mbpp_dir, code_patterns_collection)
            
            # Process QuixBugs dataset if available
            quixbugs_dir = self.datasets_dir / "quixbugs"
            if quixbugs_dir.exists():
                self._process_quixbugs_for_vector_store(quixbugs_dir, bug_fixes_collection)
            
            self.logger.info(f"Vector store built successfully at {self.vector_store_dir}")
            
        except ImportError:
            self.logger.warning("chromadb not available, skipping vector store creation")
        except Exception as e:
            self.logger.error(f"Error building vector store: {str(e)}")
        
        return self.vector_store_dir
    
    def get_vector_store_client(self) -> "chromadb.PersistentClient":
        """
        Get a chromadb client for the vector store.
        
        Returns:
            chromadb.PersistentClient instance.
            
        Raises:
            ImportError: If chromadb is not installed.
            FileNotFoundError: If the vector store does not exist.
        """
        try:
            import chromadb
        except ImportError:
            raise ImportError("chromadb not installed. Install it with 'pip install chromadb'")
        
        if not self.vector_store_dir.exists():
            raise FileNotFoundError(f"Vector store not found at {self.vector_store_dir}. Create it with download_resources command.")
        
        return chromadb.PersistentClient(path=str(self.vector_store_dir))
    
    def query_similar_bugs(self, error_message: str, code_snippet: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Query the vector store for similar bugs based on error message and code snippet.
        
        Args:
            error_message: Error message to search for.
            code_snippet: Code snippet where the error occurred.
            limit: Maximum number of results to return.
            
        Returns:
            List of similar bugs with metadata.
        """
        try:
            client = self.get_vector_store_client()
            collection = client.get_collection("bug_fixes")
            
            # Combine error message and code snippet for query
            query_text = f"{error_message}\n\n{code_snippet}"
            
            # Query the collection
            results = collection.query(
                query_texts=[query_text],
                n_results=limit
            )
            
            # Process and return results
            if not results["documents"]:
                return []
            
            # Convert to list of dictionaries
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]
            
            # Combine into a list of dictionaries
            return [
                {"document": doc, "metadata": meta, "distance": dist}
                for doc, meta, dist in zip(documents, metadatas, distances)
            ]
            
        except (ImportError, FileNotFoundError) as e:
            self.logger.warning(f"Could not query vector store: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Error querying vector store: {str(e)}")
            return []
    
    def _download_file(self, url: str, dest_path: Path, chunk_size: int = 8192) -> None:
        """
        Download a file from a URL to a local path.
        
        Args:
            url: URL to download from.
            dest_path: Local path to save the file to.
            chunk_size: Size of chunks to download.
            
        Raises:
            Exception: If the download fails.
        """
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Get the file size if available
            file_size = int(response.headers.get('content-length', 0))
            
            # Create a progress bar
            progress_bar = None
            if self.verbose and file_size > 0:
                progress_bar = tqdm(
                    total=file_size,
                    unit='B',
                    unit_scale=True,
                    desc=dest_path.name
                )
            
            # Write the file
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
                        if progress_bar:
                            progress_bar.update(len(chunk))
            
            if progress_bar:
                progress_bar.close()
                
        except Exception as e:
            # Clean up the file if it was partially downloaded
            if dest_path.exists():
                dest_path.unlink()
            
            raise Exception(f"Error downloading file: {str(e)}")
    
    def _download_and_prepare_codexglue(self, url: str, dataset_dir: Path) -> None:
        """
        Download and prepare the CodeXGLUE dataset.
        
        Args:
            url: URL to download from.
            dataset_dir: Directory to save the dataset to.
        """
        # Download to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as temp_file:
            self._download_file(url, Path(temp_file.name))
            
            # Extract the archive
            with tarfile.open(temp_file.name, 'r:gz') as tar:
                tar.extractall(path=dataset_dir)
            
            # Clean up
            os.unlink(temp_file.name)
        
        # Process the dataset as needed
        self.logger.info(f"CodeXGLUE dataset prepared at {dataset_dir}")
    
    def _download_and_prepare_mbpp(self, url: str, dataset_dir: Path) -> None:
        """
        Download and prepare the MBPP dataset.
        
        Args:
            url: URL to download from.
            dataset_dir: Directory to save the dataset to.
        """
        # Download the JSONL file
        jsonl_path = dataset_dir / "mbpp.jsonl"
        self._download_file(url, jsonl_path)
        
        # Convert to a more usable format
        examples = []
        with open(jsonl_path, 'r') as f:
            for line in f:
                example = json.loads(line)
                examples.append(example)
        
        # Save as JSON
        with open(dataset_dir / "mbpp.json", 'w') as f:
            json.dump(examples, f, indent=2)
        
        self.logger.info(f"MBPP dataset prepared at {dataset_dir}")
    
    def _download_and_prepare_quixbugs(self, url: str, dataset_dir: Path) -> None:
        """
        Download and prepare the QuixBugs dataset.
        
        Args:
            url: URL to download from.
            dataset_dir: Directory to save the dataset to.
        """
        # Download to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
            self._download_file(url, Path(temp_file.name))
            
            # Extract the archive
            with zipfile.ZipFile(temp_file.name, 'r') as zip_ref:
                zip_ref.extractall(path=dataset_dir)
            
            # Clean up
            os.unlink(temp_file.name)
        
        # The files are extracted to a subdirectory, move them up
        for item in dataset_dir.glob("QuixBugs-*/*"):
            if item.is_dir():
                shutil.copytree(item, dataset_dir / item.name, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dataset_dir)
        
        # Remove the now-empty subdirectory
        for item in dataset_dir.glob("QuixBugs-*"):
            if item.is_dir():
                shutil.rmtree(item)
        
        self.logger.info(f"QuixBugs dataset prepared at {dataset_dir}")
    
    def _download_generic_dataset(self, url: str, dataset_dir: Path) -> None:
        """
        Download and prepare a generic dataset.
        
        Args:
            url: URL to download from.
            dataset_dir: Directory to save the dataset to.
        """
        # Determine the file extension
        file_name = url.split("/")[-1]
        download_path = dataset_dir / file_name
        
        # Download the file
        self._download_file(url, download_path)
        
        # Extract if it's an archive
        if file_name.endswith(".zip"):
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(path=dataset_dir)
            
            # Clean up
            download_path.unlink()
            
        elif file_name.endswith(".tar.gz") or file_name.endswith(".tgz"):
            with tarfile.open(download_path, 'r:gz') as tar:
                tar.extractall(path=dataset_dir)
            
            # Clean up
            download_path.unlink()
        
        self.logger.info(f"Generic dataset prepared at {dataset_dir}")
    
    def _process_codexglue_for_vector_store(self, codexglue_dir: Path, collection: "chromadb.Collection") -> None:
        """
        Process the CodeXGLUE dataset for the vector store.
        
        Args:
            codexglue_dir: Directory containing the CodeXGLUE dataset.
            collection: chromadb Collection to add the data to.
        """
        self.logger.info("Processing CodeXGLUE dataset for vector store")
        
        # Find the bug-fix pairs
        bug_fix_pairs = []
        
        # Process the dataset (this is a simplified example, actual implementation depends on the dataset structure)
        # Here we assume a basic structure with buggy and fixed code files
        for buggy_file in codexglue_dir.glob("**/buggy/**/*.py"):
            # Compute the corresponding fixed file path
            fixed_file = Path(str(buggy_file).replace("/buggy/", "/fixed/"))
            
            if fixed_file.exists():
                try:
                    with open(buggy_file, 'r', encoding='utf-8', errors='replace') as f:
                        buggy_code = f.read()
                    
                    with open(fixed_file, 'r', encoding='utf-8', errors='replace') as f:
                        fixed_code = f.read()
                    
                    bug_fix_pairs.append({
                        "buggy_code": buggy_code,
                        "fixed_code": fixed_code,
                        "file_path": str(buggy_file),
                        "dataset": "codexglue"
                    })
                except Exception as e:
                    self.logger.warning(f"Error processing file {buggy_file}: {str(e)}")
        
        # Add to vector store
        if bug_fix_pairs:
            self._add_to_vector_store(collection, bug_fix_pairs)
    
    def _process_mbpp_for_vector_store(self, mbpp_dir: Path, collection: "chromadb.Collection") -> None:
        """
        Process the MBPP dataset for the vector store.
        
        Args:
            mbpp_dir: Directory containing the MBPP dataset.
            collection: chromadb Collection to add the data to.
        """
        self.logger.info("Processing MBPP dataset for vector store")
        
        # Load the JSON file
        try:
            json_path = mbpp_dir / "mbpp.json"
            with open(json_path, 'r') as f:
                examples = json.load(f)
            
            # Process the examples
            code_patterns = []
            for i, example in enumerate(examples):
                code_patterns.append({
                    "task": example.get("text", ""),
                    "code": example.get("code", ""),
                    "dataset": "mbpp",
                    "id": example.get("task_id", str(i))
                })
            
            # Add to vector store
            self._add_to_vector_store(collection, code_patterns)
            
        except Exception as e:
            self.logger.warning(f"Error processing MBPP dataset: {str(e)}")
    
    def _process_quixbugs_for_vector_store(self, quixbugs_dir: Path, collection: "chromadb.Collection") -> None:
        """
        Process the QuixBugs dataset for the vector store.
        
        Args:
            quixbugs_dir: Directory containing the QuixBugs dataset.
            collection: chromadb Collection to add the data to.
        """
        self.logger.info("Processing QuixBugs dataset for vector store")
        
        # Find bug-fix pairs
        java_dir = quixbugs_dir / "java_programs"
        java_dir_correct = quixbugs_dir / "java_programs_correct"
        py_dir = quixbugs_dir / "python_programs"
        py_dir_correct = quixbugs_dir / "python_programs_correct"
        
        bug_fix_pairs = []
        
        # Process Java programs
        if java_dir.exists() and java_dir_correct.exists():
            for buggy_file in java_dir.glob("*.java"):
                file_name = buggy_file.name
                fixed_file = java_dir_correct / file_name
                
                if fixed_file.exists():
                    try:
                        with open(buggy_file, 'r', encoding='utf-8', errors='replace') as f:
                            buggy_code = f.read()
                        
                        with open(fixed_file, 'r', encoding='utf-8', errors='replace') as f:
                            fixed_code = f.read()
                        
                        bug_fix_pairs.append({
                            "buggy_code": buggy_code,
                            "fixed_code": fixed_code,
                            "file_path": str(buggy_file),
                            "dataset": "quixbugs_java"
                        })
                    except Exception as e:
                        self.logger.warning(f"Error processing file {buggy_file}: {str(e)}")
        
        # Process Python programs
        if py_dir.exists() and py_dir_correct.exists():
            for buggy_file in py_dir.glob("*.py"):
                file_name = buggy_file.name
                fixed_file = py_dir_correct / file_name
                
                if fixed_file.exists():
                    try:
                        with open(buggy_file, 'r', encoding='utf-8', errors='replace') as f:
                            buggy_code = f.read()
                        
                        with open(fixed_file, 'r', encoding='utf-8', errors='replace') as f:
                            fixed_code = f.read()
                        
                        bug_fix_pairs.append({
                            "buggy_code": buggy_code,
                            "fixed_code": fixed_code,
                            "file_path": str(buggy_file),
                            "dataset": "quixbugs_python"
                        })
                    except Exception as e:
                        self.logger.warning(f"Error processing file {buggy_file}: {str(e)}")
        
        # Add to vector store
        if bug_fix_pairs:
            self._add_to_vector_store(collection, bug_fix_pairs)
    
    def _add_to_vector_store(self, collection: "chromadb.Collection", items: List[Dict[str, Any]]) -> None:
        """
        Add items to the vector store.
        
        Args:
            collection: chromadb Collection to add the data to.
            items: List of items to add.
        """
        # Prepare data for batch addition
        ids = []
        documents = []
        metadatas = []
        
        for i, item in enumerate(items):
            if "id" in item:
                item_id = str(item["id"])
            else:
                item_id = f"item_{i}_{hash(str(item))}"
            
            # For bug-fix pairs
            if "buggy_code" in item and "fixed_code" in item:
                document = f"BUGGY CODE:\n{item['buggy_code']}\n\nFIXED CODE:\n{item['fixed_code']}"
                metadata = {
                    "dataset": item.get("dataset", "unknown"),
                    "file_path": item.get("file_path", ""),
                    "buggy_code": item["buggy_code"],
                    "fixed_code": item["fixed_code"]
                }
            # For code patterns
            elif "task" in item and "code" in item:
                document = f"TASK:\n{item['task']}\n\nCODE:\n{item['code']}"
                metadata = {
                    "dataset": item.get("dataset", "unknown"),
                    "task": item["task"],
                    "code": item["code"]
                }
            # Generic case
            else:
                document = str(item)
                metadata = {k: str(v) for k, v in item.items()}
            
            ids.append(item_id)
            documents.append(document)
            metadatas.append(metadata)
        
        # Add in batches (to avoid memory issues with large datasets)
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i+batch_size]
            batch_documents = documents[i:i+batch_size]
            batch_metadatas = metadatas[i:i+batch_size]
            
            try:
                collection.add(
                    ids=batch_ids,
                    documents=batch_documents,
                    metadatas=batch_metadatas
                )
            except Exception as e:
                self.logger.warning(f"Error adding batch to vector store: {str(e)}")
                # Continue with next batch
