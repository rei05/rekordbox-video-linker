pip install setuptools pyrekordbox tabulate

brew install SQLCipher

git clone https://github.com/coleifer/sqlcipher3
git clone https://github.com/geekbrother/sqlcipher-amalgamation
cd sqlcipher3
SQLCIPHER_PATH=$(brew --prefix sqlcipher); C_INCLUDE_PATH="$SQLCIPHER_PATH"/include LIBRARY_PATH="$SQLCIPHER_PATH"/lib python setup.py build
SQLCIPHER_PATH=$(brew --prefix sqlcipher); C_INCLUDE_PATH="$SQLCIPHER_PATH"/include LIBRARY_PATH="$SQLCIPHER_PATH"/lib python setup.py install
SQLCIPHER_PATH=$(brew --prefix sqlcipher); C_INCLUDE_PATH="$SQLCIPHER_PATH"/include LIBRARY_PATH="$SQLCIPHER_PATH"/lib python setup.py install
cd ../

python -m pyrekordbox download-key
python show_config.py
