"""SMHI Metobs client."""

import io
import logging
from collections import defaultdict
from typing import Any, Optional, TypeAlias, Union

import pandas as pd
import requests
from requests.structures import CaseInsensitiveDict
from smhi.constants import METOBS_AVAILABLE_PERIODS
from smhi.models.metobs_data import DataModel, Datum, MetobsData
from smhi.models.metobs_parameters import ParameterModel
from smhi.models.metobs_periods import PeriodModel
from smhi.models.metobs_stations import StationModel
from smhi.models.metobs_versions import VersionModel

MetobsModels: TypeAlias = (
    VersionModel | ParameterModel | StationModel | PeriodModel | DataModel
)

logger = logging.getLogger(__name__)


class BaseMetobs:
    """Base Metobs class."""

    def __init__(self) -> None:
        """Initialise base class."""
        self.headers: Optional[CaseInsensitiveDict] = None
        self.key: Optional[str] = None
        self.updated: Optional[int] = None
        self.title: Optional[str] = None
        self.summary: Optional[str] = None
        self.link: Optional[str] = None

    def _get_and_parse_request(self, url: str, model: MetobsModels) -> MetobsModels:
        """Get and parse API request. Only JSON supported.

        Args:
            url: url to get from
            model: pydantic model to populate

        Returns:
            pydantic model

        Raise:
            requests.exceptions.HTTPError
        """
        logger.info(f"Fetching from {url} for model {model}.")

        response = requests.get(url, timeout=200)
        if response.status_code != 200:
            raise requests.exceptions.HTTPError(
                f"Could not find or load from given URL: {url}."
            )

        model = model.model_validate_json(response.content)

        self.headers = response.headers
        self.key = model.key
        self.updated = model.updated
        self.title = model.title
        self.summary = model.summary
        self.link = model.link

        return model

    def _get_url(
        self,
        data: list[Any],
        key: str,
        parameter: Union[str, int],
        data_type: str = "json",
    ) -> tuple[str, str]:
        """Get the url to get data from. Defaults to type json.

        Args:
            data: data list
            key: key to look up
            parameter: parameter to look for
            data_type: data type of requested url

        Returns:
            url
            summary

        Raises:
            IndexError
        """
        self.data_type = defaultdict(
            lambda: "application/json", json="application/json"
        )[data_type]
        try:
            requested_data = [x for x in data if getattr(x, key) == str(parameter)][0]
            url = [x.href for x in requested_data.link if x.type == self.data_type][0]
            summary = requested_data.summary
            return url, summary
        except IndexError:
            raise IndexError("Can't find data for parameters: {p}".format(p=parameter))
        except TypeError:
            raise TypeError("Can't find field: {key}".format(key=key))


class Versions(BaseMetobs):
    """Get available versions of Metobs API."""

    def __init__(
        self,
        data_type: str = "json",
    ) -> None:
        """Get versions.

        For now, only supports `json` and version 1.

        Args:
            data_type: data_type of request

        Raises:
            TypeError: data_type not supported
        """
        super().__init__()

        if data_type != "json":
            raise TypeError("Only json supported.")

        self.base_url = f"https://opendata-download-metobs.smhi.se/api.{data_type}"

        model = self._get_and_parse_request(self.base_url, VersionModel)

        self.data = model.version


class Parameters(BaseMetobs):
    """Get parameters for version 1 of Metobs API."""

    def __init__(
        self,
        versions_object: Optional[Versions] = None,
        version: Union[str, int] = "1.0",
        data_type: str = "json",
    ) -> None:
        """Get parameters from version.

        Args:
            versions_object: versions object
            version: selected version
            data_type: data_type of request

        Raises:
            TypeError: data_type not supported
            NotImplementedError: version not implemented
        """
        super().__init__()

        if data_type != "json":
            raise TypeError("Only json supported.")

        version = "1.0" if version == 1 else version
        if version != "1.0":
            raise NotImplementedError("Only supports version 1.0.")

        if versions_object is None:
            versions_object = Versions()

        url, _ = self._get_url(versions_object.data, "key", version, data_type)
        model = self._get_and_parse_request(url, ParameterModel)

        self.versions_object = versions_object
        self.selected_version = version

        self.resource = model.resource
        self.data = model.data


class Stations(BaseMetobs):
    """Get stations from parameter for version 1 of Metobs API."""

    def __init__(
        self,
        parameters_in_version: Parameters,
        parameter: Optional[int] = None,
        parameter_title: Optional[str] = None,
        data_type: str = "json",
    ) -> None:
        """Get stations from parameters.

        Args:
            parameters_in_version: parameters object
            parameter: integer parameter key to get
            parameter_title: exact parameter title to get
            data_type: data_type of request

        Raises:
            TypeError: data_type not supported
            NotImplementedError: parameter not implemented
        """
        super().__init__()
        self.selected_parameter: Optional[Union[int, str]] = None

        if data_type != "json":
            raise TypeError("Only json supported.")

        if parameter is None and parameter_title is None:
            raise NotImplementedError("No parameter selected.")

        if parameter and parameter_title:
            raise NotImplementedError("Can't decide which input to select.")

        if parameter:
            self.selected_parameter = parameter
            url, _ = self._get_url(
                parameters_in_version.resource, "key", parameter, data_type
            )
        if parameter_title:
            self.selected_parameter = parameter_title
            url, _ = self._get_url(
                parameters_in_version.resource, "title", parameter_title, data_type
            )

        model = self._get_and_parse_request(url, StationModel)

        self.parameters_in_version = parameters_in_version

        self.value_type = model.value_type
        self.station_set = model.station_set
        self.station = model.station
        self.data = model.data


class Periods(BaseMetobs):
    """Get periods from station for version 1 of Metobs API.

    Note that stationset_title is not supported
    """

    def __init__(
        self,
        stations_in_parameter: Stations,
        station: Optional[int] = None,
        station_name: Optional[str] = None,
        station_set: Optional[str] = None,
        data_type: str = "json",
    ) -> None:
        """Get periods from station.

        Args:
            stations_in_parameter: stations object
            station: integer station key to get
            station_name: exact station name to get
            station_set: station set to get
            data_type: data_type of request

        Raises:
            TypeError: data_type not supported
            NotImplementedError: station not implemented
        """
        super().__init__()
        self.selected_station: Optional[Union[int, str]] = None

        if data_type != "json":
            raise TypeError("Only json supported.")

        if [station, station_name, station_set].count(None) == 3:
            raise NotImplementedError("No stations selected.")

        if [bool(x) for x in [station, station_name, station_set]].count(True) > 1:
            raise NotImplementedError("Can't decide which input to select.")

        if station:
            self.selected_station = station
            url, _ = self._get_url(
                stations_in_parameter.station, "key", station, data_type
            )
        if station_name:
            self.selected_station = station_name
            url, _ = self._get_url(
                stations_in_parameter.station, "name", station_name, data_type
            )
        if station_set:
            self.selected_station = station_set
            url, _ = self._get_url(
                stations_in_parameter.station_set, "key", station_set, data_type
            )

        model = self._get_and_parse_request(url, PeriodModel)

        self.stations_in_parameter = stations_in_parameter

        self.owner = model.owner
        self.owner_category = model.owner_category
        self.measuring_stations = model.measuring_stations
        self.active = model.active
        self.from_ = model.from_
        self.to = model.to
        self.position = model.position
        self.period = model.period
        self.data = model.data


class Data(BaseMetobs):
    """Get data from period for version 1 of Metobs API."""

    metobs_available_periods = METOBS_AVAILABLE_PERIODS
    metobs_parameter_tim = ["Datum", "Tid (UTC)"]
    metobs_parameter_dygn = ["Representativt dygn"]
    metobs_parameter_manad = ["Representativ månad"]

    def __init__(
        self,
        periods_in_station: Periods,
        period: str = "corrected-archive",
        data_type: str = "json",
    ) -> None:
        """Get data from period.

        Args:
            periods_in_station: periods object
            period: select period from:
                    latest-hour, latest-day, latest-months or corrected-archive
            data_type: data_type of request

        Raises:
            TypeError: data_type not supported
            NotImplementedError: period not implemented
        """
        super().__init__()

        if data_type != "json":
            raise TypeError("Only json supported.")

        if (
            len(periods_in_station.data) == 1
            and periods_in_station.data[0] != period
            and period in self.metobs_available_periods
        ):
            logger.info(
                "Found only one period to download. "
                + f"Overriding the user selected {period} with the found {periods_in_station.data[0]}."
            )
            period = periods_in_station.data[0]

        if period not in self.metobs_available_periods:
            raise NotImplementedError(
                "Select a supported periods: }"
                + ", ".join([p for p in self.metobs_available_periods])
            )

        self.periods_in_station = periods_in_station
        self.selected_period = period

        url, _ = self._get_url(periods_in_station.period, "key", period, data_type)
        model = self._get_and_parse_request(url, DataModel)

        self.from_ = model.from_
        self.to = model.to

        data_model = self._get_data(model.data)
        stationdata = data_model.stationdata
        stationdata = self._clean_columns(stationdata)
        stationdata = self._drop_nan(stationdata)

        if self._has_datetime_columns(stationdata) is True and not stationdata.empty:
            stationdata = self._set_dataframe_index(stationdata)

        self.station = data_model.station
        self.parameter = data_model.parameter
        self.period = data_model.period
        self.data = stationdata

    def _get_data(self, raw_data: list[Datum], type: str = "text/plain") -> MetobsData:
        """Get the selected data file.

        Args:
            raw_data: raw data
            type: type of request

        Returns:
            data model
        """
        link = [
            link.href for item in raw_data for link in item.link if link.type == type
        ]

        if len(link) == 0:
            raise NotImplementedError("Can't find CSV file to download.")
        if len(link) > 1:
            raise NotImplementedError(
                "Found several CSV files to download, this is currently not supported."
            )

        csv_content = self._request_and_decode(link[0])

        # these are the two cases I've found. Generalise if there are others
        if len(csv_content) == 2:
            data_model = MetobsData(
                parameter=self._parse_csv(csv_content[0]),
                stationdata=self._parse_csv(csv_content[1]),
            )
        else:
            data_model = MetobsData(
                station=self._parse_csv(csv_content[0]),
                parameter=self._parse_csv(csv_content[1]),
                period=self._parse_csv(csv_content[2]),
                stationdata=self._parse_csv(csv_content[3]),
            )

        return data_model

    def _parse_csv(self, csv) -> pd.DataFrame:
        """Parse CSV files with pandas.

        Args:
            csv: csv string

        Returns:
            pandas dataframe
        """
        return pd.read_csv(io.StringIO(csv), sep=";", on_bad_lines="skip")

    def _request_and_decode(self, link: str) -> list[str]:
        """Request CSV and decode it.

        Args:
            link: link to fetch from

        Returns:
            decoded list of csv files
        """
        return requests.get(link).content.decode("utf-8").split("\n\n")

    def _set_dataframe_index(self, stationdata: pd.DataFrame) -> pd.DataFrame:
        """Set dataframe index based on datetime column.

        Args:
            data: station dataframe

        Returns:
            return augmented dataframe

        Raise:
            TypeError
        """
        columns = stationdata.columns
        if any([c for c in self.metobs_parameter_tim if c in columns]):
            datetime_columns = self.metobs_parameter_tim
        elif any([c for c in self.metobs_parameter_dygn if c in columns]):
            datetime_columns = self.metobs_parameter_dygn
        elif any([c for c in self.metobs_parameter_manad if c in columns]):
            datetime_columns = self.metobs_parameter_manad
        else:
            raise TypeError("Can't parse type.")

        stationdata.set_index(
            pd.to_datetime(stationdata[datetime_columns].agg(" ".join, axis=1)),
            inplace=True,
        )
        stationdata.drop(datetime_columns, axis=1, inplace=True)

        return stationdata

    def _drop_nan(self, df: pd.DataFrame, n_cols: int = 2) -> pd.DataFrame:
        """Drop nan from dataframe rows by first first n cols.

        Args:
            df: dataframe

        Returns
            dataframe with dropped nan rows
        """
        df.dropna(axis="index", how="all", subset=df.columns[:n_cols], inplace=True)

        return df

    def _clean_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean dataframe from non-data columns.

        Always drop the last column.

        Args:
            df: dataframe
        """
        df = df.iloc[:, :-1]
        columns = df.columns
        remove_columns = [col for col in columns if "unnamed" in col.lower()]
        df.drop(columns=remove_columns, inplace=True)

        return df

    def _has_datetime_columns(self, df: pd.DataFrame) -> bool:
        """Check if datafram has any datetime column.

        Args:
            df: dataframe
        """
        return any(
            [
                c
                for c in self.metobs_parameter_tim
                + self.metobs_parameter_dygn
                + self.metobs_parameter_manad
                if c in df.columns
            ]
        )
