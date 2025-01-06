# Installation

First, move the `pyxi` folder to `~/lib/pyxi`

Then, set up your `.bashrc` so it knows about pyxi: `PATH="$PATH:~/lib/pyxi/bin/"` and if you aren't already, `export PATH`

Then you'll need to install the dependencies.

## Install requirements

Finally, install the requirements. This is tricky if you don't already have Python with SSL (in order to download the dependencies). See:
- https://pages.github.nceas.ucsb.edu/NCEAS/Computing/local_install_python_on_a_server.html
- https://stackoverflow.com/questions/41328451/ssl-module-in-python-is-not-available-when-installing-package-with-pip3

TLDR:
1. Get the latest Python source and put it in `~/` (`Y:`) for safekeeping
2. Uncompress the folder: `tar -zxvf Python-X.Y.Z.tgz`
3. Move it somewhere tidy: `mv Python-X.Y.Z/ lib/`
4. Move inside the directory: `cd lib/Python-X.Y.Z/`
5. Create the destination folder: `mkdir ~/.localpython`
6. Figure out where openssl lives: `whereis openssl` - you might have to `ls` the results to see which one is actually a folder that includes a bunch of `.h` files. In my case, it's `/usr/include/openssl`, so that's what I use in the next step:
7. Prepare the environment for building WITH SSL: `./configure --prefix=/home/<username>/.localpython --with-ssl=/usr/include/openssl`
8. Building the system: `make`
9. Implement the installation: `make install`
10. Go back to pyxi: `cd ../pyxi/`
11. Install the pyxi dependencies: `pip3 install -r requirements.txt`
12. Verify that it works: `pyxi --help`

### Deal with multiple python versions

If you still get an error when trying to run `pip3` on step 11, we might not be using the right python version.

Run this to see if your Python has SSL: `python3 -c "import ssl; print(ssl.OPENSSL_VERSION)"`

Also try giving it the full path to the python3 executable you just installed, if that doesn't work.

If either of the above work (you get an output showing your OpenSSL version), then try the following steps:

1. Go to your user bin directory: `cd ~/bin`
2. Create a symbolic link to the python you installed: `ln -s ~/.localpython/Python-X.Y.Z/Python-X.Y.Z/Python/bin/python3 python3`
3. Repeat step 2 with `python3.11`, `pip3`, `pip3.11` (or whatever your executables are called) instead of `python3`
4. Go to pyxi and try again: `cd ~/lib/pyxi`
5. Bootstrap pip: `python3 -m ensurepip`
6. Install the dependencies using the pip module: `python3 -m pip install -r requirements.txt`
