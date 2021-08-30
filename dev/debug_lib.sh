if [ $# -eq 0 ]
  then
    echo "No arguments supplied"
    exit 1
fi

DIR=/opt/lib/$1
SETUP=setup.py

echo "Trying to enable debug mode to $1..."


if [[ ! -d $DIR ]]; then
    echo "Lib folder not found - $DIR"
    exit 2
fi

cd $DIR

if [[ ! -f $SETUP ]]; then
    echo "Invalid lib - file $SETUP does not exists"
    exit 3
fi

python $SETUP develop

echo "Debug enabled to lib $1"
exit 0