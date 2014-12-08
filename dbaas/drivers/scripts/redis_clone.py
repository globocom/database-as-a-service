#!/usr/bin/env python
# -*- coding: utf-8 -*-
import paramiko
import redis
import click
import os
from contextlib import contextmanager
import logging

logging.basicConfig(
                                level=logging.DEBUG,
                                format='%(asctime)s %(levelname)s %(message)s',
                                )

class RedisDriver(object):
    def __init__(self, address, port, password, timeout,):
        self.address= address
        self.port= int(port)
        self.password= password
        self.timeout= timeout

    def __redis_client__(self,):
        try:
            client = redis.Redis(host= self.address,
                                 port= self.port,
                                 password= self.password,
                                 socket_connect_timeout= self.timeout)
            return client
        except Exception, e:
            click.echo("Error: {}".format(e))

    @contextmanager
    def redis(self,):
        client = None
        try:
            client = self.__redis_client__()

            return_value = client
            yield return_value
        except Exception, e:
            click.echo('Error connecting to database {} {} {}. {}'.format(self.address,
                self.password, self.port, e))

def exec_remote_command(server, username, password, command, output={}):

    try:
        click.echo("Executing command [%s] on remote server %s" % (command, server))
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(server, username= username, password= password)

        stdin, stdout, stderr = client.exec_command(command)
        log_stdout = stdout.readlines()
        log_stderr = stderr.readlines()
        exit_status = stdout.channel.recv_exit_status()
        click.echo("Comand return code: %s, stdout: %s, stderr %s" % (exit_status, log_stdout, log_stderr))
        output['stdout'] = log_stdout
        output['stderr'] = log_stderr
        return exit_status
    except (paramiko.ssh_exception.SSHException) as e:
        click.echo("We caught an exception: %s ." % (e))
        return False

def create_temp_dir(dir_path,):
    try:
        os.makedirs(dir_path)
        return True
    except OSError, e:
        click.echo('ERROR on creating temporary dir: {}'.format(e))
        return False

def destroy_temp_dir(dir_path,):
    try:
        os.removedirs(dir_path)
        return True
    except OSError, e:
        click.echo('ERROR on creating temporary dir: {}'.format(e))
        return False

def test_return_code(return_code):
    if (type(return_code)=='bool' and return_code==False) or return_code != 0:
        return False

def dump_src_database(host, redis_port, redis_pass,
                                            redis_time_out, dump_path,
                                            sys_user,sys_pass, remote_path):

    click.echo("Dumping source database...")
    driver = RedisDriver(host, redis_port, redis_pass, redis_time_out)

    with driver.redis() as client:
        try:
            client.save()
        except Exception, e:
            click.echo("Error while requesting dump: {}".format(e))
            return False

    try:
        transport = paramiko.Transport((host, 22))
        transport.connect(username = sys_user, password = sys_pass)

        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.get(remote_path, dump_path)

        sftp.close()
        transport.close()

        click.echo("Dump successful! :)")
        return True
    except Exception, e:
        click.echo('ERROR while transporting dump file: {}'.format(e))
        return False

def restore_dst_database(dump_path, host, redis_port, redis_pass, sys_user, sys_pass, remote_path, redis_time_out):

    click.echo("Restoring target database...")
    return_code = exec_remote_command(server=host,
                                                  username=sys_user,
                                                  password=sys_pass,
                                                  command='/etc/init.d/redis stop')


    try:
        transport = paramiko.Transport((host, 22))
        transport.connect(username = sys_user, password = sys_pass)

        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.put(dump_path, remote_path)

        sftp.close()
        transport.close()
    except Exception, e:
        click.echo('ERROR while transporting dump file: {}'.format(e))
        return False
    
    return_code = exec_remote_command(server=host,
                                      username=sys_user,
                                      password=sys_pass,
                                      command="sed -i 's/appendonly/#appendonly/g' /data/redis.conf")


    return_code = exec_remote_command(server=host,
                                      username=sys_user,
                                      password=sys_pass,
                                      command='/etc/init.d/redis start')


    return_code = exec_remote_command(server=host,
                                      username=sys_user,
                                      password=sys_pass,
                                      command="sed -i 's/#appendonly/appendonly/g' /data/redis.conf")

    
    driver = RedisDriver(host, redis_port, redis_pass, redis_time_out)

    with driver.redis() as client:
        try:
            client.config_set("appendonly", "yes")
        except Exception, e:
            click.echo("Error while requesting dump: {}".format(e))
            return False

    click.echo("Restore successful! :)")

    return True

@click.command()
@click.argument('redis_time_out', default=60)
@click.argument('src_pass')
@click.argument('src_host', default="127.0.0.1")
@click.argument('src_port', default=6379)
@click.argument('src_sys_user', default="root")
@click.argument('src_sys_pass')
@click.argument('src_dump_path', type=click.Path(exists=False))
@click.argument('dst_pass')
@click.argument('dst_host', default="127.0.0.1")
@click.argument('dst_port', default=6379)
@click.argument('dst_sys_user', default="root")
@click.argument('dst_sys_pass')
@click.argument('dst_dump_path', type=click.Path(exists=False))
@click.argument('local_dump_path', default="/tmp/dump.rdb", type=click.Path(exists=False))
def main(redis_time_out, src_pass, src_host,
                                            src_port, src_sys_user, src_sys_pass,
                                            src_dump_path, dst_pass, dst_host, dst_port, dst_sys_user,
                                            dst_sys_pass, dst_dump_path, local_dump_path, ):
    """Command line tool to dump a redis database and import on another"""

    if not dump_src_database(src_host, src_port, src_pass,
                                            redis_time_out, local_dump_path,
                                            src_sys_user, src_sys_pass, src_dump_path):
        click.echo("Dump unsuccessful! :(")
        return 1

    if not restore_dst_database(local_dump_path, dst_host, dst_port, dst_pass, 
                                            dst_sys_user, dst_sys_pass, dst_dump_path, redis_time_out):
        click.echo("Restore unsuccessful! :(")
        return 1

    return 0


if __name__ == '__main__':
    main()
