MongoDB as a Service (MongoDBaaS)
===================================



## To setup your local environment

    mkvirtualenv dbaas
    workon dbaas
    
    
You will also need to create a sitecustomize.py file with the following content in 
yours python's lib directory.

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

Then, finally

    make check_environment

## To run project

    make run

