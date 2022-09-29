"""
SMHI STRÅNG client.
"""
import json
import arrow
import requests
from functools import partial
from smhi.constants import (
    STRANG,
    STRANG_POINT_URL,
    STRANG_PARAMETERS,
    STRANG_DATE_INTERVALS,
)


class StrangPoint:
    """
    SMHI STRÅNG Pointclass. Only supports category strang1g and version 1.
    """

    def __init__(self):
        """
        Initialise STRÅNG object.
        """
        self._category = "strang1g"
        self._version = 1

        self.latitude = None
        self.longitude = None
        self.parameter = None
        self.status = None
        self.header = None
        self.data = None
        self.available_parameters = STRANG_PARAMETERS
        self.raw_url = partial(
            STRANG_POINT_URL.format, category=self._category, version=self._version
        )
        self.url = None

    @property
    def parameters(self):
        return self.available_parameters

    def fetch_data(
        self,
        longitude: float,
        latitude: float,
        parameter: STRANG,
        date_from: str = None,
        date_to: str = None,
        date_interval: str = None,
    ):
        """
        Get data for given lon, lat and parameter.

        Args:
            longitude: longitude
            latitude: latitude
            parameter: parameter
            date_from: get data from (optional),
            date_to: get data to (optional),
            date_interval: interval of data [valid values: hourly, daily, monthly] (optional)
        """
        self.longitude = longitude
        self.latitude = latitude
        self.parameter = self.available_parameters[parameter]
        self.date_from = date_from
        self.date_to = date_to
        self.date_interval = date_interval

        if self.parameter.parameter is None:
            raise NotImplementedError(
                "Parameter not implemented. Try client.parameters to list available parameters."
            )

        self.url = self.raw_url(
            lon=self.longitude,
            lat=self.latitude,
            parameter=self.parameter.parameter,
        )

        self.url = self._build_date_url()
        self.status, self.headers, self.data = self._fetch_and_load_strang_data()

    def _build_date_url(self):
        """
        Build date part of the API url.
        """
        date_from = self._parse_date(self.date_from)
        date_to = self._parse_date(self.date_to)
        date_interval = self.date_interval
        url = self.url + "?"

        if date_from is not None:
            url = url + "from={date_from}".format(date_from=date_from)

        if date_to is not None:
            if date_from is not None:
                url = url + "&"
            url = url + "to={date_to}".format(date_to=date_to)

        if date_interval is not None and (date_from is not None or date_to is not None):
            if date_interval not in STRANG_DATE_INTERVALS:
                raise ValueError("Time interval must be hourly, daily or monthly.")
            url = url + "&interval={date_interval}".format(date_interval=date_interval)
        # else:
        #    raise NotImplementedError(
        #        "Date from and to not specified but interval is. Be more explicit."
        #    )

        return url

    def _fetch_and_load_strang_data(self):
        """
        Fetch requested data and parse it with datetime.
        """
        response = requests.get(self.url)
        status = response.ok
        headers = response.headers
        data = None

        if status is True:
            data = json.loads(response.content)

            for entry in data:
                entry["date_time"] = arrow.get(entry["date_time"]).datetime

        return status, headers, data

    def _parse_date(self, date):
        """
        Parse date into a datetime format given as string and check bounds.

        Args:
            date: date as string

        Returns:
            parsed date
        """
        if date is None:
            return date

        try:
            date = arrow.get(date)
        except ValueError:
            raise ValueError("Wrong format of from date.")

        if self.parameter.date_from < date < self.parameter.date_to():
            return date
        else:
            raise ValueError(
                "Date not in allowed interval: {date_from} to {date_to}.".format(
                    date_from=self.parameter.date_from, date_to=self.parameter.date_to()
                )
            )
