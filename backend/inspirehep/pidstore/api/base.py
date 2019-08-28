# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
#
# inspirehep is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

import six
import structlog
from flask import current_app
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier

LOGGER = structlog.getLogger()


class PidStoreBase(object):
    minters = []

    def __init__(self, object_uuid, data):
        self.data = data
        self.object_uuid = object_uuid

    @classmethod
    def mint(cls, object_uuid, data):
        LOGGER.info("Minting PIDs", uuid=str(object_uuid))
        for minter in cls.minters:
            minter.mint(object_uuid, data)

    @classmethod
    def update(cls, object_uuid, data):
        LOGGER.info("Updating PIDs", uuid=str(object_uuid))
        pid_base = cls(object_uuid, data)
        pid_base.delete_external_pids()
        for minter in cls.minters:
            minter.update(object_uuid, data)

    @classmethod
    def delete(cls, object_uuid, data):
        LOGGER.info("Deleting PIDs", uuid=str(object_uuid))
        pid_base = cls(object_uuid, data)
        pid_base.delete_external_pids()
        for minter in cls.minters:
            minter.delete(object_uuid, data)

    def delete_external_pids(self):
        try:
            LOGGER.info("Deleting external PIDs", uuid=str(self.object_uuid))
            return PersistentIdentifier.query.filter_by(
                object_type="rec",
                object_uuid=str(self.object_uuid),
                pid_provider="external",
            ).delete()
        except PIDDoesNotExistError:
            LOGGER.warning("Pids ``external`` not found", uuid=str(self.object_uuid))

    @staticmethod
    def get_endpoint_from_pid_type(pid_type):
        """Return the ``endpoint`` for a given ``pid_type``.

        Args:
            pid_type (str): the pid_type.

        Returns:
            None if not found, the ``endpoint``.
        """
        pids_to_endpoints = PidStoreBase._get_config_pid_types_to_endpoints()
        return pids_to_endpoints.get(pid_type)

    @staticmethod
    def get_pid_type_from_endpoint(endpoint):
        """Return the ``pid_type`` for a given ``endpoint``.

        Args:
            endpoint (str): the endpoint.
                The entpoint registered for a specicific ``pid_type``,
                for example ``literature``.
        Returns:
            None if not found, the ``pid_type``.
        """
        pids_to_endpoints = PidStoreBase._get_config_pid_types_to_endpoints()
        ENDPOINTS_TO_PID_TYPES = {
            value: key for (key, value) in pids_to_endpoints.items()
        }
        return ENDPOINTS_TO_PID_TYPES.get(endpoint)

    @staticmethod
    def _get_config_pid_types_to_endpoints():
        """Retrieve the map from pid_type to endpoint.

        Note:

            This function exists for the sake of testability
            otherwhise you have to bind all these util functions
            with the ``current_app``.
        """
        return current_app.config["PID_TYPES_TO_ENDPOINTS"]

    @staticmethod
    def _get_config_pid_types_to_schema():
        """Retrieve the map from pid_type to schema.

        Note:

            This function exists for the sake of testability
            otherwhise you have to bind all these util functions
            with the ``current_app``.
        """
        return current_app.config["SCHEMA_TO_PID_TYPES"]

    @staticmethod
    def get_pid_type_from_schema(schema):
        """Return the ``pid_type`` for a given ``schema``.

        Args:
            schema (str): the schema name.
                The schema name is the schema file name, for,
                example ``hep.json``  is the schema for ``hep``.
        Returns:
            None if not found, the ``pid_type``.
        """
        try:
            schema_name = (
                six.moves.urllib.parse.urlsplit(schema)
                .path.split("/")[-1]
                .split(".")[0]
            )
        except (TypeError, IndexError):
            schema_name = None
        pids_to_schema = PidStoreBase._get_config_pid_types_to_schema()
        return pids_to_schema.get(schema_name)

    @staticmethod
    def get_pid_from_record_uri(uri):
        parts = [part for part in uri.split("/") if part]
        try:
            pid_type = parts[-2][:3]
            pid_value = parts[-1]
        except IndexError:
            return None
        return pid_type, pid_value