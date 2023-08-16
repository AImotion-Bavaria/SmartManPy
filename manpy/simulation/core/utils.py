import sys


def check_config_dict(config_dict: dict, keys: list, object_name: str):

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
    print(f"INFO: {text}")
