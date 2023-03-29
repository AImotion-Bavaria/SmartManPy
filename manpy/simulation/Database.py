from questdb.ingress import Sender
from confluent_kafka.admin import AdminClient, NewTopic
import json
# TODO can we dynamically import packages? it may be annoying to install all dependencies if you only need 1

class ManPyDatabase:

    def establish_connection(self):
        """
        Establishes connection
        :return: None
        """
        raise NotImplementedError("Not implemented!")

    def insert(self, table_name: str, column_value_dict: dict):
        """
        Inserts values into given columns of a table
        :param table_name: Name of the table
        :param column_value_dict: dict containing column-value pairs for the insertion. Example: {"col1": "Test"}
        :return: None
        """
        raise NotImplementedError("Not implemented!")

    def commit(self):
        """
        Commits the changes to the database
        :return: None
        """
        raise NotImplementedError("Not implemented!")

    def close_connection(self):
        """
        Closes the database connection
        :return: None
        """
        raise NotImplementedError("Not implemented!")


class ManPyQuestDBDatabase(ManPyDatabase):

    def __init__(self, host='localhost', port=9009):
        self.sender = None
        self.host = host
        self.port = port

    def establish_connection(self):
        self.sender = Sender(host=self.host, port=self.port)
        self.sender.connect()

    def insert(self, table_name: str, column_value_dict: dict):
        self.sender.row(table_name, columns=column_value_dict)

    def commit(self):
        self.sender.flush()

    def close_connection(self):
        self.sender.close()


class ManPyKafkaConnection(ManPyDatabase):

    def __init__(self, producer, topics, bootstrap_server_address):
        self.producer = producer
        self.__create_topics(topics, bootstrap_server_address)

    def __create_topics(self, names, bootstrap_server_address):
        admin_client = AdminClient({'bootstrap.servers': bootstrap_server_address})
        topics_to_create = [NewTopic(n, 1, 1) for n in names]
        admin_client.create_topics(topics_to_create)

    def establish_connection(self):
        pass

    def insert(self, table_name: str, column_value_dict: dict):
        """
        sends data to kafka
        :param table_name: topic to write to
        :param column_value_dict: dict containing column-value pairs for the insertion. Example: {"col1": "Test"}
        :return: None
        """
        encoded_data = json.JSONEncoder().encode(column_value_dict)
        self.producer.poll(0)
        self.producer.produce(table_name, encoded_data.encode("utf-8"), callback=self.__on_delivery)

    def __on_delivery(self, err, msg):
        if err is not None:
            print(f">>>>> Error while sending data to Kafka!: {err}")

    def commit(self):
        self.producer.flush()

    def close_connection(self):
        pass
