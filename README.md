## Original proof of concept from ages ago  
[POC](https://github.com/Vector4-new/pekora-external/blob/main/Screenshot%202024-12-29%20013610.png?raw=true)

This doesn't actually work lol  
Maybe you can skid this  
Even if you do fix it some opcodes are still not converted which will lead to freezes & strange effects  
  
This used to work at some point, but in it's current state it's unusable.  

This is an external written for Pekora's 2017 client.  
I am not responsible if this gets you banned!

To run this, make sure you have all the modules installed by running `pip install -r requirements.txt`.  
If you do not have Visual Studio installed, you will need to install a copy of the [Visual C++ build tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) to install the LZ4 library.  
Make sure the MSVC build tools and the Windows SDK are downloaded.

You will also need a `luac5.1` binary. Lua binaries are available [here](https://luabinaries.sourceforge.net/). Place the executable in the same path as the `main.py` file.\
