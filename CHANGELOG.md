# Changelog

All notable changes to this project will be documented in this file.

## [0.2.4] - 2025-04-05

### Added
- Added option to download Phi-2 model or run in no-model mode
- Enhanced update command with --no-model flag to skip model download
- Added bolor-generate helper script for direct code generation
- Improved CLI wrapper to better handle quotes and special characters
- Fixed all update command issues with resource paths and imports

### Fixed
- Fixed all path reference errors in update command
- Improved error handling to avoid OptionInfo object errors
- Made all command interactions more reliable
- Better organized the codebase for easier maintenance

## [0.2.3] - 2025-04-05

### Fixed
- Direct fix for update command error with OptionInfo object
- Completely rewrote update command to skip mock model response handling
- Added explicit no-model mode configuration in update command
- Updated system to work without downloading models or using LLM

## [0.2.2] - 2025-04-05

### Fixed
- Fixed PyPI deployment issue with existing version
- Further improved `update` command to bypass model loading completely
- Removed all internal references to Generator in update functionality

## [0.2.1] - 2025-04-05

### Fixed
- Critical fix for model loading failure in all scenarios
- Implemented robust mock model fallback in core llm_wrapper.py
- Added proper handling of mock model responses in generator.py
- Fixed OptionInfo handling bug in update command
- Added standalone script (fix-bolor-standalone.sh) for direct model fix without dependencies

### Added
- Standalone model fixer script that works without relying on bolor update command
- Enhanced error handling in model loading to ensure Bolor never crashes
- Better handling of mock model responses to provide useful feedback

## [0.2.0] - 2025-04-05

### Changed
- Renamed `download-resources` command to `update` for better clarity
- Integrated model loading fix functionality directly into the main code
- Simplified user experience with a consolidated approach for model updates

### Fixed
- Model downloading process now more reliable with better progress indicators
- Improved handling of model compatibility issues across different ctransformers versions
- Fixed configuration file handling to ensure proper model type detection
- Eliminated the need for separate scripts by integrating fixes into core code

### Added
- New `update` command that handles model downloading, configuration, and compatibility testing
- Better error messaging and diagnostics during model loading
- Improved documentation for troubleshooting model issues

## [0.1.9] - 2025-04-05

### Fixed
- Fixed version numbering for PyPI compatibility
- Added executable shebang fix for global bolor script
- Ensured all scripts have proper permissions

## [0.1.8] - 2025-04-05

### Fixed
- Fixed model loading issues by integrating fallback mechanisms directly into core code
- Added automatic model verification and testing during download
- Improved version number to avoid PyPI conflicts

## [0.1.7] - 2025-04-05

### Fixed
- Fixed CLI command handling for quoted arguments (e.g., `bolor generate "login HTML"`)
- Improved CLI wrapper to properly interpret commands with spaces in arguments
- Modified core CLI argument handling in `__main__.py` to fix quote parsing issues
- Integrated model loading fixes directly into dataset_loader.py (no separate script needed)
- Added automatic fallback to smaller models when larger ones can't be loaded
- Improved model type detection to work across different ctransformers versions
- Streamlined installation process with a consolidated setup script

### Added
- Added new `setup-bolor-cli.sh` script that combines functionality from install and fix scripts
- Added `deploy-bolor-cli.sh` for automatic non-interactive CLI deployment
- Added `deploy-to-pypi.sh` for streamlined PyPI package deployment with CLI fixes
- Updated package metadata and PyPI description

## [0.1.6] - 2025-04-05

### Fixed
- Fixed CLI usage display showing "python -m bolor" instead of just "bolor"
- Updated CLI wrappers to properly set sys.argv[0] to 'bolor'

## [0.1.5] - 2025-04-05

### Fixed
- Fixed model loading compatibility issues with improved diagnostics
- Added comprehensive model loading diagnostics via `check_ctransformers.py`
- Created patched version of NLP interface example that works without model loading
- Added documentation on model loading issues and workarounds

### Added
- Added `examples/nlp_interface_example_patched.py` with mock LLM responses
- Added `MODEL_LOADING_FIX.md` with troubleshooting guide for model issues

## [0.1.4] - 2025-04-05

### Added
- Added natural language interface for generating code directly from prompts
- Added `generate` command for code generation from natural language
- Added direct mode interface without specifying a command (e.g., `bolor "create a function..."`)
- Added language auto-detection from natural language descriptions
- Implemented automatic code formatting and file saving capabilities

## [0.1.3] - 2025-04-05

### Fixed
- Fixed Phi-2 model loading issues with new fix_model_loading.py script
- Added fallback to smaller model when full model can't be downloaded
- Added model verification and automatic repair capabilities

## [0.1.2] - 2025-04-05

### Fixed
- Fixed dataset download errors by creating placeholder datasets
- Improved error handling in dataset loader and suppressed warning messages
- Fixed HuggingFace authentication errors by disabling datasets requiring auth
- Added `fix_dataset_errors.py` script to create placeholder datasets
- Added `setup-bolor.sh` for complete end-to-end setup

### Added
- Created comprehensive setup script that handles all installations
- Added placeholder datasets to allow offline usage

## [0.1.1] - 2025-04-05

### Fixed
- CLI script installation issue: Fixed issue where the `bolor` command wasn't in PATH
- Added helper scripts for CLI installation troubleshooting
- Included CLI wrapper script as an alternative method to run Bolor
- Fixed urllib3/requests dependency warnings by properly pinning dependency versions
- Added proper version constraints for all dependencies

### Added
- Added CHANGELOG.md file to track changes
- Added more detailed CLI installation instructions in documentation
- Added direct CLI installer via install-bolor-cli.sh

## [0.1.0] - 2025-04-05

### Added
- Initial release of Bolor
- Scan functionality for detecting code issues
- Fix functionality for automatically repairing detected issues
- Plan functionality for suggesting code improvements without modifying code
- deploy-check functionality for analyzing CI/CD configurations
- Support for Python, JavaScript/TypeScript, Java and C/C++ code analysis
- Local LLM integration with Phi-2
- Dataset integration with CodeXGLUE, MBPP, and QuixBugs
