# coding: utf-8
"""
@Author: Robby
@Module name: producer.py
@Create date: 2020-10-28
@Function: 向kafka写入指令消息
"""

import json
from utils.parse_file import KafkaProducerConsumerSingleton, KafkaConfigSingleton
from utils.const_file import PRODUCER_INFO_LOG, PRODUCER_ERROR_LOG
from utils.global_logger import getlogger

from kafka.errors import KafkaError

producer_logger = getlogger('producer', PRODUCER_INFO_LOG, PRODUCER_ERROR_LOG)


def send_message(message: dict):
    json_message = json.dumps(message)
    bytes_message = json_message.encode()
    producer = KafkaProducerConsumerSingleton._get_producer()
    *_, kafka_topic = KafkaConfigSingleton._get_kafka_config_info()

    try:
        future = producer.send(kafka_topic, bytes_message)
        try:
            record_metadata = future.get(timeout=30)
            producer_logger.info('Topic={}, Partition={}, Offset={}, Message={}'.format(record_metadata.topic, record_metadata.partition, record_metadata.offset, json_message))


        except KafkaError as e:
            producer_logger.error('Send Result Error={}'.format(e))
            raise Exception('Send Message Error: {}'.format(e))

    except Exception as e:
        producer_logger.error('Send Message Error: {}'.format(e))
        raise Exception('Send Message Error: {}'.format(e))