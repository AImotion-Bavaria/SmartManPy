from questdb.ingress import Sender


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
