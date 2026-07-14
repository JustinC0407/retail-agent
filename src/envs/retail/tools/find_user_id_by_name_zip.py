

from typing import Any, Dict
from src.envs.tool import Tool


class FindUserIdByNameZip(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], first_name: str, last_name: str, zip: str) -> str:
        """
        Find a user ID by matching first name, last name, and zip code.

        Args:
            data: The shared database dict containing a "users" key.
            first_name: The customer's first name (case-insensitive match).
            last_name: The customer's last name (case-insensitive match).
            zip: The customer's zip code (exact match).

        Returns:
            The user_id string if a matching user is found, otherwise
            "Error: user not found".
        """

        user_id = None
        # Match the first user whose first/last name (case-insensitive) and zip
        # code (exact) equal the arguments.
        for candidate_user_id, user in data["users"].items():
            name = user["name"]
            address = user["address"]
            if (
                name["first_name"].lower() == first_name.lower()
                and name["last_name"].lower() == last_name.lower()
                and address["zip"] == zip
            ):
                user_id = candidate_user_id
                break

        if user_id is None:
            return "Error: user not found"
        return user_id

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "find_user_id_by_name_zip",
                "description": (
                    "Find user id by first name, last name, and zip code. If the user is not found, the function "
                    "will return an error message. By default, find user id by email, and only call this function "
                    "if the user is not found by email or cannot remember email."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "first_name": {
                            "type": "string",
                            "description": "The first name of the customer, such as 'John'.",
                        },
                        "last_name": {
                            "type": "string",
                            "description": "The last name of the customer, such as 'Doe'.",
                        },
                        "zip": {
                            "type": "string",
                            "description": "The zip code of the customer, such as '12345'.",
                        },
                    },
                    "required": ["first_name", "last_name", "zip"],
                },
            },
        }
