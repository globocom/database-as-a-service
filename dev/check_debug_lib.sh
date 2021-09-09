if [ $# -eq 0 ]
  then
    echo "Argument not found"
    exit 1
fi

DIR=/opt/lib/$1
SETUP=setup.py

echo "Trying to enable debug mode to $1..."


if [[ ! -d $DIR ]]; then
    echo "Path not found: $DIR"
    exit 2
fi

cd $DIR

if [[ ! -f $SETUP ]]; then
    echo "file not found $DIR/$SETUP"
    exit 3
fi

echo "debug enabled to $1"
exit 0