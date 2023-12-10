import json
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict

import requests

# Setup basic configuration for logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s')


class SoloonColor(Enum):
    """Enum for Soloon colors."""
    BLUE = "blue"
    RED = "red"
    PURPLE = "purple"
    WHITE = "white"


class ComethDirection(Enum):
    """Enum for Cometh directions."""
    UP = "up"
    DOWN = "down"
    RIGHT = "right"
    LEFT = "left"


class MegaverseAPI:
    """Class to interact with the Megaverse API."""

    BASE_URL = "https://challenge.crossmint.io/api"

    def __init__(self, config_path: str) -> None:
        """
        Initialize the API client.

        Args:
            candidate_id (str): Unique identifier for the candidate.
            request_delay (float): Delay between API requests to prevent rate limiting.
        """

        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        self.candidate_id = config['candidate_id']
        self.base_url = config['base_url']
        # Default to 0.6 if not specified
        delay = config.get('request_delay', 0.6)
        self.request_delay = timedelta(seconds=delay)
        self.last_request_time = datetime.now()

    def _rate_time(self) -> None:
        """Ensure that the API is not called more frequently than the rate limit."""
        now = datetime.now()
        if now - self.last_request_time < self.request_delay:
            wait_time = (self.request_delay -
                         (now - self.last_request_time)).total_seconds()
            time.sleep(wait_time)

        self.last_request_time = datetime.now()

    def _handle_requests(self, method: str, endpoint: str,
                         **kwards: Any) -> Dict[str, Any] | None:
        """
        Handle API requests with the specified method, endpoint, and parameters.

        Args:
            method (str): HTTP method to use ('get', 'post', etc.).
            endpoint (str): API endpoint to be called.
            **kwargs: Additional keyword arguments for the request.

        Returns:
            dict | None: JSON response from the API or None if an error occurs.
        """
        self._rate_time()
        url: str = f"{self.base_url}/{endpoint}"
        payload: Dict[str, Any] = {"candidateId": self.candidate_id, **kwards}
        try:
            response = getattr(requests, method)(url, data=payload)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as error:
            logging.error(f"HTTP Error: {error}")
        except requests.exceptions.ConnectionError as error:
            logging.error(f"Error Connecting: {error}")
        except requests.exceptions.Timeout as error:
            logging.error(f"Timeout Error: {error}")
        except requests.exceptions.RequestException as error:
            logging.error(f"Something weird went wrong: {error}")

    def create_object(
            self,
            object_type: str,
            row: int,
            column: int,
            **kwargs: Any) -> None:
        """
        Create an object.

        Args:
            object_type (str): Type of object to create.
            row (int): Row position for the object.
            column (int): Column position for the object.
            **kwargs: Additional keyword arguments for object creation.
        """
        self._handle_requests(
            "post",
            object_type,
            row=row,
            column=column,
            **kwargs)
        logging.info(f"{object_type.capitalize()} successfully created")

    def delete_object(self, object_type: str, row: int, column: int):
        """
        Delete an object.

        Args:
            object_type (str): Type of object to delete.
            row (int): Row position for the object.
            column (int): Column position for the object.
        """
        self._handle_requests("delete", object_type, row=row, column=column)
        logging.info(f"{object_type.capitalize()} successfully deleted")

    def create_soloon(self, row: int, column: int, color: SoloonColor) -> None:
        """
        Create a Soloon.

        Args:
            row (int): Row position for the Soloon.
            column (int): Column position for the Soloon.
            color (SoloonColor): Color of the Soloon.
        """
        self.create_object("soloons", row, column, color=color)

    def delete_soloon(self, row: int, column: int) -> None:
        """
        Delete a Soloon.

        Args:
            row (int): Row position for the Soloon.
            column (int): Column position for the Soloon.
        """
        self.delete_object("soloons", row, column)

    def create_cometh(
            self,
            row: int,
            column: int,
            direction: ComethDirection) -> None:
        """
        Create a Cometh.

        Args:
            row (int): Row position for the Cometh.
            column (int): Column position for the Cometh.
            direction (ComethDirection): Movement direction of the Cometh.
        """
        self.create_object("comeths", row, column, direction=direction)

    def delete_cometh(self, row: int, column: int) -> None:
        """
        Delete a Cometh.

        Args:
            row (int): Row position for the Cometh.
            column (int): Column position for the Cometh.
        """
        self.delete_object("comeths", row, column)

    def create_polyanet(self, row: int, column: int) -> None:
        """
        Create a Polyanet.

        Args:
            row (int): Row position for the Polyanet.
            column (int): Column position for the Polyanet.
        """
        self.create_object("polyanets", row, column)

    def delete_polyanet(self, row: int, column: int) -> None:
        """
        Delete a Polyanet.

        Args:
            row (int): Row position for the Polyanet.
            column (int): Column position for the Polyanet.
        """
        self.delete_object("polyanets", row, column)

    def create_polyanet_cross(self) -> None:
        """Create a cross formation of Polyanets."""
        for i in range(11):
            if i == 5:
                self.create_polyanet(i, i)
            elif i >= 2 and i <= 8:
                self.create_polyanet(i, i)
                self.create_polyanet(i, 10 - i)

    def create_crossmint_logo(self) -> None:
        """
        Create the Crossmint logo on the map based on a predefined goal map.
        """
        response = self.goal_map()
        if isinstance(response, dict):
            for i, row in enumerate(response["goal"]):
                for j, object_name in enumerate(row):
                    if (object_name == "SPACE"):
                        continue
                    elif (object_name == "POLYANET"):
                        self.create_polyanet(i, j)

                    elif (object_name.split("_")[1] == "COMETH"):
                        direction_text: str = object_name.split("_")[0]
                        try:
                            direction_att: ComethDirection = getattr(
                                ComethDirection, direction_text).value
                        except AttributeError:
                            logging.error(
                                f"Invalid Soloon direction: {direction_text}")
                            return
                        self.create_cometh(i, j, direction_att)

                    else:
                        color_text: str = object_name.split("_")[0]
                        try:
                            color_att: SoloonColor = getattr(
                                SoloonColor, color_text).value
                        except AttributeError:
                            logging.error(
                                f"Invalid Soloon direction: {color_text}")
                            return

                        self.create_soloon(i, j, color_att)

    def goal_map(self) -> Dict[str, Any] | None:
        """
        Retrieve the goal map for the Crossmint second challenge.

        Returns:
            dict | None: The goal map as a dictionary or None if an error occurs.
        """
        response = self._handle_requests(
            "get", f"map/{self.candidate_id}/goal")
        return response


if __name__ == "__main__":
    config_path = "./config.json"
    megaverse_api = MegaverseAPI(config_path)

    megaverse_api.create_crossmint_logo()
