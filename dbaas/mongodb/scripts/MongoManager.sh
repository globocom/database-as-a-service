#!/bin/bash
## ======================================================
##
##
## ======================================================

#--------------------------------------------------------

function die() {
    echo $@
    exit 1
}

# Don't forget to add new option/commands on this function!
function usage() {
cat << EOF

Usage: $0 [option]

Options:

    -h			    Show this message
    adduser		    Create a database credential
    dropuser		    Remove specific username from the database
    createdatabase	    Initialize a database
    dropdatabase	    Drop database and the associated files
    status/healthcheck	    It is a kind of healthcheck
    serverstatus	    Statistics data

Environment variables required:
    INSTANCE_CONNECTION INSTANCE_USER INSTANCE_PASSWORD

EOF
exit 1
}
# --------------------------------------------------------

# mongo client exists and is executable?
mongo_client='/usr/local/mongodb-osx-x86_64-2.4.6/bin/mongo'
[[ -x $mongo_client ]] || die "Mongo client ($mongo_client) does not exist or it is not executable."

# Check and set the required environment variables
if [[ -n $INSTANCE_CONNECTION || -n $INSTANCE_USER || -n $INSTANCE_PASSWORD ]]; then
    ADM_USER=$INSTANCE_USER; ADM_PASS=$INSTANCE_PASSWORD;
else
    die "You must provide at least these environment variables:\
    INSTANCE_CONNECTION INSTANCE_USER INSTANCE_PASSWORD"
    
fi

# Main
exec_time=$(/bin/date "+[%d/%b/%Y %H:%M:%S]")
action=$1
case $action in
    adduser)
        [[ -z $CREDENTIAL_USER || -z $CREDENTIAL_PASSWORD || -z $DATABASE_NAME ]] && die "Missing the env variables: DATABASE_NAME CREDENTIAL_USER CREDENTIAL_PASSWORD"
        log_msg="The user $CREDENTIAL_USER was successfully added on $INSTANCE_NAME/$DATABASE_NAME by $INSTANCE_USER."
        my_params="var db_name='$DATABASE_NAME', user_to_create='$CREDENTIAL_USER', user_password='$CREDENTIAL_PASSWORD'"
        my_js='addUser.js';;
    dropuser)
        [[ -z $CREDENTIAL_USER || -z $DATABASE_NAME ]] && die "Missing the env variable: DATABASE_NAME CREDENTIAL_USER"
        log_msg="The user $CREDENTIAL_USER was successfully removed from $INSTANCE_NAME/$DATABASE_NAME by $INSTANCE_USER."
        my_params="var db_name='$DATABASE_NAME', user_to_remove='$CREDENTIAL_USER'"
        my_js='removeUser.js';;
    createdatabase)
        [[ -z $DATABASE_NAME ]] && die "Missing the env variable: DATABASE_NAME"
        log_msg="The database $INSTANCE_NAME/$DATABASE_NAME has been created by $INSTANCE_USER."
        my_params="var db_name='$DATABASE_NAME'"
        my_js='createDatabase.js';;
    dropdatabase)
        [[ -z $DATABASE_NAME ]] && die "Missing the env variable: DATABASE_NAME"
        log_msg="The database $INSTANCE_NAME/$DATABASE_NAME was successfully dropped by $INSTANCE_USER."
        my_params="var db_name='$DATABASE_NAME'"
        my_js='dropDatabase.js';;
    status|healthcheck)
        log_msg="The $INSTANCE_NAME healthy looks good."
        my_js='healthCheck.js';;
    serverstatus)
        log_msg="Getting the statistics data from $INSTANCE_NAME."
        my_js='serverStatus.js';;
    listcollections)
        echo "collections:"
        my_js='getCollectionNames.js';;
    listdatabases)
        echo "databases:"
        my_js='listDatabases.js';;
    *)
        usage;;
esac

# Global vars
BASEDIR=$(dirname $0)
JSDIR="${BASEDIR}/js"
MONGO_DEFAULT_OPTS='--norc --quiet'
js_file="${JSDIR}/${my_js}"

[[ -f $js_file ]] || die "The file ${js_file} does not exist, please check it."

# Action!
#ssl
[[ $verbose -eq 1 ]] && echo "$exec_time [DEBUG] Exec: $mongo_client $MONGO_DEFAULT_OPTS -u $INSTANCE_USER -p xxx $INSTANCE_CONNECTION/admin --eval \"$my_params\" $js_file"

output_cmd=`$mongo_client $MONGO_DEFAULT_OPTS -u $INSTANCE_USER -p $INSTANCE_PASSWORD $INSTANCE_CONNECTION/admin --eval "$my_params" $js_file`
exit_code=$?

if [[ $exit_code -eq 0 ]]; then
    echo "$exec_time [INFO] $log_msg"
else
    echo "$exec_time [ERROR] $output_cmd"
fi

[[ $verbose -eq 1 ]] && echo -ne "$exec_time [DEBUG] exit code: $exit_code, output: $output_cmd\n"
exit $exit_code
