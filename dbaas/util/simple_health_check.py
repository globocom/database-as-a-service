# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
from contextlib import contextmanager


LOG = logging.getLogger(__name__)


class HealthCheckError(Exception):
    def __init__(self, service, extra_message=None):
        msg = "HealthCheckError: Service {} is experiencing issues.".format(
            service
        )
        if extra_message:
            msg += " " + extra_message
        super(HealthCheckError, self).__init__(msg)


class RedisNotWorking(Exception):
    pass


class KeyAlreadyLocked(Exception):
    pass


class SimpleHealthCheck(object):
    def __init__(
        self, health_check_url, service_key, redis_client, http_client,
        http_request_exceptions, service_ok_status=200,
        service_ok_response='WORKING', health_check_request_timeout=2,
        health_check_ttl=60, verify_ssl=True
    ):
        self._health_check_url = health_check_url
        self._service_key = service_key
        self._service_ok_status = service_ok_status
        self._service_ok_response = service_ok_response
        self._health_check_request_timeout = health_check_request_timeout
        self._health_check_ttl = health_check_ttl
        self._redis_client = redis_client
        self._http_client = http_client
        self._http_request_exceptions = http_request_exceptions
        self._verify_ssl = verify_ssl

    @property
    def _service_ok_key(self):
        return 'ok_' + self._service_key

    @property
    def _service_failed_key(self):
        return 'failed_' + self._service_key

    @property
    def _service_ok_lock_key(self):
        return 'service_ok_lock_' + self._service_key

    @property
    def _service_failed_lock_key(self):
        return 'service_failed_lock_' + self._service_key

    def _get_key_value(self, key):
        try:
            return self._redis_client.get(key)
        except Exception as e:
            LOG.warn(e)
            raise RedisNotWorking(e)

    def _set_key_with_expire(self, key, timeout, value=1):
        try:
            self._redis_client.setex(key, value, timeout)
        except Exception as e:
            LOG.warn(e)
            raise RedisNotWorking(e)

    def _make_http_request(self):
        return self._http_client.get(
            self._health_check_url,
            timeout=self._health_check_request_timeout,
            verify=self._verify_ssl
        )

    @contextmanager
    def _acquire_lock(self, key):
        lock = self._redis_client.lock(
            key, timeout=self._health_check_ttl
        )
        try:
            is_locked = lock.acquire(blocking=False)
        except Exception as e:
            LOG.warn(e)
            raise RedisNotWorking(e)
        else:
            if is_locked:
                yield True
            else:
                raise KeyAlreadyLocked(
                    "Key {} is already locked!".format(key)
                )
        finally:
            if 'is_locked' in locals() and is_locked:
                try:
                    lock.release()
                except Exception as e:
                    LOG.warn(e)
                    error_message = "Error while releasing lock for key {}, wait for {}s.".format(
                        key, self._health_check_ttl
                    )
                    LOG.warn(error_message)

    def _handle_service_is_down(self, error_message=None):
        try:
            with self._acquire_lock(self._service_failed_lock_key):
                self._set_key_with_expire(
                    self._service_failed_key, self._health_check_ttl
                )
        except KeyAlreadyLocked as e:
            self.check_service()
        else:
            raise HealthCheckError(
                service=self._health_check_url,
                extra_message=error_message
            )

    def _handle_service_is_up(self, service_response):
        status_is_ok = self._service_ok_status == service_response.status_code
        content_is_ok = self._service_ok_response == service_response.content

        if status_is_ok and content_is_ok:
            try:
                with self._acquire_lock(self._service_ok_lock_key):
                    self._set_key_with_expire(
                        self._service_ok_key, self._health_check_ttl
                    )
            except KeyAlreadyLocked as e:
                self.check_service()
        else:
            error_message = "Expecting status {} and content {}, but received {} and {}".format(
                self._service_ok_status, self._service_ok_response,
                service_response.status_code, service_response.content
            )
            self._handle_service_is_down(error_message)

    def _is_service_up(self):
        return self._get_key_value(self._service_ok_key)

    def _is_service_down(self):
        return self._get_key_value(self._service_failed_key)

    def check_service(self):
        if self._is_service_up():
            return True

        if self._is_service_down():
            raise HealthCheckError(
                service=self._health_check_url,
                extra_message="Waiting to check again..."
            )

        try:
            service_response = self._make_http_request()
        except self._http_request_exceptions as e:
            LOG.warn(e)
            self._handle_service_is_down(str(e))
        else:
            self._handle_service_is_up(service_response)
            return True
