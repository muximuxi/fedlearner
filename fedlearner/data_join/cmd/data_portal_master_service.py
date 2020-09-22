# Copyright 2020 The FedLearner Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# coding: utf-8

import argparse
import logging
from google.protobuf import text_format

from fedlearner.common import data_portal_service_pb2 as dp_pb
from fedlearner.common.mysql_client import DBClient

from fedlearner.data_join import common
from fedlearner.data_join.data_portal_master import DataPortalMasterService

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    logging.basicConfig(format="%(asctime)s %(filename)s "\
                               "%(lineno)s %(levelname)s - %(message)s")
    parser = argparse.ArgumentParser(description='DataPortalMasterService cmd.')
    parser.add_argument('--db_database', type=str,
                        default='test_mysql', help='the name of mysql')
    parser.add_argument('--db_addr', type=str,
                        default='localhost:2379', help='the addrs of mysql')
    parser.add_argument('--db_base_dir', type=str, default='fedlearner_test',
                        help='the namespace of mysql key')
    parser.add_argument('--db_username', type=str,
                        default='test_user', help='the user of mysql')
    parser.add_argument('--db_password', type=str,
                        default='test_password', help='the password of mysql')
    parser.add_argument('--listen_port', '-p', type=int, default=4032,
                        help='Listen port of data join master')
    parser.add_argument('--data_portal_name', type=str,
                        default='test_data_source',
                        help='the name of data source')
    parser.add_argument('--data_portal_type', type=str,
                        default='Streaming', choices=['PSI', 'Streaming'],
                        help='the type of data portal type')
    parser.add_argument('--output_partition_num', type=int, required=True,
                        help='the output partition number of data portal')
    parser.add_argument('--input_file_wildcard', type=str, default='',
                        help='the wildcard filter for input file')
    parser.add_argument('--input_base_dir', type=str, required=True,
                        help='the base dir of input directory')
    parser.add_argument('--output_base_dir', type=str, required=True,
                        help='the base dir of output directory')
    parser.add_argument('--raw_data_publish_dir', type=str, required=True,
                        help='the raw data publish dir in mysql')
    parser.add_argument('--use_mock_db', action='store_true',
                        help='use to mock mysql for test')
    parser.add_argument('--long_running', action='store_true',
                        help='make the data portal long running')
    args = parser.parse_args()

    kvstore = DBClient(args.db_database, args.db_addr, args.db_username,
                        args.db_password, args.db_base_dir,
                        args.use_mock_db)
    kvstore_key = common.portal_db_base_dir(args.data_portal_name)
    if kvstore.get_data(kvstore_key) is None:
        portal_manifest = dp_pb.DataPortalManifest(
                name=args.data_portal_name,
                data_portal_type=(dp_pb.DataPortalType.PSI if
                                  args.data_portal_type == 'PSI' else
                                  dp_pb.DataPortalType.Streaming),
                output_partition_num=args.output_partition_num,
                input_file_wildcard=args.input_file_wildcard,
                input_base_dir=args.input_base_dir,
                output_base_dir=args.output_base_dir,
                raw_data_publish_dir=args.raw_data_publish_dir,
                processing_job_id=-1
            )
        kvstore.set_data(kvstore_key, text_format.\
            MessageToString(portal_manifest))

    options = dp_pb.DataPotraMasterlOptions(use_mock_db=args.use_mock_db,
                                            long_running=args.long_running)

    portal_master_srv = DataPortalMasterService(args.listen_port,
                                                args.data_portal_name,
                                                args.db_database,
                                                args.db_base_dir,
                                                args.db_addr,
                                                args.db_username,
                                                args.db_password,
                                                options)
    portal_master_srv.run()
