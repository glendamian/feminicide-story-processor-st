# Additional Set Up Instructions

## Apple Silicon

If you ran into the error: `zsh: illegal hardware instruction ...` after following the set up instructions on the `README.md` file, there might be an issue related to Tensorflow. These instructions might resolve the problem:

1. Uninstall current installed Tensorflow: `pip uninstall tensorflow`
2. Make sure that Xcode command-line tools is installed: `xcode-select --install`
3. Install Tensorflow for MacOS: `pip install tensorflow-macos`
4. Install tensorflow-metal plug-in for MacOS: `pip install tensorflow-metal`
5. Run `pip list | grep tensorflow` and verify that the desired version of Tensorflow is installed, refer back to instructions on `README.md`if tensorflow-text is not installed
6. Run `pytest` to run all the automated tests and verify setup is working
