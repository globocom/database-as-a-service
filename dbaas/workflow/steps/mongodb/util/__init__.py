# -*- coding: utf-8 -*-
import logging

LOG = logging.getLogger(__name__)


def build_mongodb_connect_string(instances, databaseinfra):
    connect_string = ""
    for instance in instances:
        if instance.instance_type != instance.MONGODB_ARBITER:
            if connect_string:
                connect_string += ','
            connect_string += instance.address + \
                ":" + str(instance.port)

    replica_name = databaseinfra.get_driver().get_replica_name()
    if replica_name:
        connect_string = replica_name + "/" + connect_string

    connect_string = " --host {} admin -u{} -p{}".format(
        connect_string, databaseinfra.user, databaseinfra.password)

    LOG.debug(connect_string)
    return connect_string


def build_permission_script():

    return """
        mkdir /data/data
        die_if_error "Error creating data dir"

        chown mongodb:mongodb /data
        die_if_error "Error changing datadir permission"
        chown -R mongodb:mongodb /data/*
        die_if_error "Error changing datadir permission"

        chmod 600 /data/mongodb.key
        die_if_error "Error changing mongodb key file permission"
        """


def build_start_database_script(wait_time=0):
    return """
        echo ""; echo $(date "+%Y-%m-%d %T") "- Starting the database"
        /etc/init.d/mongodb start > /dev/null
        die_if_error "Error starting database"
        sleep {}
    """.format(wait_time)


def build_stop_database_script(clean_data=True):
    script = """
        /etc/init.d/mongodb stop
        sleep 5
    """
    if clean_data:
        script += """
            rm -rf /data/*
        """
    return script


def build_add_replica_set_members_script():
    return """
        echo ""; echo $(date "+%Y-%m-%d %T") "- Adding new database members"
        /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
        rs.add( { "_id": {{SECUNDARY_ONE_MEMBER_ID}}, "host": "{{SECUNDARY_ONE}}", "priority": 0 } )
        rs.add( { "_id": {{SECUNDARY_TWO_MEMBER_ID}}, "host": "{{SECUNDARY_TWO}}", "priority": 0 } )
        rs.addArb("{{ARBITER}}")
        exit
        \nEOF_DBAAS
        die_if_error "Error adding new replica set members"
    """


def build_remove_replica_set_members_script():
    return """
        echo ""; echo $(date "+%Y-%m-%d %T") "- Removing new database members"
        /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
        rs.remove("{{ARBITER}}")
        exit
        \nEOF_DBAAS
        die_if_error "Error removing new replica set members"

        sleep 30
        echo ""; echo $(date "+%Y-%m-%d %T") "- Removing new database members"
        /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
        rs.remove("{{SECUNDARY_TWO}}")
        exit
        \nEOF_DBAAS
        die_if_error "Error removing new replica set members"

        sleep 30
        echo ""; echo $(date "+%Y-%m-%d %T") "- Removing new database members"
        /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
        rs.remove("{{SECUNDARY_ONE}}")
        exit
        \nEOF_DBAAS
        die_if_error "Error removing new replica set members"
    """


def build_switch_primary_to_new_instances_script():
    return """
       echo ""; echo $(date "+%Y-%m-%d %T") "- Change priority of members"
       /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
       status = rs.status()
       var_secundary_member = 0
       if (status["members"][1].stateStr == "SECONDARY") {var_secundary_member = 1}
       cfg = rs.conf()
       cfg.members[var_secundary_member].priority = 0
       cfg.members[3].priority = 1
       cfg.members[4].priority = 1
       rs.reconfig(cfg)
       exit
       \nEOF_DBAAS
       die_if_error "Error changing priority of members"

       sleep 30
       echo ""; echo $(date "+%Y-%m-%d %T") "- Switch primary"
       /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
       rs.stepDown()
       exit
       \nEOF_DBAAS
       die_if_error "Error switching primary"

       sleep 30
       echo ""; echo $(date "+%Y-%m-%d %T") "- Change priority of members"
       /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
       cfg = rs.conf()
       cfg.members[0].priority = 0
       cfg.members[1].priority = 0
       rs.reconfig(cfg)
       exit
       \nEOF_DBAAS
       die_if_error "Error changing priority of members"
    """


def build_switch_primary_to_old_instances_script():
    return """
       echo ""; echo $(date "+%Y-%m-%d %T") "- Change priority of members"
       /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
       status = rs.status()
       var_secundary_member = 3
       if (status["members"][4].stateStr == "SECONDARY") {var_secundary_member = 4}
       cfg = rs.conf()
       cfg.members[var_secundary_member].priority = 0
       cfg.members[0].priority = 1
       cfg.members[1].priority = 1
       rs.reconfig(cfg)
       exit
       \nEOF_DBAAS
       die_if_error "Error changing priority of members"

       sleep 30
       echo ""; echo $(date "+%Y-%m-%d %T") "- Switch primary"
       /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
       rs.stepDown()
       exit
       \nEOF_DBAAS
       die_if_error "Error switching primary"

       sleep 30
       echo ""; echo $(date "+%Y-%m-%d %T") "- Change priority of members"
       /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
       cfg = rs.conf()
       cfg.members[3].priority = 0
       cfg.members[4].priority = 0
       rs.reconfig(cfg)
       exit
       \nEOF_DBAAS
       die_if_error "Error changing priority of members"
    """


def clean_files_old_binary_files():
    return """
        cd {{TARGET_PATH}}
        rm -rf {{MONGODB_OLD_RELEASE_FOLDER}}
    """


def build_cp_mongodb_binary_file():
    return """
        cd {{TARGET_PATH}}
        die_if_error "Error change current path"

        cp {{SOURCE_PATH}}/{{MONGODB_RELEASE_FILE}} .
        die_if_error "Error coping mongodb binary file"

        tar -xvf {{MONGODB_RELEASE_FILE}}
        die_if_error "Error uncompress mongodb binary file"

        chown -R mongodb:mongodb {{MONGODB_RELEASE_FOLDER}}
        die_if_error "Error changing owner"

        rm -f {{MONGODB_RELEASE_FILE}}
        die_if_error "Error removing tgz file"
    """


def build_change_release_alias_script():
    return """
        cd {{TARGET_PATH}}
        die_if_error "Error change current path"

        rm -f mongodb
        die_if_error "Error deleting mongodb alias"

        ln -s {{MONGODB_RELEASE_FOLDER}} mongodb
        die_if_error "Error creating mongodb alias"
    """


def build_authschemaupgrade_script():
    return """
        sleep 10
        /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
        db.adminCommand({authSchemaUpgrade: 1});
        exit
        \nEOF_DBAAS
        die_if_error "Error running authSchemaUpgrade"
    """


def build_change_limits_script():
    return """
        sed -i 's/soft nofile 32756/soft nofile 65536/g' /etc/security/limits.conf
        echo "* - nproc 65536" >> /etc/security/limits.conf
    """


def build_disable_authentication_single_instance_script():
    return """
        sed -i 's/auth/#auth/g' /data/mongodb.conf
    """


def build_enable_authentication_single_instance_script():
    return """
        sed -i 's/#auth/auth/g' /data/mongodb.conf
    """


def build_wait_admin_be_created_script():
    return """
        while true
        do
           if [ -d "/data/data/admin" ]; then
              break
           fi
           sleep 10
        done
        sleep 60
    """


def build_restart_database_script():
    return """
        echo ""; echo $(date "+%Y-%m-%d %T") "- Starting the database"
        /etc/init.d/mongodb restart > /dev/null
        die_if_error "Error restarting database"
    """


def build_clean_data_data_script():
    return """
        rm -rf /data/data/*
    """


def build_dump_database_script():
    return """
        mkdir /data/dump
        /usr/local/mongodb/bin/mongodump --out /data/dump/
        die_if_error "Error dumping database"
    """


def build_mongorestore_database_script():
    return """
        /usr/local/mongodb/bin/mongorestore /data/dump/
        die_if_error "Error restoring database"
        rm -rf /data/dump/
    """


def build_change_mongodb_conf_file_script():
    return """
        line=$(cat '/data/mongodb.conf' | grep -n 'dbpath' | grep -o '^[0-9]*')
        line=$((line + 2))
        sed -i ${line}'i\# Storage Engine\\nstorageEngine = wiredTiger\\n' /data/mongodb.conf

        line=$(cat '/data/mongodb.conf' | grep -n 'rest' | grep -o '^[0-9]*')
        line=$((line + 1))
        sed -i ${line}'i\httpinterface = true' /data/mongodb.conf
    """


def build_reinstal_mongo_gen_script():
    return """
        /etc/init.d/td-agent stop
        yum install -y gcc44
        yes | td-agent-gem uninstall mongo
        td-agent-gem install mongo
        /etc/init.d/td-agent start
    """


def build_change_in_serverstatus_file_script():
    return """
        (cat <<EOF_IN_SERVERSTATUS_FILE
module Fluent
  class ServerStatusInput < Input
    Plugin.register_input('serverstatus', self)

    config_param :uris, :array, :default => nil
    config_param :uri, :string
    config_param :stats_interval, :time, :default => 60 # every minute
    config_param :tag_prefix, :string, :default => "serverstatus"

    def initialize
      super
      require 'mongo'
    end

    def configure(conf)
      super

      unless @uris or @uri
        raise ConfigError, 'uris or uri must be specified'
      end

      if @uris.nil?
        @uris = [@uri]
      end

      @conns = @uris.map do |uri_str|
        uri_str = "mongodb://#{uri_str}" if not uri_str.start_with?("mongodb://")
        user, password = uri_str.split('@')[0].split('//')[1].split(':')
        uri = Mongo::URI.new(uri_str, :connect => :direct, :user => user, :password => password)
  client = Mongo::Client.new(uri.servers, uri.options)
        [client, uri]
      end
    end

    def start
      @loop = Coolio::Loop.new
      tw = TimerWatcher.new(@stats_interval, true, @log, &method(:collect_serverstatus))
      tw.attach(@loop)
      @thread = Thread.new(&method(:run))
    end
    def run
      @loop.run
    rescue
      log.error "unexpected error", :error=>\$!.to_s
      log.error_backtrace
    end

    def shutdown
      @loop.stop
      @thread.join
    end

    def collect_serverstatus
      begin

        for conn, conn_uri in @conns
          database = conn.database
          stats = database.command(:serverStatus => :true).first
    make_data_msgpack_compatible(stats)
          host, port = conn_uri.servers[0].split(':')
    tag = [@tag_prefix, host.gsub(/[\.-]/, "_"), port].join(".")
          Engine.emit(tag, Engine.now, stats)
        end

      rescue => e
        log.error "failed to collect MongoDB stats", :error_class => e.class, :error => e
      end
    end

    # MessagePack doesn't like it when the field is of Time class.
    # This is a convenient method that traverses through the
    # getServerStatus response and update any field that is of Time class.
    def make_data_msgpack_compatible(data)
      if [Hash, BSON::Document].include?(data.class)
        data.each {|k, v|
          if v.respond_to?(:each)
            make_data_msgpack_compatible(v)
          elsif v.class == Time
            data[k] = v.to_i
          end
        }
        # serverStatus's "locks" field has "." as a key, which can't be
        # inserted back to MongoDB withou wreaking havoc. Replace it with
        # "global"
        data["global"] = data.delete(".") if data["."]
      elsif data.class == Array
        data.each_with_index { |v, i|
          if v.respond_to?(:each)
            make_data_msgpack_compatible(v)
          elsif v.class == Time
            data[i] = v.to_i
          end
        }
      end
    end

    class TimerWatcher < Coolio::TimerWatcher

      def initialize(interval, repeat, log, &callback)
        @callback = callback
        @log = log
        super(interval, repeat)
      end
      def on_timer
        @callback.call
      rescue
        @log.error \$!.to_s
        @log.error_backtrace
      end
    end
  end
end

EOF_IN_SERVERSTATUS_FILE
) > /etc/td-agent/plugin/in_serverstatus.rb
    """
