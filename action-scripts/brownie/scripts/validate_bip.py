import os
from typing import Tuple

from .script_utils import get_changed_files
from bal_addresses import AddrBook
from prettytable import PrettyTable

ADDRESSES_MAINNET = AddrBook("mainnet").reversebook
ADDRESSES_POLYGON = AddrBook("polygon").reversebook
ADDRESSES_ARBITRUM = AddrBook("arbitrum").reversebook
ADDRESSES_AVALANCHE = AddrBook("avalanche").reversebook
ADDRESSES_OPTIMISM = AddrBook("optimism").reversebook
ADDRESSES_GNOSIS = AddrBook("gnosis").reversebook
ADDRESSES_ZKEVM = AddrBook("zkevm").reversebook
# Merge all addresses into one dictionary
ADDRESSES = {**ADDRESSES_MAINNET, **ADDRESSES_POLYGON, **ADDRESSES_ARBITRUM, **ADDRESSES_AVALANCHE,
             **ADDRESSES_OPTIMISM, **ADDRESSES_GNOSIS, **ADDRESSES_ZKEVM}


def validate_contains_msig(file: dict) -> Tuple[bool, str]:
    """
    Validates that file contains a multisig transaction
    """
    msig = file['meta'].get('createdFromSafeAddress') or file['meta'].get('createFromSafeAddress')
    if not msig or not isinstance(msig, str):
        return False, "No msig address found or it is not a string"
    return True, ""


def validate_msig_in_address_book(file: dict) -> Tuple[bool, str]:
    """
    Validates that multisig address is in address book
    """
    msig = file['meta'].get('createdFromSafeAddress') or file['meta'].get('createFromSafeAddress')
    if msig not in ADDRESSES:
        return False, "Multisig address not found in address book"
    return True, ""


def validate_chain_specified(file: dict) -> Tuple[bool, str]:
    """
    Validates that chain is specified in file
    """
    chain = file.get('chainId')
    if not chain or not isinstance(chain, str):
        return False, "No chain specified or it is not a string"
    return True, ""


# Add more validators here as needed
VALIDATORS = [
    validate_contains_msig,
    validate_msig_in_address_book,
    validate_chain_specified,
]


def main() -> None:
    files = get_changed_files()
    # Filter out merged jsons that are placed under 00batched folder
    files = [file for file in files if "00batched" not in file["file_name"]]
    # Run each file through validators and collect output in form of a dictionary
    results = {}
    for file in files:
        file_path = file["file_name"]
        results[file_path] = {}
        for validator in VALIDATORS:
            is_valid, output_msg = validator(file)
            if not is_valid:
                results[file_path][validator.__name__] = output_msg
            else:
                results[file_path][validator.__name__] = "OK"

    # Generate report for each file and save it in a list
    reports = []
    for file_path, file_results in results.items():
        report = f"BIP validation results for file {file_path}:\n"
        # Commit:
        report += f"Commit: `{os.getenv('COMMIT_SHA')}`\n"
        # Convert output for each file into table format
        table = PrettyTable()
        table.field_names = ["Validator", "Result"]
        for validator_name, result in file_results.items():
            table.add_row([validator_name, result])
        report += f"```\n{table}\n```"
        reports.append(report)

    # Save temporary file with results so that it can be used in github action later
    with open("validate_bip_results.txt", "w") as f:
        f.write("\n\n".join(reports))


if __name__ == "__main__":
    main()