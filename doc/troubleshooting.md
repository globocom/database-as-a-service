# DBaaS Troubleshooting

#### Purpose

The purpose of this guide is to serve as a troubleshooting knowledge base
for DBaaS, helping the team to better communicate and avoiding that the 
same problem is rediscovered and solved multiple times by different developers.

## EnvironmentError: mysql_config not found

You might get this error for two reasons:

1. You need to install mysql on your computer. 

2. After the installation, you didn't create the environment variable for mysql. 

    ```export PATH=$PATH:/usr/local/mysql/bin``` 

## Clang failed to find 'x11/xlib.h'

This error is related to Pillow or python-ldap installation inside the virtual environment and is most likely to happen because of three main reasons:

1. Xcode Command Line Tools are not installed on your Mac

    ```xcode-select --install```

2. Some libs are not installed

    ```brew install libtiff libjpeg webp little-cms2 openssl```
    
3. The compiler can't find the headers on the default directory. You need to create a symbolic link to the actual directory.

    ```ln -s /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.14.sdk/System/Library/Frameworks/Tk.framework/Versions/8.5/Headers/X11 /usr/local/include/X11```


## Clang failed to find 'sasl.h'

When executing `make pip`, you might have some problem with python-ldap lib. Other than the solutions above, this issue found to be originated from some reasons:

1. You need to check if xcode is installed on your machine. Just type CMD + Space: xcode.

2. If the compiler's still not finding it. Try exporting CFLAGS such that it adds an include path to the sasl headers already installed by Xcode:

    ```export CFLAGS="-I$(xcrun --show-sdk-path)/usr/include/sasl"```
    
3. Just in case the problem persists, try to reinstall opensll and set LIBRARY_PATH.

    ```brew install openssl```
    
    ```export LIBRARY_PATH=$LIBRARY_PATH:/usr/local/opt/openssl/lib/```
