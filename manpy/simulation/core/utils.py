import sys


# TODO add to docs!

def check_config_dict(config_dict: dict, keys: list, object_name: str):
    """
    Function to check if config dictionaries contain a mistake.
    I.e., it checks if certain keys are contained in the dict and warns the user if some are missing.
    Is used to prevent accidental misconfigurations.

    :param config_dict: The config dict to be checked
    :param keys: A list with the keys in config_dict that should be checked
    :param object_name: The name of the object in which the check is done. Is used for the print statement
    """

    for k in keys:
        if k not in config_dict:
            print(f"ATTENTION: {k} was not found in a config dict for {object_name}.")
            answer = input("Was this intentional? Enter 'Yes' or 'y' to continue.... ")
            if answer == "Yes" or answer == "y" or answer == "Y":
                continue
            else:
                print("Exiting program...")
                sys.exit(1)

    print(f"Checked a config dict of {object_name} for {keys}. No issues were found.")


def info(text):
    """
    Puts "INFO: " in front of a text.

    :param text: The text to which "INFO: " should be added.
    """
    print(f"INFO: {text}")


def define_sequential_routing(sim_object: list):
    pass
