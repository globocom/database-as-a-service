bash /code/dev/check_debug_lib.sh $1

if [[ $?  -eq 0 ]]
then
    echo $1 > /code/dev/debug_lib/lib.list
fi